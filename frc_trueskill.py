from trueskill import TrueSkill, Rating, rate
import argparse
#from pytba import api as tba


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
