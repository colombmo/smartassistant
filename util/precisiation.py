from util.similarity import Similarity
from util.syn_retriever import SynDB
import numpy as np
import math
import json

class Precisiation:

	similarity = None
	wordsdb = None
	maxes = None
	mins = None
	syndb = None
	
	def __init__(self, db_file = "./synonyms.db"):
		try:
			self.similarity = Similarity(db_file)
			
			## Load max and min (basis) for each adjective categories
			with open("./util/adjective_types.json", "r") as read_file:
				self.wordsdb = json.load(read_file)
			self.maxes = {key: val[0] for key, val in self.wordsdb.items()}
			self.mins = {key: val[1] for key, val in self.wordsdb.items()}
			self.syndb = SynDB(db_file)
		except Exception as e:
			print(f"ERROR! Could not load the similarity class. {e}")
			self.close()
			
	def close(self):
		self.similarity.close()
		self.syndb.disconnect()
		
	# Precisiate the meaning of a the word w, knowing the category to which it belongs
	def precisiate(self, word, category, lvl=2):
		# Put at maximum or minimum if maximum or minimum of category
		if self.maxes[category] == word:
			return 1.0
		elif self.mins[category] == word:
			return 0
		
		prec = self.syndb.get_precisiation(word, category, lvl) # Try to get from db
		if prec != None:
			return prec
		else:
			#print(f"Not found: {word}")
			if lvl == 1:
				maxsim = self.similarity.sim_lvl1(word, self.maxes[category])
				minsim = self.similarity.sim_lvl1(word, self.mins[category])
				
				if maxsim == None or minsim == None:
					res = -1
					self.syndb.set_precisiation(word, category, lvl, res) # Save to db
					return res
				elif minsim[1] + maxsim[1] == 0:
					res = 0.5
					self.syndb.set_precisiation(word, category, lvl, res) # Save to db
					return res
				else:
					res = (maxsim[1]*1+minsim[1]*0)/(maxsim[1] + minsim[1])
					self.syndb.set_precisiation(word, category, lvl, res) # Save to db
					return res
			else:
				maxsim = self.similarity.sim_lvl2(word, self.maxes[category])
				minsim = self.similarity.sim_lvl2(word, self.mins[category])
				
				if maxsim == None or minsim == None:
					res = -1
					self.syndb.set_precisiation(word, category, lvl, res) # Save to db
					return res
				elif minsim + maxsim == 0:
					res = 0.5
					self.syndb.set_precisiation(word, category, lvl, res) # Save to db
					return res
				else:
					res = (maxsim*1+minsim*0)/(maxsim + minsim)
					self.syndb.set_precisiation(word, category, lvl, res) # Save to db
					return res
			
	# Get most probable category of adjectives - Improved to exploit the fact that several adjectives should belong to the same category
	def get_category(self, adjectives_list):
		for k,v in self.wordsdb.items():
			if all([w in v for w in adjectives_list]):
				return k
		# Using lvl1 synonyms if words are not in the list
		syns = self.flatten([s for w in adjectives_list for s in self.syndb.get(w)])
		overlaps = {k: self.similarity.count_overlaps(syns,v) for (k, v) in self.wordsdb.items()}
		
		return max(overlaps, key=overlaps.get)
	
	
	def precisiate_v2_partial(self, word, category, lvl=2):
		
		# Using all synonyms !! What happens if we take only the best meaning? -> No way to know which is best?! :S
		if lvl == 1:
			t = []
			for w in self.flatten(self.syndb.get(word)):
				p = self.precisiate(w, category, lvl=1)
				if p != None and p != -1:
					t.append(p)
		else:
			t = []
			for w in self.flatten(self.syndb.get(word)):
				p = self.precisiate(w, category, lvl=2)
				if p != None and p != -1:
					t.append(p)
					
		# Clean and mirror the data
		if self.maxes[category] == word or self.mins[category] == word:
			if self.maxes[category] == word:
				m = 1
			elif self.mins[category] == word:
				m = 0
			syn_prec = self.remove_and_mirror(t, m, ratio=0.5)
		else:
			m = np.median(t)	
			#syn_prec = self.remove_outliers(t, m, ratio=0.5)
			#m = np.mean(syn_prec)
			syn_prec = self.remove_and_mirror(t, m, ratio=0.99)
		
		return syn_prec
	
	def precisiate_v2(self, word, category, lvl=2):
		t = self.precisiate_v2_partial(word, category, lvl)
		
		return np.mean(t), np.std(t)
	
	'''
	#
	# Helpers
	#
	'''
	# Flatten a 2d list
	def flatten(self, list2d):
		return list(set([el for sublist in list2d for el in sublist]))
		
	def remove_outliers(self, lst, m, ratio=1):
		dists = np.abs(np.array(lst)-m)
		ds = [(d, lst[i]) for i,d in enumerate(dists)]
		s = sorted(ds, key = lambda x: x[0])
		top = s[0:math.floor(ratio*len(s))]
		res = [t[1] for t in top]
		
		return res

	def remove_and_mirror(self, lst, m, ratio=1):
		lst = self.remove_outliers(lst, m, ratio)
		res = []
		for l in lst:
			res.append(m+np.abs(l-m))
			res.append(m-np.abs(l-m))
		return res