from requests_toolbelt.adapters import appengine
appengine.monkeypatch()

import logging
import os
from flask import Flask, request
from frc_trueskill import FrcTrueSkill
from slack import Slack
import cloudstorage as gcs

app = Flask(__name__)
trueskill = FrcTrueSkill()

# Set up Slack integration
slack = Slack()

# Get TBA key
with gcs.open('/trueskill/tba.txt') as gcs_token_file:
    tba_token = gcs_token_file.readline().rstrip('\n')

@app.route('/')
def hello():
    return 'Hello World!'


@app.route('/tba-webhook', methods=['POST'])
def tba_webhook():
    msg_data = request.json['message_data']
    msg_type = request.json['message_type']
    if msg_type == 'verification':
        slack.message('TBA verification key: %s' % msg_data)
    if msg_type == 'ping':
        slack.message('Just been pinged by The Blue Alliance.')
    elif msg_type == 'upcoming_match':
        predict(msg_data)
    elif msg_type == 'match_score':
        update(msg_data)
    return msg_type


def predict(msg_data):
    blue = msg_data['team_keys'][0:3]
    red = msg_data['team_keys'][3:6]
    event = msg_data['event_name']
    event_key = msg_data['match_key'].split('_')[0]
    match = msg_data['match_key'].split('_')[1]
    prediction = trueskill.predict(red, blue)
    red_text = ''
    blue_text = ''
    teams = trueskill.get_teams_at_event(event_key)
    team_dict = dict(zip([team['key'] for team in teams], teams))
    for r in red:
        red_text += '%s - %s\n' % (r[3:], team_dict[r]['nickname'])
    for b in blue:
        blue_text += '%s - %s\n' % (b[3:], team_dict[b]['nickname'])
    slack.message(text='*%s - %s*' % (event, match.upper()),
            attachments=[{'title': '%i%%' % prediction,
                'text': red_text, 'color': '#ff0000'},
                {'title': '%i%%' % (100-prediction),
                    'text': blue_text, 'color': '#0000ff'}])

def update(msg_data):
    event_key = msg_data['match']['event_key']
    event = msg_data['event_name']
    alliances = msg_data['match']['alliances']
    red = alliances['red']
    blue = alliances['blue']
    trueskill.update(blue['teams'], blue['score'], red['teams'], red['score'])
    event_teams = trueskill.get_teams_at_event(event_key)
    skills = [(team['key'], trueskill.skill(team['key']), team['nickname']) for team in event_teams]
    skills = sorted(skills, key=lambda skill: skill[1], reverse=True)
    match = msg_data['match']['key'].split('_')[1].upper()
    msg = ''
    for skill in skills:
        msg += '%s - %s - %0.1f\n' % (skill[0][3:], skill[2], skill[1])
    slack.message(text='*%s - %s*' % (event, match),
            attachments=[{'text':msg}])

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
