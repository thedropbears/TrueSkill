import logging
from slacker import Slacker
from flask import Flask, request
from frc_trueskill import FrcTrueSkill

app = Flask(__name__)
slack = Slacker('xoxp-14694181588-14700916992-149818386853-291b2003af5865e54e895136b070257a')
trueskill = FrcTrueSkill()
verify_data = {'verification_key': 'No verification code received'}


@app.route('/')
def hello():
    slack.chat.post_message('#trueskill', 'Hello world!')
    return 'Hello World!'


@app.route('/verify')
def verify():
    return verify_data['verification_key']


@app.route('/tba-webhook', methods=['POST'])
def tba_webhook():
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
    slack.chat.post_message('#trueskill', '%s - %s\n%s, %s, %s vs %s, %s, %s'
            % (event, match, red[0], red[1], red[2], blue[0], blue[1], blue[2]))
    slack.chat.post_message('#trueskill', '%i%% : %i%%' % (prediction, 100-prediction))

def update(msg_data):
    event_key = msg_data['match']['event_key']
    event = msg_data['event_name']
    alliances = msg_data['match']['alliances']
    red = alliances['red']
    blue = alliances['blue']
    trueskill.update(blue['teams'], blue['score'], red['teams'], red['score'])
    event_teams = trueskill.trueskills.keys() #trueskill.events[event_key]
    skills = [(team, trueskill.skill(team)) for team in event_teams]
    skills = sorted(skills, key=lambda skill: skill[1], reverse=True)
    slack.chat.post_message('#trueskill', '%s' % event)
    for skill in skills:
        slack.chat.post_message('#trueskill', '%s: %f' % skill)


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.\n%s\n' % e, 500
