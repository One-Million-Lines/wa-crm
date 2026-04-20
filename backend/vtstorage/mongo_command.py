import time

import pymongo.errors

from vtutils.misc import convert_mongo_result_to_dict
from vtutils.vtlogger import getLog


class MongoCommand(object):

    def __init__(self, mongo, db=None, col=None):
        super(MongoCommand, self).__init__()
        self._mongo = mongo
        self._database = db
        self._collection = col
        self.mylog = getLog("mongocommand")

    def get_many(self, database, collection, query, projection=None, limit=100, start=0, sort=None):
        try:
            return self._mongo[database][collection].find(query, projection=projection, limit=limit,
                                                          skip=start, sort=sort)
        except Exception as exc:
            self.mylog.error("get", err=str(exc), collection=collection, database=database)
            return None

    def get_all(self, database, collection, query, projection=None, sort=None):
        try:
            return self._mongo[database][collection].find(query, projection=projection, sort=sort)
        except Exception as exc:
            self.mylog.error("get_all", err=str(exc), collection=collection, database=database)
            return None

    def get_one(self, database, collection, query, projection=None):
        try:
            return self._mongo[database][collection].find_one(query, projection=projection)
        except Exception as exc:
            self.mylog.error("get_one", err=str(exc), collection=collection, database=database)
            return None

    def update_one(self, database, collection, query, set_object=None, options=None):
        if not set_object or not query:
            return None
        if not options:
            options = {}
        try:
            return self._mongo[database][collection].update_one(query, set_object, **options)
        except Exception as exc:
            self.mylog.error("update_one", query=query, collection=collection, database=database, set_object=set_object, err=str(exc), exc=exc)
            return None

    def replace_one(self, database, collection, query, set_object=None, upsert=False):
        if not set_object or not query:
            return None
        for attempt in range(1, 3):
            try:
                return self._mongo[database][collection].replace_one(query, set_object, upsert=upsert)
            except pymongo.errors.PyMongoError as exc:
                self.mylog.debug("replace_one_retry", err=str(exc), collection=collection, database=database)
                if attempt == 3:
                    raise
                time.sleep(1 * (2 ** attempt))
            except Exception as exc:
                self.mylog.error("replace_one_exc", err=str(exc), collection=collection, database=database)
                raise exc

    def update_many(self, database, collection, query, set_object=None):
        if not set_object or not query:
            return None
        try:
            return self._mongo[database][collection].update_many(query, set_object)
        except Exception as exc:
            self.mylog.error("update_many", err=str(exc), collection=collection, database=database)
            return None

    def delete_one(self, database, collection, query):
        if not query:
            return None
        try:
            return self._mongo[database][collection].delete_one(query)
        except Exception as exc:
            self.mylog.error("delete_one", err=str(exc), collection=collection, database=database)
            return None

    def delete_many(self, database, collection, query):
        if not query:
            return None
        try:
            return self._mongo[database][collection].delete_many(query)
        except Exception as exc:
            self.mylog.error("delete_many", err=str(exc), collection=collection, database=database)
            return None

    def count(self, database, collection, query):
        try:
            if not query:
                query = {}
            return self._mongo[database][collection].count_documents(query)
        except Exception as exc:
            self.mylog.error("count", err=str(exc), collection=collection, database=database)
            return None

    def insert(self, database, collection, set_object):
        try:
            return self._mongo[database][collection].insert_one(set_object)
        except Exception as exc:
            self.mylog.debug("insert", err=str(exc), item=set_object, collection=collection, database=database)
            return None

    def insert_many(self, database, collection, items):
        try:
            return self._mongo[database][collection].insert_many(items)
        except Exception as exc:
            self.mylog.error("insert_many", err=str(exc), collection=collection, database=database)
            return None

    def find_one_and_update(self, database, collection, query, set_object=None, options=None):
        if not set_object or not query:
            return None
        if not options:
            options = {}
        try:
            return self._mongo[database][collection].find_one_and_update(query, set_object, **options)
        except Exception as exc:
            self.mylog.error("find_one_and_update", err=str(exc), collection=collection, database=database)
            return None

    def bulk_write(self, database, collection, actions=None, options=None):
        if not options:
            options = {}
        if not actions:
            return None
        try:
            return self._mongo[database][collection].bulk_write(actions, **options)
        except Exception as exc:
            self.mylog.error("bulk_operations", err=str(exc), collection=collection, database=database)
            return None

    def ensure_index(self, database, collection, index_options=None):
        if not index_options or not index_options.get("fields", None):
            return None
        index_fields = index_options.pop("fields")
        try:
            return self._mongo[database][collection].create_index(index_fields, **index_options)
        except Exception as exc:
            self.mylog.error("index_errors", err=str(exc))
            return None

    def aggregate(self, database, collection, pipeline):
        try:
            return self._mongo[database][collection].aggregate(pipeline)
        except Exception as exc:
            self.mylog.error("pipeline_error", err=str(exc))
            return None
