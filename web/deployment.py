import logging
import os
import sys

from dotenv import load_dotenv

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


def main():
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


if __name__ == "__main__":
    main()
