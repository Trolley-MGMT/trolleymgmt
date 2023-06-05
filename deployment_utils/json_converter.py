import json
from argparse import ArgumentParser, RawDescriptionHelpFormatter

# incoming_string = """
# {"payload":{\"name\":\"Firefox\",\"pref_url\":\"about:config\"}}
# """

def main(incoming_string: str = ''):
    name = json.loads(incoming_string)['name']
    print(name)
    url = json.loads(incoming_string)['url']
    print(url)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--incoming_string', default='', type=str, help='The stringified JSON of all the requested parameters')
    args = parser.parse_args()
    main(incoming_string=args.incoming_string)