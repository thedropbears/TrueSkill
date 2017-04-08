import os
from collections import defaultdict
from flask import Flask, jsonify, request, send_file

from frc_trueskill import FrcTrueSkill
from slack import get_slackclient

import requests.packages.urllib3.contrib.appengine as urllib3_appengine
from requests_toolbelt.adapters import appengine
if urllib3_appengine.is_appengine_sandbox():
    appengine.monkeypatch()

app = Flask(__name__)
slack = get_slackclient()
trueskill = FrcTrueSkill()

# Get TBA key
try:
    import cloudstorage as gcs
    with gcs.open('/trueskill/tba.txt') as gcs_token_file:
        tba_token = gcs_token_file.readline().rstrip('\n')
except:
    tba_token = None

# Store predictons
prediction_msgs = {}
trueskill_predictions = defaultdict(dict)


@app.route('/')
def hello():
    return send_file('index.html')


@app.route('/tba-webhook', methods=['POST'])
def tba_webhook():
    msg_data = request.json['message_data']
    msg_type = request.json['message_type']
    if msg_type == 'verification':
        slack.api_call(
            'chat.postMessage', channel='trueskill', as_user=True,
            text='TBA verification key: %s' % msg_data)
    elif msg_type == 'ping':
        slack.api_call(
            'chat.postMessage', channel='trueskill', as_user=True,
            text='Just got pinged by The Blue Alliance.')
    elif msg_type == 'upcoming_match':
        predict(msg_data)
    elif msg_type == 'match_score':
        update(msg_data)
    return msg_type


@app.route('/api/predict/<red_alliance>/<blue_alliance>')
def api_predict(red_alliance, blue_alliance):
    red = [int(n) for n in red_alliance.split(',')]
    blue = [int(n) for n in blue_alliance.split(',')]
    return str(trueskill.predict(red, blue)), {'Content-Type': 'text/plain'}


# Please don't use this. This is a quick hack to get things working.
@app.route('/api/predictions')
def api_predictions_all():
    return jsonify(trueskill_predictions)


@app.route('/api/predictions/<event_key>')
def api_predictions(event_key):
    if event_key not in trueskill_predictions:
        return jsonify({}), 404
    return jsonify(trueskill_predictions[event_key])


@app.route('/predict')
def send_predict_page():
    return send_file('predict.html')


def predict(msg_data):
    blue = [int(key[3:]) for key in msg_data['team_keys'][0:3]]
    red = [int(key[3:]) for key in msg_data['team_keys'][3:6]]
    event = msg_data['event_name']
    event_key, match = msg_data['match_key'].split('_', 1)
    prediction = trueskill.predict(red, blue)
    red_text = ''
    blue_text = ''
    teams = trueskill.get_teams_at_event(event_key)

    trueskill_predictions[event_key][match] = prediction
    for r in red:
        red_text += '%d - %s\n' % (r, trueskill.nicknames[r])
    for b in blue:
        blue_text += '%d - %s\n' % (b, trueskill.nicknames[b])
    msg = send_prediction(event, match, red_text, blue_text, prediction)
    prediction_msgs[msg_data['match_key']] = msg


def send_prediction(event, match, red_text, blue_text, prediction):
    return slack.api_call(
        'chat.postMessage',
        channel='trueskill', as_user=True,
        text='*%s - %s*' % (event, match.upper()),
        attachments=[
            {'title': format(prediction, '.0%'), 'text': red_text, 'color': '#ff0000'},
            {'title': format(1-prediction, '.0%'), 'text': blue_text, 'color': '#0000ff'}
        ])


def update(msg_data):
    event = msg_data['event_name']
    alliances = msg_data['match']['alliances']
    red = alliances['red']
    blue = alliances['blue']
    if msg_data['match']['key'] not in prediction_msgs:
        predict({
            'team_keys': blue['teams'] + red['teams'],
            'event_name': event,
            'match_key': msg_data['match']['key']
        })
    result = trueskill.update(msg_data['match'])
    if result:
        return send_update(msg_data['match']['key'], result)


def send_update(match, result):
    # Find our previous prediction and resend with the winner marked on it
    prediction = prediction_msgs[match]
    msg = prediction['message']
    attachments = msg['attachments']
    for idx in 0, 1:
        if result[idx] is FrcTrueSkill.WON:
            # Alliance won (or tied)
            attachments[idx]['title'] += ' :trophy:'
    # Add another attachment with the current ratings
    attachments.append({'text': list_trueskills(match.split('_', 1)[0])})

    return slack.api_call(
        'chat.update', channel=prediction['channel'],
        ts=prediction['ts'], text=msg['text'],
        attachments=attachments)


@app.route('/api/trueskill/<int:team_number>')
def api_trueskill(team_number):
    return str(trueskill.skill(team_number)), {'Content-Type': 'text/plain'}


def get_trueskills_list(event_key):
    event_teams = trueskill.get_teams_at_event(event_key)
    skills = [(trueskill.skill(team), team, trueskill.nicknames[team])
              for team in event_teams]
    skills.sort(reverse=True)
    return skills


def list_trueskills(event_key):
    msg = []
    for i, (skill, team_number, nickname) in enumerate(get_trueskills_list(event_key), start=1):
        msg.append('%d. %s - %s - %.1f\n' % (i, team_number, nickname, skill))
    return ''.join(msg)


@app.route('/trueskills/<event_key>')
def list_trueskills_http(event_key):
    return list_trueskills(event_key), {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/api/trueskills/<event_key>')
def api_trueskills(event_key):
    return jsonify(get_trueskills_list(event_key))


if __name__ == "__main__":
    app.run(host=os.environ.get('OPENSHIFT_PYTHON_IP', '0.0.0.0'), port=int(os.environ.get('OPENSHIFT_PYTHON_PORT', 8080)))
