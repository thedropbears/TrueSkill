from trueskill import TrueSkill, Rating, rate
import argparse
import requests
from datetime import datetime


class FrcTrueSkill:
    def __init__(self):
        self.env = TrueSkill(draw_probability=0.02)
        self.trueskills = {}
        self.events = {}
        #self.get_previous_matches()
        #for team in self.trueskills.keys():
         #   print team, self.skill(team)

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
        new_red, new_blue = self.env.rate([[self.trueskills[number] for number in red_alliance],
                                      [self.trueskills[number] for number in blue_alliance]], ranks)
        # Store the new values
        new_ratings = new_red + new_blue
        for rating, team_number in zip(new_ratings, red_alliance + blue_alliance):
            self.trueskills[team_number] = rating


    def predict(self, red_alliance, blue_alliance):
        proba = self.env.quality([[self.trueskills[team] for team in red_alliance],
                            [self.trueskills[team] for team in blue_alliance]])
        return round(proba*100)

    def skill(self, team):
        return self.env.expose(self.trueskills[team])

    def get_previous_matches(self):
        started_events = []
        all_matches = []
        events = requests.get("https://www.thebluealliance.com/api/v2/events/2017")
        events = events.json()

        for event in events:
            if event['event_type'] > 5:
                continue
            if event['start_date'] < str(datetime.date(datetime.today())):
                started_events.append(event["key"])

            teams = requests.get("https://www.thebluealliance.com/api/v2/event/"+event['key']+"/teams", headers={"X-TBA-App-Id":"frc-4774:TrueSkill:1.0"})
            teams = teams.json()
            self.events[event['key']] = teams

        for event in started_events:
            matches = requests.get("https://www.thebluealliance.com/api/v2/event/"+event+"/matches", headers={"X-TBA-App-Id":"frc-4774:TrueSkill:1.0"})

            matches = matches.json()
            all_matches += matches
        all_matches.sort(key=lambda m: m['time'])

        for match in all_matches:
            score = match['score_breakdown']
            if score is None:
                continue

            red_stats = score['red']
            blue_stats = score['blue']

            alliances = match['alliances']
            red = alliances['red']
            blue = alliances['blue']

            if red_stats["rotor3Engaged"]:
                red['score'] += 100
            if red_stats["kPaRankingPointAchieved"]:
                red['score'] += 20

            if blue_stats["rotor3Engaged"]:
                blue['score'] += 100
            if blue_stats["kPaRankingPointAchieved"]:
                blue['score'] += 20

            self.update(red['teams'], red['score'], blue['teams'], blue['score'])
