import os
from slackclient import SlackClient


def get_slackclient():
    # We need the Slack bot secret token
    # Try the environment variable first
    slack_token = os.getenv('SLACK_TOKEN', None)
    if not slack_token:
        # We must be on the Google App Engine
        import cloudstorage as gcs
        with gcs.open('/trueskill/slack.txt') as gcs_token_file:
            slack_token = gcs_token_file.readline().rstrip('\n')
    return SlackClient(slack_token)
