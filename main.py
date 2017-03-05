import logging
import os
from flask import Flask, request
from frc_trueskill import FrcTrueSkill
from slackclient import SlackClient


app = Flask(__name__)
trueskill = FrcTrueSkill()
verify_data = {'verification_key': 'No verification code received'}

# Set up Slack integration
slack = SlackClient(os.environ.get('SLACK_TOKEN'))

@app.route('/')
def hello():
    slack_message('Hello world!')
    return 'Hello World!'


@app.route('/verify')
def verify():
    return verify_data['verification_key']


@app.route('/tba-webhook', methods=['POST'])
def tba_webhook():
    global verify_data
    msg_data = request.json['message_data']
    msg_type = request.json['message_type']
    if msg_type == 'verification':
        verify_data = msg_data
    elif msg_type == 'upcoming_match':
        predict(msg_data)
    elif msg_type == 'match_score':
        update(msg_data)
    return msg_type


def predict(msg_data):
    red = msg_data['team_keys'][0:3]
    blue = msg_data['team_keys'][3:6]
    event = msg_data['event_name']
    match = msg_data['match_key'].split('_')[1]
    prediction = trueskill.predict(red, blue)
    slack_message('%s - %s\n%s, %s, %s vs %s, %s, %s'
            % (event, match, red[0], red[1], red[2], blue[0], blue[1], blue[2]))
    slack_message('%i%% : %i%%' % (prediction, 100-prediction))

def update(msg_data):
    event_key = msg_data['match']['event_key']
    event = msg_data['event_name']
    alliances = msg_data['match']['alliances']
    red = alliances['red']
    blue = alliances['blue']
    trueskill.update(blue['teams'], blue['score'], red['teams'], red['score'])
    event_teams = trueskill.events[event_key]
    skills = [(team['key'], trueskill.skill(team['key'])) for team in event_teams]
    skills = sorted(skills, key=lambda skill: skill[1], reverse=True)
    slack_message('%s' % event)
    for skill in skills:
        slack_message('%s: %f' % skill)

def slack_message(msg):
    slack.api_call('chat.postMessage', channel='#trueskill',
            text=msg, username='trueskillbot', icon_emoji=':robot_face:')

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.\n%s\n' % e, 500
