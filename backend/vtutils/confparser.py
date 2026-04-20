import base64
import json
import os
import sys
from os.path import expanduser, isfile
from configparser import ConfigParser
from dotenv import dotenv_values
from vtutils.vtlogger import getLog
from vtutils.misc import get_project_root, decode_bytes_value

ROOT_DIR = get_project_root()
sys.path.append(ROOT_DIR)

mylog = getLog('confparser')


def parse_config(filename, config=None):
    if not isfile(expanduser(filename)):
        filename = expanduser("{0}/vtconf.d/{1}".format(ROOT_DIR, filename))

    if not isfile(filename):
        raise Exception("No such file: {0}".format(filename))

    special_config = ["mongo", "redis", "postgresql"]

    parser = ConfigParser()
    parser.read(expanduser(filename))
    conn_object = {}

    for section_name in parser.sections():
        section_type = parser.get(section_name, 'type')
        env_config_key = ""

        if section_type in special_config:
            section_connection = parser.get(section_name, 'connection') \
                if parser.has_option(section_name, 'connection') else "conn1"
            if section_connection in conn_object and conn_object[section_connection]:
                conn_object[section_name] = conn_object[section_connection]
                continue
            env_config_key = "{0}_{1}".format(section_type, section_connection).upper()

        elif section_type == 'env_config':
            # special section that just returns the config dict
            conn_object[section_name] = config if config else {}
            continue

        if not config or (env_config_key and env_config_key not in config):
            conn_object[section_name] = dict(parser.items(section_name))
            continue

        config_credentials = config.get(env_config_key)

        if section_type in special_config and isinstance(config_credentials, str):
            env_config_key = "{0}_{1}".format(section_type, config_credentials).upper()
            config_credentials = config.get(env_config_key)

        if section_type == 'mongo':
            import pymongo
            if config_credentials and config_credentials.get("user") and config_credentials.get("password"):
                conn_object[section_name] = pymongo.MongoClient(
                    config_credentials["string"],
                    username=config_credentials["user"],
                    password=config_credentials["password"],
                    tz_aware=True,
                    socketTimeoutMS=10000,
                    serverSelectionTimeoutMS=5000
                )
            elif config_credentials:
                conn_object[section_name] = pymongo.MongoClient(
                    config_credentials["string"],
                    tz_aware=True,
                    socketTimeoutMS=10000,
                    serverSelectionTimeoutMS=5000
                )
            else:
                conn_object[section_name] = dict(parser.items(section_name))

        elif section_type == 'redis':
            import redis
            if config_credentials:
                conn_object[section_name] = redis.Redis(
                    host=config_credentials["hostname"],
                    password=config_credentials["password"],
                    port=config_credentials["port"],
                    decode_responses=True,
                    socket_connect_timeout=5
                )
            else:
                conn_object[section_name] = dict(parser.items(section_name))

        else:
            conn_object[section_name] = dict(parser.items(section_name))

    return conn_object


def env_config(filename):
    config = dotenv_values(filename)
    new_config = {}
    for item in config:
        if item.startswith("b64_json_") and config[item]:
            new_config[item.replace("b64_json_", "")] = json.loads(
                decode_bytes_value(base64.b64decode(decode_bytes_value(config[item]))))
        elif item.startswith("b64_") and config[item]:
            new_config[item.replace("b64_", "")] = base64.b64decode(decode_bytes_value(config[item]))
        elif item.startswith("json_") and config[item]:
            new_config[item.replace("json_", "")] = json.loads(decode_bytes_value(config[item]))
        else:
            new_config[item] = config[item]
    return new_config
