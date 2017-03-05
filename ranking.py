from trueskill import TrueSkill, Rating, rate
import argparse
from pytba import api as tba
import math


class FrcTrueSkill:
    def __init__(self):
        self.env = TrueSkill(draw_probability=0.02)
        self.trueskills = {}
        self.events = {}

    def update(self, red_alliance, red_score, blue_alliance, blue_score):
        # Calculate teams per alliance
        for alliance in [red_alliance, blue_alliance]:
            for team in alliance:
                if not team in self.trueskills:
                    self.trueskills[team] = self.env.Rating()
        # Update ratings based on result
        if red_score == blue_score:  # Tied
            if red_score == -1:
                return  # No result yet
            ranks = [0, 0]
        elif red_score > blue_score:  # Red beat blue
            ranks = [0, 1]  # Lower is better
        else:
            ranks = [1, 0]
        new_red, new_blue = self.env.rate([[trueskills[number] for number in red_alliance],
                                      [trueskills[number] for number in blue_alliance]], ranks)
        # Store the new values
        new_ratings = new_red + new_blue
        for rating, team_number in zip(new_ratings, red_alliance + blue_alliance):
            self.trueskills[team_number] = rating


    def predict(self, red_alliance, blue_alliance):
        proba = self.env.quality([[teams[number] for number in red_alliance],
                            [teams[number] for number in blue_alliance]])
        return math.round((1.0-proba)*100)

    def skill(self, team):
        return self.env.expose(trueskills[team])


def parse_matches(matches, env, predict=False):
    count = 0.0
    draws = 0.0

    # Initialise our trueskills dictionary
    trueskills = {}
    for row in matches:
        alliances = row['alliances']
        red_alliance = alliances['red']['teams']
        blue_alliance = alliances['blue']['teams']
        # Calculate teams per alliance
        for alliance in [red_alliance, blue_alliance]:
            for team in alliance:
                if not team in trueskills:
                    trueskills[team] = env.Rating()
        # Update ratings based on result
        if alliances['red']['score'] == alliances['blue']['score']:  # Tied
            if alliances['red']['score'] == -1:
                if predict:
                    proba = env.quality([[teams[number] for number in red_alliance],
                                        [teams[number] for number in blue_alliance]])
                    print(row['match_number'], [str(number)[3:] for number in red_alliance], [str(number)[3:] for number in blue_alliance], "Win probability: %2.0f:%2.0f"  %((1.0-proba)*100,proba*100))
                else:
                    continue  # No result yet
            ranks = [0, 0]
            draws = draws + 1
        elif alliances['red']['score'] > alliances['blue']['score']:  # Red beat blue
            ranks = [0, 1]  # Lower is better
        else:
            ranks = [1, 0]
        new_red, new_blue = env.rate([[trueskills[number] for number in red_alliance],
                                      [trueskills[number] for number in blue_alliance]], ranks)
        count = count + 1
        # Store the new values
        new_ratings = new_red + new_blue
        for rating, team_number in zip(new_ratings, red_alliance + blue_alliance):
            trueskills[team_number] = rating
    if not predict:
        if count > 0:
            print("Draw rate: %f" % (draws / count))
        print("Matches: %i" % count)
    return trueskills

def get_all_matches(year):
    matches = []
    events = tba.tba_get('events/%s' % year)
    for event in events:
        matches += tba.event_get(event['key']).matches
    return sorted(matches, key=lambda k: float('inf') if k['time'] is None else k['time'])

def sort_by_trueskill(trueskills, env):
    return sorted(trueskills.items(), key=lambda k: env.expose(k[1]), reverse=True)  # Sort by trueskill

def sort_by_name(trueskills):
    return sorted(trueskills.items(), key=lambda k: ('0000' + k[0][3:])[-4:])  # Sort by team number

def print_trueskills(trueskills, env):
    for k,v in trueskills:
        print('%s: %f' % (k, env.expose(v)))


if __name__ == '__main__':
    import datetime
    now = datetime.datetime.now()
    tba.set_api_key('frc4774', 'trueskill', '1.0')
    parser = argparse.ArgumentParser(description='Run TrueSkill algorithm on event results.')
    parser.add_argument('--predict', help='Predict unplayed matches', dest='predict', action='store_true')
    parser.add_argument('--year', help='All matches in all events in specified year', type=str, default=str(now.year))

    args = parser.parse_args()

    # Set the draw probability based on previous data - around 3%
    env = TrueSkill(draw_probability=0.025)  # Try tweaking tau and beta too
    matches = get_all_matches(args.year)
    results = parse_matches(matches, env)
    results = sort_by_trueskill(results, env)
    #results = sort_by_name(results)
    print_trueskills(results, env)
