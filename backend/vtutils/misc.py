from pathlib import Path
import json
import base64
import hashlib
import datetime
from typing import Optional


def get_project_root():
    return str(Path(__file__).parent.parent)


def resolve_project_file_path(file_path: Optional[str], project_root: Optional[str] = None) -> Optional[str]:
    """
    Resolves a file path against the project root for relative paths.

    Resolution order:
    1. absolute path as-is
    2. project root + relative path
    3. current working directory + relative path

    If the file does not exist in any of those places, returns the project-root candidate.
    """
    if not file_path:
        return None

    path_obj = Path(file_path).expanduser()
    if path_obj.is_absolute():
        return str(path_obj)

    root_candidate = Path(project_root or get_project_root()) / path_obj
    if root_candidate.is_file():
        return str(root_candidate)

    cwd_candidate = Path.cwd() / path_obj
    if cwd_candidate.is_file():
        return str(cwd_candidate)

    return str(root_candidate)


def str2bool(element):
    if type(element) is bool:
        return element
    if isinstance(element, str) and element.lower() in ["true", "1", "yes", "on"]:
        return True
    if isinstance(element, str) and element.lower() in ["false", "0", "no", "off"]:
        return False
    if type(element) in [int, float, list, dict]:
        return bool(element)
    return False


def decode_bytes_value(value):
    if isinstance(value, dict):
        value = {decode_bytes_value(k): decode_bytes_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        value = [decode_bytes_value(k) for k in value]
    else:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
    return value


def make_dict_json_serializable(input_dict):
    def handle_non_serializable(item):
        if isinstance(item, (int, float, str, bool, type(None))):
            return item
        elif isinstance(item, (list, tuple)):
            return [handle_non_serializable(x) for x in item]
        elif isinstance(item, dict):
            return make_dict_json_serializable(item)
        elif isinstance(item, set):
            return list(item)
        elif isinstance(item, bytes):
            return item.decode('utf-8', 'ignore')
        else:
            try:
                return str(item)
            except Exception as e:
                return str(e)
    if isinstance(input_dict, dict):
        return {key: handle_non_serializable(value) for key, value in input_dict.items()}
    elif isinstance(input_dict, list):
        return [make_dict_json_serializable(item) for item in input_dict]
    else:
        return handle_non_serializable(input_dict)


def convert_mongo_result_to_dict(mongo_result):
    result = {}
    if not mongo_result:
        return result
    if isinstance(mongo_result, dict):
        return mongo_result
    for attr in ["upserted_id", "matched_count", "modified_count", "deleted_count", "inserted_ids", "inserted_id"]:
        try:
            result[attr] = getattr(mongo_result, attr)
        except AttributeError:
            pass
    if result.get("inserted_id") or result.get("upserted_id"):
        result["document_id"] = result.get("inserted_id") or result.get("upserted_id")
    return result


def toMiliseconds():
    return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)


def md5(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.md5(value).hexdigest()
