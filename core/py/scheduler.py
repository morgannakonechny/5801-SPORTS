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

	# schedule a game in a given week
	@staticmethod
	def schedule_game(team1, team2, venues, week, interval_trees, game_duration, season):
		# check each day for availability
		for day in range(1, 8):
			# SAM CHANGE
			print(f"Trying day {day}...")

			# get each team's availability for that day
			t1_avail = Interval(team1[f"d{day}Start"], team1[f"d{day}End"], day, week)
			t2_avail = Interval(team2[f"d{day}Start"], team2[f"d{day}End"], day, week)

			# check that they have overlapping availability that day and it is long enough for game_duration
			team_overlap, team_overlap_duration = t1_avail.get_overlap(t2_avail)
			if team_overlap and team_overlap_duration >= game_duration:
				# SAM CHANGE
				print(f"\tTeams have overlap for day {day}...")
				# check each venue for availability
				for venue in venues:
					# SAM CHANGE
					print(f"\tTrying venue {venue["venueId"]}...")
					# get the list of overlapping intervals with the venue (the availability for that day)
					venue_overlap = interval_trees[f"{venue['venueId']}Avail"].overlap(team_overlap)
					# if the team availability aligns with the venues hours for that day
					if venue_overlap:
						# SAM CHANGE
						print(f"\t\tVenue has overlap for day {day}...")
						# find a timeslot that doesn't overlap with any other matches at the given venue
						game_start = team_overlap.start
						scheduled = False
						while (not scheduled and ((game_start + game_duration) <= team_overlap.end)):
							# interval for the game
							cur_slot = Interval(game_start, game_start + game_duration, day, week)
							# check that the slot doesn't intersect with any scheduled games
							slot_overlap = interval_trees[f"{venue["venueId"]}Sched"].overlap(cur_slot)
							# can schedule the game
							if not slot_overlap:
								# SAM CHANGE
								print(f"\t\tFOUND TIME SLOT: {game_start}-{game_start+game_duration}")
								# add interval to venue's interval tree
								interval_trees[f"{venue['venueId']}Sched"].insert(cur_slot)
								# set scheduled to true
								scheduled = True
								# return the game?
								return Game(team1["teamId"], team2["teamId"], week, day, season, game_start, game_start+game_duration, venue["venueId"])
							else:
								game_start += 0.5
		# no availability for the teams at any venue
		return None


						

				
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

			numWeeks = league["seasonEnd"] - league["seasonStart"] + 1

			# check that there are at least 2 teams in the league, there is at least 1 week in the season, and there is at least 1 game
			if (len(league["teams"]) >= 2 and numWeeks >= 1 and league["numberOfGames"] > 0):
				league["valid"] = True
				
				# extract the number of games that should be played every week by a team to reach numberOfGames
				league["gamesPerWeek"] = int((league["numberOfGames"] / numWeeks) + 0.5)
				# create the initial groupings of teams
				Scheduler.createPairs(league)
			else:
				league["valid"] = False

		games = []
		
		# these create an interval tree for each venue containing available times for that venue
		interval_trees = {}
		for venue in venues:
			schedule_tree = IntervalTree()
			availability_tree = IntervalTree()
			for week in range(1, 53):
				for day in range(1, 8):
					available = Interval(venue[f"d{day}Start"], venue[f"d{day}End"], day, week)
					availability_tree.insert(available)
			interval_trees[f"{venue['venueId']}Sched"] = schedule_tree
			interval_trees[f"{venue['venueId']}Avail"] = availability_tree

		# each game should last 2 hours
		game_duration = 2 
		# schedule games for each league
		for league in leagues:
			if league["valid"]:
				# for each week in the league
				for week in range(league["seasonStart"], league["seasonEnd"]):
					# for each game that should be scheduled in a week
					for game_of_week in range(0, league["gamesPerWeek"]):
						# schedule a game for each pair of teams	
						homeTeams = league["pairs"][0]
						awayTeams = league["pairs"][1]
						# iterate through the pairs
						for pair_idx in range(0, len(homeTeams)):
							t1 = homeTeams[pair_idx]
							t2 = awayTeams[pair_idx]
							# attempt to schedule a game
							if (t1 != "bye" and t2 != "bye"):
								game = Scheduler.schedule_game(t1, t2, venues, week, interval_trees, game_duration, league["season"])
								# if successful, add the game to the list of games
								if game:
									games.append(game)
						# rotate the teams
						Scheduler.rotatePairs(league)
		
		
		# '''
		# for each league in leagues:
		# |	get teams where leagueID = league.id
		# |	if teams < 2:
		# |	|	return 1
		# |	pairs = generatePairs()
		# |	for _ in league.numGames:
		# |	|	schedule = schedule_game()
		# |	|	if !schedule:
		# |	|	|	return 2
		# |	|	games.append(new Game())
		# '''




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