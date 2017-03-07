import os
import cloudstorage as gcs
from slackclient import SlackClient

class Slack:
    def __init__(self):
        # We need the Slack bot secret token
        # Try the environment variable first
        slack_token = os.getenv('SLACK_TOKEN', None)
        if not slack_token:
            # We must be on the Google App Engine
            with gcs.open('/trueskill/slack.txt') as gcs_token_file:
                slack_token = gcs_token_file.readline().rstrip('\n')
        self.slack_client = SlackClient(slack_token)
