import requests

headers = {
    'Content-type': 'application/json',
}


def send_slack_message(deployment_object) -> None:
    human_expiration_timestamp = deployment_object.human_expiration_timestamp
    json_data = {
        'text': f'Hello, <@U03JLDGHWG1> your GKE cluster is working!\n'
                f'The cluster will be expired in {human_expiration_timestamp}',
    }

    response = requests.post('https://hooks.slack.com/services/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',
                             headers=headers, json=json_data)
    print(response)

