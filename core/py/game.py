class Game:
	def __init__(self, team1_id, team2_id, week, day, season, start, end, venue_id):
		self.team1_id = team1_id
		self.team2_id = team2_id
		self.week = week
		self.day = day
		self.season = season
		self.start = start
		self.end = end
		self.venue_id = venue_id
		
	def dump(self):
		print(f"Team {self.team1_id} vs. Team {self.team2_id} ({self.start}-{self.end}) {self.week} {self.day}")