"""
Used to access the data files.
"""
import os
import sys

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')
import pkg_resources

import libraries.emojipasta.data

DATA_DIRECTORY_NAME = libraries.emojipasta.data.__name__
PATH_TO_MAPPINGS_FILE = pkg_resources.resource_filename(DATA_DIRECTORY_NAME, "emoji-mappings.json")
