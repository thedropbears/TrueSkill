from trueskill import TrueSkill, Rating, rate
import fnmatch
import os
import csv

def parse_data():
    # Get a directory listing.
    # We want to find any files ending in _matches.csv
    matches = []
    for root, dirnames, filenames in os.walk('the-blue-alliance-data'):
        for filename in fnmatch.filter(filenames, '*_matches.csv'):
            matches.append(os.path.join(root, filename))
    matches = sorted(matches)
    #print matches
    
    # Set the draw probability based on previous data - around 3%
    env = TrueSkill(draw_probability=0.03) # Try tweaking tau and beta too
    
    count = 0.0
    draws = 0.0
    
    # Initialise our teams dictionary
    teams = {}
    try:
        # Now start iterating over the files to build up rankings
        for matchfile in matches:
            with open(matchfile, 'rb') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                headers = csvreader.next() # Ignore header row
                for row in csvreader:
                    if len(row) % 2 == 0: # Weird row - odd number of teams
                        continue 
                    red_alliance = ()
                    blue_alliance = ()
                    # Calculate teams per alliance
                    n = (len(row) - 3) / 2 # Number of teams per alliance
                    for red in range(1, n+1):
                        if not row[red] in teams:
                            teams[row[red]] = env.Rating()
                        red_alliance = red_alliance + (teams[row[red]],)
                    for blue in range(n+1, 2*n+1):
                        if not row[blue] in teams:
                            teams[row[blue]] = env.Rating()
                        blue_alliance = blue_alliance + (teams[row[blue]],)
                    # Update ratings based on result
                    if row[2*n+1] == row[2*n+2]: # Tied
                        ranks = [0, 0]
                        draws = draws + 1
                    elif row[2*n+1] > row[2*n+2]: # Red beat blue
                        ranks = [0, 1] # Lower is better
                    else:
                        ranks = [1, 0]
                    new_red, new_blue = env.rate([red_alliance, blue_alliance], ranks)
                    count = count + 1
                    # Store the new values
                    new_ratings = new_red + new_blue
                    for i in range(len(new_ratings)):
                        teams[row[1+i]] = new_ratings[i]
    except:
        print matchfile
    #teams = sorted(teams.iteritems(), key=lambda (k,v): (('0000'+k[3:])[-4:],v)) # Sort by team number
    teams = sorted(teams.iteritems(), key=lambda (k,v): (env.expose(v), k)) # Sort by trueskill
    for k,v in teams:
        print k + ': ' + str(env.expose(v))
    
    print "Draw rate: " + str(draws/count)

if __name__ == '__main__':
    parse_data()
