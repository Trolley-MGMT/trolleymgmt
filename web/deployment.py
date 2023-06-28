import json
import logging
import os
import sys

from dotenv import load_dotenv

from web.mongo_handler.mongo_utils import insert_dict, insert_file, get_files, delete_file, \
    update_user_profile_image_id, retrieve_user, delete_user, user_exists, team_exists, delete_team
from web.mongo_handler.variables import TEAM_NAME
from web.variables.variables import USER_EMAIL, USER_NAME

DOCKER_ENV = os.getenv('DOCKER_ENV', False)

log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'{os.getcwd()}/web/{log_file_name}'
else:
    log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(filename=log_file_path)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))

TROLLEY_URL = os.getenv('TROLLEY_URL', "https://trolley.com")


def mongo_dump(collection_name: str):
    collection_json_name = f'mongo_boot_dump/trolley_{collection_name}.json'
    with open(collection_json_name) as file:
        file_data = json.load(file)[0]
        if collection_name == 'users':
            if user_exists(file_data[USER_EMAIL]):
                delete_user(user_name=file_data[USER_NAME.lower()], delete_completely=True)
        elif collection_name == 'teams':
            if team_exists(file_data[TEAM_NAME]):
                delete_team(team_name=file_data[TEAM_NAME], delete_completely=True)
        del file_data['_id']
        insert_dict(collection_name=collection_name, collection_dict=file_data)


def js_builder():
    with open('web/static/pre_script.js', 'r') as f:
        lines = f.readlines()
    with open('web/static/script.js', 'w') as f:
        logger.info('successfully opened the static.js file')
        for line in lines:
            if "trolley_url = " in line:
                line = f"    let trolley_url = '{TROLLEY_URL}';\n"
            try:
                f.write(line)
            except Exception as e:
                logger.error(f'Writing of the file failed because: {e}')


def main():
    collections_names = ['users', 'teams']
    for collection in collections_names:
        mongo_dump(collection)
    files = get_files()
    for file in files:
        delete_file(file._id)
    grid_file_id = insert_file(profile_image_filename='mongo_boot_dump/thumbnail_admin_adminovitch.jpg')
    update_user_profile_image_id(user_email='admin@trolley.org', grid_file_id=grid_file_id)
    js_builder()


if __name__ == "__main__":
    main()
