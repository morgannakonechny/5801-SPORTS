import sys
import pandas as pd
from game import Game
from interval_tree import Interval, IntervalNode, IntervalTree

class Scheduler:
	# method to generate pairs of teams in a league in a round robin manner
	@staticmethod
	def createPairs(league):
		# create lists to store the teams
		homeTeams = []
		awayTeams = []
		# splits the teams into two evenly sized groups by alternating which list they are added to
		for i in range(len(league["teams"])):
			if i % 2 == 0:
				homeTeams.append(league["teams"][i])
			else:
				awayTeams.append(league["teams"][i])
		# if there is an odd number of teams, create a dummy team to represent a bye
		if len(awayTeams) < len(homeTeams):
			awayTeams.append("bye")
		# set the pairs key to 
		league["pairs"] = [homeTeams, awayTeams]
		
		
	@staticmethod
	def roundRobin(league):
        # cycle the lists
		home = league["pairs"][0]
		away = league["pairs"][1]
		newAway = [home[1]]
		if len(home) > 2 and len(away) > 2:
			for i in range(len(away) - 1):
				newAway.append(away[i])
			for i in range(1, len(home) - 1):
				home[i] = home[i + 1]
			home[-1] = away[-1]
			league["pairs"] = [home, newAway]		
			
	@staticmethod
	def rotatePairs(league):
		home = league["pairs"][0]
		away = league["pairs"][1]

		# new lists to be populated with "rotated teams"
		newHome = []
		newAway = []

		# first element of home is anchored and should stay the same
		newHome.append(home[0])
		newHome += home[2:]
		newHome.append(away[-1])

		# rotate away
		newAway.append(home[1])
		newAway += away[:len(away) - 1]

		# update league["pairs"]
		league["pairs"] = [newHome, newAway]

				
	@staticmethod
	def run(case: str = "case1") -> int:
		"""
		Scheduling algorithm that takes in various data files to schedule games involving different sports, regions, and leagues.
		
		Return:
			int: Returns 0 if successful.
		"""
		
		# SAM CHANGE: back to ./data
		input_teams: str = f"../../data/{case}/team.csv"
		input_venues: str = f"../../data/{case}/venue.csv"
		input_leagues: str = f"../../data/{case}/league.csv"

		input_sports = {
			1: "Basketball",
			2: "Soccer",
			3: "Baseball",
			4: "Softball",
			5: "Kickball",
			6: "Dodgeball",
			7: "Hockey"
		}
		
		# read data into pandas dataframes
		team_df = pd.read_csv(input_teams)
		venue_df = pd.read_csv(input_venues)
		league_df = pd.read_csv(input_leagues)
		
		# convert dataframes to a list of dictionaries
		leagues = league_df.to_dict(orient="records")
		venues = venue_df.to_dict(orient="records")
		teams = team_df.to_dict(orient="records")

		# add appropriate teams to their corresponding leagues
		# [{leagueid: 1, ... teams: [{team 1 dict}, {team 2 dict}] } ]
		for league in leagues:
			league_teams = []
			for team in teams:
				if team["leagueId"] == league["leagueId"]:
					league_teams.append(team)
			league["teams"] = league_teams
			league["gamesPlayed"] = 0

			if len(league["teams"]) < 2: 
				# SAM: comment this back in
				print("not enough teams!")
				# return 1	# cannot create schedule for a league with only team
			
			# check that there are a valid number of weeks in the league
			numWeeks = league["seasonEnd"] - league["seasonStart"] + 1
			if numWeeks < 1:
				# SAM: comment this back in/out
				print("not enough weeks!")
				# return 1	# cannot create schedule for a league with 0 weeks, or start week later than end week
			
			# extract the number of games that should be played every week by a team to reach numberOfGames
			league["gamesPerWeek"] = int((league["numberOfGames"] / numWeeks) + 0.5)
			# create the initial groupings of teams
			Scheduler.createPairs(league)

		games = []
		
		# these create an interval tree for each venue containing available times for that venue
		interval_trees = []
		for venue in venues:
			schedule_tree = IntervalTree()
			availability_tree = IntervalTree()
			for week in range(1, 53):
				for day in range(1, 8):
					closed_until = Interval(0, ven[f"d{day}Start"], day, week)
					closed_after = Interval(ven[f"d{day}End"], 23.5, day, week)
					schedule_tree.insert(closed_until)
					schedule_tree.insert(closed_after)
					available = Interval(ven[f"d{day}Start"], ven[f"d{day}End"], day, week)
					availability_tree.insert(available)
			interval_trees.append({f"{venue["venueId"]}Sched": schedule_tree, f"{venue["venueId"]}Avail": availability_tree})

		# each game should last 2 hours
		game_duration = 2 
		# schedule games for each league
		for league in leagues:
			# for each week in the league
			for week in range(league["seasonStart"], league["seasonEnd"] + 1):
				# for each game that should be scheduled in a week
				for game_of_week in range(0, league["gamesPerWeek"]):
					# schedule a game for each pair of teams	
					homeTeams = league["pairs"][0]
					awayTeams = league["pairs"][1]
					# iterate through the pairs
					for pair_idx in range(0, len(homeTeams)):
						t1 = homeTeams[pair_idx]
						t2 = awayTeams[pair_idx]
						# try to schedule a game
						# try each day
						for day in range(1, 8):
							# try each venue
							for ven in venues:
								# team 1 availability
								t1_avail = Interval(t1[f"d{day}Start"], t1[f"d{day}End"], day, week)
								# team 2 availability
								t2_avail = Interval(t2[f"d{day}Start"], t2[f"d{day}End"], day, week)

								# check for team availability overlap
								# dur for duration
								team_overlap, team_dur = t1_avail.get_overlap(t2_avail)
								if team_overlap and team_dur >= game_duration:
									# check for overlap with venue availability (need this to get possible intervals)
									# need both because 
									venue_overlap = interval_trees[f"{ven["venueId"]}Avail"].overlap(team_overlap)
									# check that the overlap is long enough
									for overlap in venue_overlap:
										if overlap.duration() >= game_duration:
											# create a game with the first game duration available
											# insert this interval into the tree for the venue




			


		# start by extracting the team/venue/league data into the dataframes from the csv files -- DONE
		# determine the number of games that need to be played each week in order to reach the total number of games for each league -- DONE
		# separate the teams based on league -- DONE
		# for each week of the year:
			# check if each league is playing during that week
			# if the league is playing: 
				# Pair up each of the teams in a league for each league 
					# NOTE: we'll want to keep track of the initial pairings for round robin purposes ----- DONE
				# Use round robin to generate enough sets of pairs so that the league meets the number of games needed for the week 
				# for each pair: 
				#     create an intervalTree with the availabilities of each team and store the list of overlapping intervals for that team
				#     create an intervalTree with the overlapping availabilities of the pair and all venue availabilities
							# we'll probably want a function for making the tree with venue availabilities because we'll likely need many copies of it
				#     Store the list of overalapping intervals for that pair and the venues
				# NOTE: if any pair don't have any viable overlaps (needs to be long enough for a whole game), 
					# then regroup the teams (go to next round robin pairing and start over)

				# use a greedy algorithm that schedules pairs starting with the pairs with the fewest viable overlaps
				# create games for each pair this way and add the games to the game list
				# Build an intervalTree as matches are scheduled
				# NOTE: I'm not sure if this will be optimal, but I figured it's a fair guess
				# check to make sure there are no conflicting games. 
					# If there are, resolve them by keeping track of the game (maybe add the list of viable overlaps to games)
					# and then selecting a different time slot from viable overlaps
					# This will get tricky as more teams are scheduled, may need some tweaking
		
		
		
		'''
		for each league in leagues:
		|	get teams where leagueID = league.id
		|	if teams < 2:
		|	|	return 1
		|	pairs = generatePairs()
		|	for _ in league.numGames:
		|	|	schedule = scheduleGame()
		|	|	if !schedule:
		|	|	|	return 2
		|	|	games.append(new Game())
		'''

		# leaguesDict = {}


		# intervalTrees = {}
		# for venue in venues:
		# 	intervalTrees[f"Venue{venue.id}"] = IntervalTree()
		# for league in leagues:
		# 	if league.teams.length < 2:
		# 		return 1 # cannot schedule not enough teams
			
			
		# 	for team in league.teams:




		schedule_records = []
		for game in games:
			game.dump()
			team1 = team_df[team_df["teamId"] == game.team1_id].to_dict(orient="records")
			team2 = team_df[team_df["teamId"] == game.team2_id].to_dict(orient="records")
			venue = venue_df[venue_df["venueId"] == game.venue_id].to_dict(orient="records")
			league = league_df[league_df["leagueId"] == team1[0]["leagueId"]].to_dict(orient="records")
			schedule_records.append({
				"team1Name": team1[0]["name"],
				"team2Name": team2[0]["name"],
				"week": game.week, 
				"day": game.day, 
				"start": game.start, 
				"end": game.end,
				"season": game.season,
				"league": league[0]["leagueName"],
				"location": f"{venue[0]["name"]} Field #{venue[0]["field"]}"
			})
			
		schedule_df = pd.DataFrame(schedule_records)
		# SAM CHANGE
		schedule_df.to_csv(f"../../data/{case}/schedule.csv", index=False)		
		schedule_df.to_json(f"../../data/{case}/schedule.json")
		
		return 0
	
if __name__ == "__main__":
	case = sys.argv[1]	

	schedule = Scheduler()
	schedule.run(case)