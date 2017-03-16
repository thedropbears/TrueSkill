import collections
import requests
from datetime import datetime, timedelta
from trueskill import TrueSkill, backends

Scores = collections.namedtuple('Scores', ('red', 'blue'))


class FrcTrueSkill:
    # Constants for sending requests to TBA.
    TBA_API_BASE = 'https://www.thebluealliance.com/api/v2'
    HEADERS = {"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"}

    # Ranks for TrueSkill.rate. Lower is better.
    WON = 0
    LOST = 1

    TIE = (WON, WON)
    RED_WIN = (WON, LOST)
    BLUE_WIN = (LOST, WON)

    def __init__(self):
        self.env = TrueSkill(draw_probability=0.02)
        self.trueskills = {}
        self.events = {}
        self.processed_matches = set()
        self.get_previous_matches()

    def init_teams(self, red_alliance, blue_alliance):
        for team in red_alliance + blue_alliance:
            if team not in self.trueskills:
                self.trueskills[team] = self.env.Rating()

    def update(self, match_data):
        if match_data['key'] in self.processed_matches:
            return None

        alliances = match_data['alliances']
        red_teams = alliances['red']['teams']
        blue_teams = alliances['blue']['teams']

        self.init_teams(red_teams, blue_teams)
        # Update ratings based on result
        corrected_scores = self.correct_scores(match_data)

        if corrected_scores.red == corrected_scores.blue:  # Tied
            if corrected_scores.red == -1:
                return None  # No result yet
            ranks = self.TIE
        elif corrected_scores.red > corrected_scores.blue:  # Red beat blue
            ranks = self.RED_WIN
        else:
            ranks = self.BLUE_WIN

        new_red, new_blue = self.env.rate([
            [self.trueskills[t] for t in red_teams],
            [self.trueskills[t] for t in blue_teams]], ranks)

        # Store the new values
        for team, rating in zip(red_teams + blue_teams, new_red + new_blue):
            self.trueskills[team] = rating
        self.processed_matches.add(match_data['key'])
        return ranks

    def predict(self, red_alliance, blue_alliance):
        self.init_teams(red_alliance, blue_alliance)
        a = [self.trueskills[t] for t in red_alliance]
        b = [self.trueskills[t] for t in blue_alliance]
        delta_mu = sum([x.mu for x in a]) - sum([x.mu for x in b])
        sum_sigma = sum([x.sigma ** 2 for x in a + b])
        player_count = len(a) + len(b)
        denominator = (player_count * (self.env.beta**2) + sum_sigma) ** 0.5
        return backends.cdf(delta_mu / denominator)

    def skill(self, team):
        if isinstance(team, int):
            team = 'frc%d' % team
        if team not in self.trueskills:
            self.trueskills[team] = self.env.Rating()
        return self.env.expose(self.trueskills[team])

    def get_teams_at_event(self, event):
        if event not in self.events:
            # We haven't got this one yet
            teams = requests.get("%s/event/%s/teams" % (self.TBA_API_BASE, event),
                                 headers=self.HEADERS)
            teams = teams.json()
            self.events[event] = teams
        return self.events[event]

    def get_previous_matches(self):
        all_matches = []
        events = requests.get(self.TBA_API_BASE + "/events/2017", headers=self.HEADERS)
        events = events.json()

        for event in events:
            if event['event_type'] > 5:
                continue
            if event['start_date'] <= str(datetime.date(datetime.today()+timedelta(days=1))):
                matches = requests.get("%s/event/%s/matches" % (self.TBA_API_BASE, event['key']),
                                       headers=self.HEADERS)
                matches = matches.json()
                all_matches += matches
        all_matches.sort(key=lambda m: m['time'])

        for match in all_matches:
            self.update(match)

    def correct_scores(self, match):
        alliances = match['alliances']
        red = alliances['red']
        blue = alliances['blue']

        score = match['score_breakdown']
        red_score = red['score']
        blue_score = blue['score']
        if score is None:
            return Scores(red_score, blue_score)

        red_stats = score['red']
        blue_stats = score['blue']

        if red_stats["rotorRankingPointAchieved"]:
            red_score += 100
        if red_stats["kPaRankingPointAchieved"]:
            red_score += 20

        if blue_stats["rotorRankingPointAchieved"]:
            blue_score += 100
        if blue_stats["kPaRankingPointAchieved"]:
            blue_score += 20

        return Scores(red_score, blue_score)
