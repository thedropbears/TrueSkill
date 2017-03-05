import os
import cloudstorage as gcs
from slackclient import SlackClient

class Slack:
    def __init__(self):
        # We need the Slack bot secret token
        # Try the environment variable first
        slack_token = os.environ.get('SLACK_TOKEN')
        if not slack_token:
            # We must be on the Google App Engine
            gcs_token_file = gcs.open('slack.txt')
            slack_token = gcs_token_file.readline()
            gcs_token_file.close()
        self.slack_client = Slack(slack_token)

    def message(self, msg, channel='#trueskill'):
        self.slack_client.api_call('chat.postMessage', channel=channel,
                text=msg, username='trueskillbot', icon_emoji=':robot_face:')
