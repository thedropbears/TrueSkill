from requests_toolbelt.adapters import appengine
appengine.monkeypatch()

import logging
import os
from flask import Flask, jsonify, request
from frc_trueskill import FrcTrueSkill
from slack import get_slackclient
import cloudstorage as gcs

app = Flask(__name__)
slack = get_slackclient()
trueskill = FrcTrueSkill()

# Get TBA key
try:
    with gcs.open('/trueskill/tba.txt') as gcs_token_file:
        tba_token = gcs_token_file.readline().rstrip('\n')
except:
    tba_token = None

# Store predictons
prediction_msgs = {}

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


@app.route('/api/predict/<red_alliance>/<blue_alliance>')
def api_predict(red_alliance, blue_alliance):
    red_alliance = ['frc%d' % int(n) for n in red_alliance.split(',')]
    blue_alliance = ['frc%d' % int(n) for n in blue_alliance.split(',')]
    return str(trueskill.predict(red_alliance, blue_alliance)), {'Content-Type': 'text/plain'}


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
    retval = send_prediction(event, match, red_text, blue_text, prediction)
    prediction_msgs[msg_data['match_key']] = retval


def send_prediction(event, match, red_text, blue_text, prediction):
    return slack.api_call('chat.postMessage',
        channel='trueskill', as_user=True,
        text='*%s - %s*' % (event, match.upper()),
        attachments=[
            {'title': format(prediction, '.0%'), 'text': red_text, 'color': '#ff0000'},
            {'title': format(1-prediction, '.0%'), 'text': blue_text, 'color': '#0000ff'}
        ])


def update(msg_data):
    event_key = msg_data['match']['event_key']
    event = msg_data['event_name']
    alliances = msg_data['match']['alliances']
    match = msg_data['match']['key'].split('_')[1].upper()
    red = alliances['red']
    blue = alliances['blue']
    if not msg_data['match']['key'] in prediction_msgs:
        payload = {'team_keys': blue['teams']+red['teams'], 'event_name': event,
                'match_key': msg_data['match']['key']}
        predict(payload)
    result = trueskill.update(msg_data['match'])
    if result:
        return send_update(msg_data['match']['key'], result)

def send_update(match, result):
    # Find our previous prediction and resend with the winner marked on it
    prediction = prediction_msgs[match]
    msg = prediction['message']
    attachments = msg['attachments']
    for idx in [0, 1]:
        if result[idx] == 0:
            # Alliance won (or tied)
            attachments[idx]['title'] += ' :trophy:'
    # Add another attachment with the current ratings
    attachments.append({'text': list_trueskills(match.split('_')[0])})

    return slack.api_call('chat.update', channel=prediction['channel'],
            ts=prediction['ts'],text=msg['text'],
            attachments=attachments)


@app.route('/api/trueskill/<int:team_number>')
def api_trueskill(team_number):
    return str(trueskill.skill('frc%d' % team_number)), {'Content-Type': 'text/plain'}


def get_trueskills_list(event_key):
    event_teams = trueskill.get_teams_at_event(event_key)
    skills = [(trueskill.skill(team['key']), int(team['key'][3:]), team['nickname']) for team in event_teams]
    skills.sort(reverse=True)
    return skills


def list_trueskills(event_key):
    msg = []
    for skill, team_number, nickname in get_trueskills_list(event_key):
        msg.append('%s - %s - %.1f\n' % (team_number, nickname, skill))
    return ''.join(msg)


@app.route('/trueskills/<event_key>')
def list_trueskills_http(event_key):
    return list_trueskills(event_key), {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/api/trueskills/<event_key>')
def api_trueskills(event_key):
    return jsonify(get_trueskills_list(event_key))


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
