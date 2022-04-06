import sqlite3
from thesaurus import Word
import traceback

class SynDB:
	conn = None
	cur = None
	rel = [1,2,3]

	def __init__(self, db_file = "./synonyms.db"):
		try:
			self.conn = sqlite3.connect(db_file)
			self.cur = self.conn.cursor()
		
			# Create tables if they do not exist yet
			# List of all words
			self.cur.execute("""CREATE TABLE IF NOT EXISTS words (
								id integer PRIMARY KEY AUTOINCREMENT,
								name text NOT NULL UNIQUE
							);""")
			
			# List of all synonyms
			self.cur.execute("""CREATE TABLE IF NOT EXISTS synonyms (
								origin integer NOT NULL,
								target integer NOT NULL,
								meaning integer NOT NULL,
								FOREIGN KEY (origin) REFERENCES words(id),
								FOREIGN KEY (target) REFERENCES words(id)
							);""")
							
			# List of pre-precisiated value of words for category, and specifying if using lvl1 or lvl2 similarity
			self.cur.execute("""CREATE TABLE IF NOT EXISTS precisiations (
								word integer NOT NULL,
								category text NOT NULL,
								similarity_level integer NOT NULL,
								value float NOT NULL,
								FOREIGN KEY (word) REFERENCES words(id)
							);""")
			
			# Index name TEST
			self.cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS name_idx 
								ON words(name)
							;""")
			
			# Index origin TEST
			self.cur.execute("""CREATE INDEX IF NOT EXISTS origin_idx 
								ON synonyms(origin)
							;""")
							
			# Ensure unique triplet origin, target, meaning
			self.cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS unique_origin_target 
								ON synonyms(origin, target, meaning)
							;""")
			
			# Index word TEST
			self.cur.execute("""CREATE INDEX IF NOT EXISTS word_idx 
								ON precisiations(word)
							;""")
			
			
			if db_file == "./synonyms_rel1.db":
				self.rel = [1]
			
		except Exception as e:
			print(f"ERROR! Could not create the database connection.{e}")
			self.disconnect()
	
	
	def disconnect(self):
		self.conn.close()
	
	
	def get(self, word = ""):
		synonyms = self.__get_from_db(word)
		if len(synonyms) == 0:
			synonyms = self.__get_from_thesaurus(word)
			if len(synonyms) != 0:
				self.set(word, synonyms)
			else:
				# Add synonyms as NO_SYNONYMS to tell words which have no synonyms or were not found in thesaurus from those who were never searched
				self.set(word, [["NO_SYNONYMS"]])
		elif synonyms[0][0] == "NO_SYNONYMS":
			return []
				
		return synonyms
		
		
	def __get_from_thesaurus(self, word= ""):
		syns = []
		try:
			syns = Word(word).synonyms("all", relevance = self.rel)
		except Exception as e:
			#print(f"ERROR! Could not retrieve synonyms from thesaurus. Word: {word} {e}")
			return []
		return syns
	
	
	def __get_from_db(self, word = ""): 
		try:
			temp = []
			for row in self.cur.execute("""
				SELECT name, meaning FROM synonyms 
				INNER JOIN words ON synonyms.target = words.id
				WHERE origin = (SELECT id FROM words WHERE name = ? LIMIT 1)
				""", (word,)):
				
				temp.append((row[0], row[1]))
			
			# Keep info about the meaning	
			if len(temp) > 0:	
				size = max(temp, key = lambda k:k[1])[1]
				res = [[] for i in range(size+1)]
				
				for i,t in enumerate(temp):
					res[t[1]].append(t[0])
					
				return res
					
		except Exception as e:
			print(f"ERROR! Could not retrieve synonyms from DB. {e}")
			
		return []
		
			
	def set(self, word = "", synonyms = []):
		try:
			self.cur.execute("INSERT OR IGNORE INTO words(name) VALUES (?);", (word,))
			
			for meaning, syns in enumerate(synonyms):
				# Create right structure to feed to executemany:
				temp_words = [(s,) for s in syns]
				temp_syns = [(word, s, meaning) for s in syns]
				self.cur.executemany("INSERT OR IGNORE INTO words(name) VALUES (?);", temp_words);
				#self.conn.commit()
				self.cur.executemany("""
					INSERT OR IGNORE INTO synonyms (origin, target, meaning)
					VALUES ((SELECT id from words where name=? LIMIT 1), (SELECT id from words where name=? LIMIT 1), ?);
					""", temp_syns)
					
			self.conn.commit()
			
		except Exception as e:
			print(f"ERROR! Could not insert new values in table. {e}")
			
	def get_precisiation(self, word = "", category = "", lvl = 1):
		try:
			for row in self.cur.execute("""
				SELECT value FROM precisiations
				WHERE word = (SELECT id FROM words WHERE name = ?)
				AND category = ?
				AND similarity_level = ?
				LIMIT 1
				;""", (word, category, lvl)):
				
				return row[0]
					
			return None

		except Exception as e:
			print(f"ERROR! Could not get value from table. {e}")
	
	def set_precisiation(self, word = "", category = "", lvl = 1, value = 0.5):
		try:
			self.cur.execute("INSERT OR IGNORE INTO words(name) VALUES (?);", (word,))
			self.cur.execute("INSERT INTO precisiations(word, category, similarity_level, value) VALUES ((SELECT id from words where name=? LIMIT 1), ?, ?, ?);", (word, category, lvl, value))
					
			self.conn.commit()
			
		except Exception as e:
			print(f"ERROR! Could not insert new values in table. {e}")