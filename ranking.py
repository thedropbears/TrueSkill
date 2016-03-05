from trueskill import TrueSkill, Rating, rate
import argparse
import json
import httplib

def get_event_matches(event):
    conn = httplib.HTTPSConnection('www.thebluealliance.com')
    header = {'X-TBA-App-Id': '%s:%s:%s' % ('frc4774', 'trueskill', '1.0')}
    conn.request('GET', '/api/v2/event/%s/matches' % event, None, header)
    response = conn.getresponse()
    response = json.loads(response.read().decode("utf-8"))
    return response

def get_matches(event=None, year=None):

    if event:
        return get_event_matches(event)
    if year:
        conn = httplib.HTTPSConnection('www.thebluealliance.com')
        header = {'X-TBA-App-Id': '%s:%s:%s' % ('frc4774', 'trueskill', '1.0')}
        conn.request('GET', '/api/v2/events/%s' % year, None, header)
        response = conn.getresponse()
        response = json.loads(response.read().decode("utf-8"))
        all_events = []
        for event in response:
            name = event['key']
            all_events += get_event_matches(name)
        return all_events

def parse_matches(matches, env):

    count = 0.0
    draws = 0.0

    # Initialise our teams dictionary
    teams = {}
    for row in matches:
        alliances = row['alliances']
        red_alliance = alliances['red']['teams']
        blue_alliance = alliances['blue']['teams']
        # Calculate teams per alliance
        for alliance in [red_alliance, blue_alliance]:
            for team in alliance:
                if not team in teams:
                    teams[team] = env.Rating()
        # Update ratings based on result
        if alliances['red']['score'] == alliances['blue']['score']:  # Tied
            if alliances['red']['score'] == -1:
                continue  # No result yet
            ranks = [0, 0]
            draws = draws + 1
        elif alliances['red']['score'] > alliances['blue']['score']:  # Red beat blue
            ranks = [0, 1]  # Lower is better
        else:
            ranks = [1, 0]
        new_red, new_blue = env.rate([[teams[number] for number in red_alliance],
                                      [teams[number] for number in blue_alliance]], ranks)
        count = count + 1
        # Store the new values
        new_ratings = new_red + new_blue
        for rating, team_number in zip(new_ratings, red_alliance + blue_alliance):
            teams[team_number] = rating
    print "Draw rate: " + str(draws / count)
    print "Matches: " + str(count)
    return teams

def sort_by_trueskill(teams, env):
    return sorted(teams.iteritems(), key=lambda (k, v): (env.expose(v), k))  # Sort by trueskill

def sort_by_name(teams):
    return sorted(teams.iteritems(), key=lambda (k, v): (('0000' + k[3:])[-4:], v))  # Sort by team number

def print_teams(teams, env):
    for k,v in teams:
        print k + ': ' + str(env.expose(v))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run TrueSkill algorithm on event results.')
    parser.add_argument('--event', help='TheBlueAlliance event code')
    parser.add_argument('--year', help='All matches in all events in specified year', type=str)

    args = parser.parse_args()

    # Set the draw probability based on previous data - around 3%
    env = TrueSkill(draw_probability=0.01)  # Try tweaking tau and beta too
    matches = get_matches(event=args.event, year=args.year)
    teams = parse_matches(matches, env)
    teams = sort_by_trueskill(teams, env)
    print_teams(teams, env)
