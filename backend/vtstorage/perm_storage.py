from vtstorage.mongo_command import MongoCommand
from pymongo import InsertOne, ReplaceOne, UpdateOne
from vtutils.misc import convert_mongo_result_to_dict
import os


class VTPermStorage():

    def __init__(self, type, connection, params=None):
        self._type = type
        self._connection = connection
        self._params = params
        if self._type == "mongo":
            self.mongo_command = MongoCommand(self._connection)
        self._bulk_actions = {}
        self.vt_env = os.getenv("VT_ENV", "development")

    def get_one(self, database=None, collection=None, query=None, projection=None):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.get_one(database=database, collection=collection, query=query, projection=projection)

    def get_many(self, database=None, collection=None, query=None, limit=20, projection=None, start=0, sort=None, make_list=True):
        if self._type == "mongo":
            database = self.return_db(database)
            result_query = self.mongo_command.get_many(database=database, collection=collection, query=query,
                                              projection=projection, limit=limit, start=start, sort=sort)
            if make_list:
                return list(result_query)
            return result_query

    def get_all(self, database=None, collection=None, query=None, projection=None, sort=None):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.get_all(database=database, collection=collection, query=query,
                                              projection=projection, sort=sort)

    def count(self, database=None, collection=None, query=None):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.count(database=database, collection=collection, query=query)

    def update_one(self, database=None, collection=None, query=None, set_object=None, options=None):
        if self._type == "mongo":
            database = self.return_db(database)
            set_object = self.clean_update_object(set_object)
            result_db = self.mongo_command.update_one(database=database, collection=collection, query=query,
                                                 set_object=set_object, options=options)
            return convert_mongo_result_to_dict(result_db)

    def find_one_and_update(self, database=None, collection=None, query=None, set_object=None, options=None):
        if self._type == "mongo":
            database = self.return_db(database)
            set_object = self.clean_update_object(set_object)
            return self.mongo_command.find_one_and_update(database=database, collection=collection, query=query,
                                                 set_object=set_object, options=options)

    def update_many(self, database=None, collection=None, query=None, set_object=None):
        if self._type == "mongo":
            database = self.return_db(database)
            set_object = self.clean_update_object(set_object)
            return self.mongo_command.update_many(database=database, collection=collection, query=query,
                                                 set_object=set_object)

    def insert_one(self, database=None, collection=None, set_object=None):
        if self._type == "mongo":
            database = self.return_db(database)
            db_result = self.mongo_command.insert(database=database, collection=collection, set_object=set_object)
            return convert_mongo_result_to_dict(db_result)

    def insert_many(self, database=None, collection=None, items=None):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.insert_many(database=database, collection=collection, items=items)

    def replace_one(self, database=None, collection=None, query=None, set_object=None, upsert=False):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.replace_one(database=database, collection=collection, query=query,
                                                  set_object=set_object, upsert=upsert)

    def delete_one(self, database=None, collection=None, query=None):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.delete_one(database=database, collection=collection, query=query)

    def delete_many(self, database=None, collection=None, query=None):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.delete_many(database=database, collection=collection, query=query)

    def return_db(self, database):
        if database:
            return database
        else:
            return self._params["database"]

    def bulk_write(self, database=None, collection=None, action=None):
        name = "{0}_{1}".format(database, collection)
        if not name in self._bulk_actions:
            self._bulk_actions[name] = []
        if action and self._type == "mongo":
            action_mongo = None
            if action["type"] == "replace_one":
                action_mongo = ReplaceOne(**action["pymongo"])
            if action["type"] == "insert_one":
                action_mongo = InsertOne(**action["pymongo"])
            if action["type"] == "update_one":
                action_mongo = UpdateOne(**action["pymongo"])
            if action_mongo:
                self._bulk_actions[name].append(action_mongo)

    def bulk_write_execute(self, database=None, collection=None, options=None):
        name = "{0}_{1}".format(database, collection)
        actions = self._bulk_actions[name] if name in self._bulk_actions else []
        if self._type == "mongo" and actions:
            database = self.return_db(database)
            result = self.mongo_command.bulk_write(database=database, collection=collection, actions=actions, options=options)
            self._bulk_actions[name] = []
            return result

    def bulk_write_count(self, database=None, collection=None):
        name = "{0}_{1}".format(database, collection)
        return len(self._bulk_actions[name]) if name in self._bulk_actions else 0

    def clean_update_object(self, set_object):
        if set_object and "$set" in set_object and "_id" in set_object["$set"]:
            del set_object["$set"]["_id"]
        return set_object

    def ensure_index(self, database=None, collection=None, index_options=None):
        # this creates an index
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.ensure_index(database=database, collection=collection, index_options=index_options)

    def aggregate(self, database=None, collection=None, pipeline=None):
        if self._type == "mongo":
            database = self.return_db(database)
            return self.mongo_command.aggregate(database=database, collection=collection, pipeline=pipeline)
