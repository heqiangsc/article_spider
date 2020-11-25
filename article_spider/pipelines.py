# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
import logging
import os
import re
import sys
from datetime import time

import gridfs
from scrapy.exceptions import NotConfigured
from scrapy.pipelines.files import FilesPipeline
from twisted.enterprise import adbapi
import MySQLdb
import MySQLdb.cursors
import pymongo

from scrapy.pipelines.images import ImagesPipeline
from twisted.internet import threads


class ArticleSpiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    #自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item
    def spider_closed(self, spider):
        self.file.close()


class MysqlPipeline(object):
    #采用同步的机制写入mysql
    def __init__(self):
        self.conn = MySQLdb.connect('192.168.0.106', 'root', 'root', 'article_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(title, url, create_date, fav_nums)
            VALUES (%s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (item["title"], item["url"], item["create_date"], item["fav_nums"]))
        self.conn.commit()


class MongoPipeline(object):

    collection_name = 'scrapy_items'
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        # 生成更新请求，需要按照code和date创建索引
        return item

class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) #处理异常
        return item

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print (failure)

    def do_insert(self, cursor, item):
        #执行具体的插入
        #根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        print (insert_sql, params)
        cursor.execute(insert_sql, params)

class ImageMysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) #处理异常
        return item

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print (failure)

    def do_insert(self, cursor, item):
        #执行具体的插入
        #根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_image_insert_sql()
        print (insert_sql, params)
        if len(params) > 0:
            cursor.executemany(insert_sql, params)

class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "content_image_url" in item:
            image_file_path = []
            for ok, value in results:
                image_file_path.append(value["path"])
            item["content_image_path"] = image_file_path
        return item


class ArticleContentReplacePipeline(object):
    def process_item(self, item, spider):
        content = item["content"] if "content" in item else None
        content_image_urls = item["content_image_url"] if "content_image_url" in item else None
        content_image_paths = item["content_image_path"] if "content_image_path" in item else None
        if content is None:
            return item
        if content_image_urls is None \
                or content_image_paths is None\
                or len(content_image_paths) == 0 \
                or len(content_image_urls) != len(content_image_paths):
            return item
        cnt = 0
        for url in content_image_urls :
            content = content.replace(url, content_image_paths[cnt])
            cnt += 1
        item["content"] = content
        item["content_replace_flag"] = 1
        return item


import datetime
import hashlib
import time

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from scrapy.http import Request
from scrapy.pipelines.files import FilesPipeline, logger, FileException
from scrapy.utils.log import failure_to_exc_info
from scrapy.utils.misc import md5sum
from scrapy.utils.python import to_bytes
from scrapy.utils.request import referer_str
from twisted.internet import defer

import gridfs
import pymongo


class GridFSFilesStorage(object):
    """MongoDB GridFS storage.
    Store files in GridFS and returns their ObjectId.
    Check if file exists based on file guid generated by pipeline"""

    def __init__(self, uri):
        client = pymongo.MongoClient(uri)
        self.db = client.get_database()
        self.fs = gridfs.GridFS(self.db)

    def persist_file(self, buf, info, file_data={}, meta=None, headers=None):
        """Save the file to GridFS and return it's ObjectId"""

        grid_id = self.fs.put(buf, **file_data)
        return grid_id

    def stat_file(self, file_guid, info):
        """Check if file exists based on file guid generated by the scrapy pipeline"""

        buf = self.fs.find_one({'scrapy_guid': file_guid})
        epoch = datetime.datetime.utcfromtimestamp(0)
        last_modified = (buf.upload_date - epoch).total_seconds()
        checksum = md5sum(buf)
        return {'last_modified': last_modified, 'checksum': checksum, 'mongo_objectid': buf._id}


