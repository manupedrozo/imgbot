import logging
import os
import json
from datetime import datetime

logging.getLogger().setLevel(level=logging.INFO)

DEBUG_INFO = True
DEBUG_DATA = True
DEBUG_HTTP = True


def debug_log_response(response, successful=True):
    if DEBUG_HTTP:
        if successful:
            logging.info(f"Status: {response.status_code}, Json: {response.json()}")
        else:
            logging.warning(f"Status: {response.status_code}, Json: {response.json()}")


def debug_log_data(*args):
    if DEBUG_DATA:
        logging.info(*args)


def debug_log_info(*args):
    if DEBUG_INFO:
        logging.info(*args)


def date_to_string(date: datetime):
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def date_from_string(date_str: str, millis=False):
    if millis:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def json_save(obj, file_path: str, indent=2):
    with open(file_path, 'w') as f:
        json.dump(obj, f, indent=indent)


def json_load(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise Exception(f"[JSON] No file at {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)
