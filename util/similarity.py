from util.syn_retriever import SynDB
import numpy as np
import itertools

class Similarity:
	db = None
	
	def __init__(self, db_file = "./synonyms.db"):
		try:
			self.db = SynDB(db_file)
		except Exception as e:
			print(f"ERROR! Could not open the database.{e}")
			self.close()
			
	def close(self):
		self.db.disconnect()
		
	# Return a tuple with the index of the maximum element in a multidimensional array, and a tuple with the number of
	# common synonyms and the total number of synonyms
	def max2d(self, lst_tuples):
		try:
			if len(lst_tuples) > 0:
				divided = np.array(
					[[1 / 2 * (tup[0] / tup[1] + tup[0] / tup[2]) if tup[1] != 0 and tup[2] != 0 else 0 for tup in lst]
					 for lst in lst_tuples])
					 
				maxid = np.unravel_index(divided.argmax(), divided.shape)
					
				return ((maxid[0], maxid[1]), lst_tuples[maxid[0]][maxid[1]])
			else:
				return None
		except:
			return None

	# Function to count the number of common elements in two lists
	def count_overlaps(self, l1, l2):
		return len(set(l1) & set(l2))
	
	
	# Function to compute similarity between two words, based on the percentage of common synonyms
	def sim(self, w1, w2):
		try:
			syns1, syns2 = self.db.get(w1), self.db.get(w2)
			
			syns1 = [s + [w1] for s in syns1]
			syns2 = [s + [w2] for s in syns2]
			
			return [[(self.count_overlaps(syn1, syn2), len(syn1), len(syn2))
					 for syn2 in syns2] for syn1 in syns1]
					 
		except Exception as e:
			print(e)
			return None
	
	# Get lvl1 similarity of words
	def sim_lvl1(self, w1, w2):
		sims = self.sim(w1, w2)
		dists = np.array([[(r[0] / r[1] + r[0] / r[2])/2 if r[1] != 0 and r[2] != 0 else 0 for r in row] for row in sims])
		
		try:
			max_index = np.unravel_index(dists.argmax(), dists.shape)
		except Exception:
			return None
						
		return max_index, np.max(dists)
		
		
	# Helper function to flatten 2d list
	def flat(self, lst):
		return [x for l in lst for x in l]
	
	
	# Level 2 similarity of words
	def sim_lvl2(self, w1, w2):
		# Get all synonyms for all meanings
		syns1, syns2 = self.db.get(w1), self.db.get(w2)
		
		# Do we want to have the word itself in the list? NO
		#syns1 = [s + [w1] for s in syns1]
		#syns2 = [s + [w2] for s in syns2]
		
		############
		# Find meaning with highest lvl1 similarity -- Careful, not the optimal solution (but quicker)!! => Should change this? It would become very slow then...
		ids = self.sim_lvl1(w1, w2)
		
		if ids == None:
			return None
		else:
			ids = ids[0]
		
		syns1 = [syns1[ids[0]]]
		syns2 = [syns2[ids[1]]]
		#############
						
		comb = itertools.product(syns1, syns2)
		
		temp = []
		for c in comb:
			tmp = []
			for wi in c[1]:
				t = []
				for wj in c[0]:
					s = self.sim(wi, wj)
					if s != None and len(s) > 0 :
						if len(s[0]) > 0:
							t.append(self.max2d(s)[1])
				if t != None and len(t) > 0:
					if len(t[0]) > 0:
						tmp.append(self.max2d([t])[1])
			temp.append(np.sum(tmp, axis=0))
		try:
			if temp != None and len(temp) > 0:
				if temp[0].size > 0:
					res_lvl2 = self.max2d([temp])[1]
				
					#return (res_lvl2[0])/(res_lvl2[1] + res_lvl2[2])*2
					return (res_lvl2[0] / res_lvl2[1] + res_lvl2[0] / res_lvl2[2])/2
				else:
					return None
			else:
				return None	
		except:
			return None		