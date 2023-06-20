import logging
import os

from dotenv import load_dotenv

DOCKER_ENV = os.getenv('DOCKER_ENV', False)

log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'{os.getcwd()}/web/{log_file_name}'
else:
    log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

project_folder = os.path.expanduser(os.getcwd())
load_dotenv(os.path.join(project_folder, '.env'))
logger.info(f'project_folder is: {project_folder}')

TROLLEY_URL = os.getenv('TROLLEY_URL', "https://trolley.com")


def main():
    with open('web/static/pre_script.js', 'r') as f:
        lines = f.readlines()
        print(f'reading the pre_script.js {lines}')

    with open('web/static/script.js', 'w') as f:
        print(f'Current directory is: {os.getcwd()}')
        print('successfully opened the static.js file')
        logger.info('successfully opened the static.js file')
        for line in lines:
            logger.info(f'line value is: {line}')
            if "trolley_url = " in line:
                line = f"    let trolley_url = '{TROLLEY_URL}';\n"
            try:
                f.write(line)
                logger.info(f'Writing of the file succeeded')
            except Exception as e:
                logger.error(f'Writing of the file failed because: {e}')


if __name__ == "__main__":
    main()