class GridFSFilesPipeline(FilesPipeline):
    """
    An extension of FilesPipeline that store files in MongoDB GridFS.
    Is using a guid to check if the file exists in GridFS and MongoDB ObjectId to reference the file with item.
    FilesPipeline was using a single variable 'path' for reference and identification.
    guid is used in MongoGridFSFilesPipeline because the pipeline needs a unique identifier generated based on file URL.
    MongoGridFSFilesPipeline is using ObjectId to reference the file because it's the primary key.
    """

    @classmethod
    def from_settings(cls, settings):
        """Override to use store_uri = MONGO_URI"""

        store_uri = settings['MONGO_URI']
        return cls(store_uri, settings=settings)

    def _get_store(self, uri):
        """Override to use MongoGridFSFilesStorage as singele storage option"""
        store_cls = GridFSFilesStorage
        return store_cls(uri)

    def media_to_download(self, request, info):
        """Override to include in the returned result mongo object id and file_guid instead of file_path and filename"""

        def _onsuccess(result):
            if not result:
                return  # returning None force download

            last_modified = result.get('last_modified', None)
            if not last_modified:
                return  # returning None force download

            age_seconds = time.time() - last_modified
            age_days = age_seconds / 60 / 60 / 24
            if age_days > self.expires:
                return  # returning None force download

            referer = referer_str(request)
            logger.debug(
                'File (uptodate): Downloaded %(medianame)s from %(request)s '
                'referred in <%(referer)s>',
                {'medianame': self.MEDIA_NAME, 'request': request,
                 'referer': referer},
                extra={'spider': info.spider}
            )
            self.inc_stats(info.spider, 'uptodate')

            checksum = result.get('checksum', None)
            mongo_objectid = result.get('mongo_objectid', None)
            filename = self.filename(request)
            return {'url': request.url, 'file_guid': file_guid, 'checksum': checksum,
                    'mongo_objectid': mongo_objectid, 'filename': filename}

        file_guid = self.file_guid(request, info=info)
        dfd = defer.maybeDeferred(self.store.stat_file, file_guid, info)
        dfd.addCallbacks(_onsuccess, lambda _: None)
        dfd.addErrback(
            lambda f:
            logger.error(self.__class__.__name__ + '.store.stat_file',
                         exc_info=failure_to_exc_info(f),
                         extra={'spider': info.spider})
        )
        return dfd

    def media_downloaded(self, response, request, info):
        """Override to include in the returned result mongo object id and file_guid instead of file_path and filename"""

        referer = referer_str(request)

        if response.status != 200:
            logger.warning(
                'File (code: %(status)s): Error downloading file from '
                '%(request)s referred in <%(referer)s>',
                {'status': response.status,
                 'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('download-error')

        if not response.body:
            logger.warning(
                'File (empty-content): Empty file from %(request)s referred '
                'in <%(referer)s>: no-content',
                {'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('empty-content')

        status = 'cached' if 'cached' in response.flags else 'downloaded'
        logger.debug(
            'File (%(status)s): Downloaded file from %(request)s referred in '
            '<%(referer)s>',
            {'status': status, 'request': request, 'referer': referer},
            extra={'spider': info.spider}
        )
        self.inc_stats(info.spider, status)

        try:
            file_guid = self.file_guid(request, response=response, info=info)
            checksum, mongo_objectid = self.file_downloaded(response, request, info)
        except FileException as exc:
            logger.warning(
                'File (error): Error processing file from %(request)s '
                'referred in <%(referer)s>: %(errormsg)s',
                {'request': request, 'referer': referer, 'errormsg': str(exc)},
                extra={'spider': info.spider}, exc_info=True
            )
            raise
        except Exception as exc:
            logger.error(
                'File (unknown-error): Error processing file from %(request)s '
                'referred in <%(referer)s>',
                {'request': request, 'referer': referer},
                exc_info=True, extra={'spider': info.spider}
            )
            raise FileException(str(exc))

        filename = self.filename(request)
        return {'url': request.url, 'file_guid': file_guid, 'checksum': checksum, 'mongo_objectid': mongo_objectid,
                "filename": filename}

    def file_downloaded(self, response, request, info):
        """Override to return also the mongo object id along with checksum"""

        filename = self.filename(request)
        guid = self.file_guid(request, response=response, info=info)
        file_data = {'filename': filename, 'scrapy_guid': guid}
        buf = BytesIO(response.body)
        checksum = md5sum(buf)
        buf.seek(0)
        mongo_objectid = self.store.persist_file(buf, info, file_data=file_data)
        return checksum, mongo_objectid

    def file_guid(self, request, response=None, info=None):
        """Renamed and modify file_path to file_guid. In mongo DB the path to file is mongo id. In FilesPipeline path
        was used as identifier and localization"""

        ## start of deprecation warning block (can be removed in the future)

        # check if called from file_key with url as first argument
        url = self._url(request)
        # detect if file_key() method has been overridden
        if not hasattr(self.file_key, '_base'):
            self._warn()
            return self.file_key(url)
        ## end of deprecation warning block

        media_guid = hashlib.sha1(to_bytes(url)).hexdigest()  # change to request.url after deprecation
        return media_guid

    def filename(self, request):
        """Return the original filename"""

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            self._warn()
            url = request
        else:
            url = request.url
        filename = url.split('/')[-1]
        return filename

    ## start of deprecation warning block (can be removed in the future)
    def _url(self, request):
        if not isinstance(request, Request):
            self._warn()
            url = request
        else:
            url = request.url
        return url

    def _warn(self):
        from scrapy.exceptions import ScrapyDeprecationWarning
        import warnings
        warnings.warn('GridFSFilesPipeline.file_key(url) method is deprecated, please use '
                      'file_guid(request, response=None, info=None) instead',
                      category=ScrapyDeprecationWarning, stacklevel=1)
    ## end of deprecation warning block

    # deprecated
    def file_key(self, url):
        """Override to use file_guid instead of file_path"""
        return self.file_guid(url)
    file_key._base = True


import six

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from PIL import Image

from scrapy.pipelines.images import ImagesPipeline, ImageException
from scrapy.utils.misc import md5sum



class GridFSImagesPipeline(ImagesPipeline, GridFSFilesPipeline):
    """
    An extension of ImagesPipeline that store files in MongoDB GridFS.
    Is using a guid to check if the file exists in GridFS and MongoDB ObjectId to reference the file with item.
    ImagesPipeline was using a single variable 'path' for reference and identification.
    guid is used in MongoGridFSFilesPipeline because the pipeline needs a unique identifier generated based on file URL.
    MongoGridFSFilesPipeline is using ObjectId to reference the file because it's the primary key.
    """

    @classmethod
    def from_settings(cls, settings):
        store_uri = settings['MONGO_URI']
        return cls(store_uri, settings=settings)

    def image_downloaded(self, response, request, info):
        """Override to return image_ids along with checksum"""

        # First image is the original image
        image_iter = self.get_images(response, request, info)
        image_guid, image, buf = next(image_iter)
        filename = self.filename(request)
        file_data = {'scrapy_guid': image_guid, "filename": filename}
        buf.seek(0)
        checksum = md5sum(buf)
        buf.seek(0)

        mongo_object_id = self.store.persist_file(buf, info, file_data=file_data,
                        meta={'width': image.size[0], 'height': image.size[1]}, headers={'Content-Type': 'image/jpeg'})

        # Next images are thumbs
        thumbs = {}
        thumbs_id_iter = six.iteritems(self.thumbs)
        for thumb_guid, thumb, thumb_buf in image_iter:
            width, height = thumb.size
            thumb_buf.seek(0)
            filename = self.filename(request)
            name, ext = filename.split('.')
            thumb_id, size = next(thumbs_id_iter)
            filename = name + '_thumb_' + thumb_id + '.' + ext
            file_data = {'scrapy_guid': thumb_guid, "filename": filename}
            thumb_mongo_object_id = self.store.persist_file(thumb_buf, info, file_data=file_data,
                        meta={'width': width, 'height': height}, headers={'Content-Type': 'image/jpeg'})
            thumbs[thumb_id] = thumb_mongo_object_id
        if thumbs:
            images_mongoobjectids = {"image": mongo_object_id}
            images_mongoobjectids.update(thumbs)
            return checksum, images_mongoobjectids
        else:
            return checksum, mongo_object_id

    def get_images(self, response, request, info):
        """Override to return thumb_guid instead of thumb_path"""

        image_guid = self.file_guid(request, response=response, info=info)
        orig_image = Image.open(BytesIO(response.body))

        width, height = orig_image.size
        if width < self.min_width or height < self.min_height:
            raise ImageException("Image too small (%dx%d < %dx%d)" %
                                 (width, height, self.min_width, self.min_height))

        image, buf = self.convert_image(orig_image)
        yield image_guid, image, buf

        for thumb_id, size in six.iteritems(self.thumbs):
            thumb_guid = self.file_guid(request, response=response, info=info)
            thumb_image, thumb_buf = self.convert_image(image, size)
            yield thumb_guid, thumb_image, thumb_buf