import os
import sys
import copy
import time
import pickle
import random
from threading import Thread, Lock
from multiprocessing import Queue

# Class to generate text reponse based on a Markov chain
class DonaldBot():
	
	# Initialize the bot
	def __init__(self):
		
		# Empty dictionary for the data
		self.data = {u'default':{}}

	# Clear internal data
	def clear_data(self, database=None):
		
		# Overwrite data
		if database == None:
			self.data = {'default':{}}
		else:
			try:
				self.data.pop(database)
			except KeyError:
				self._error(u'clear_data', u"Database: '%s' was not found" % (database))

	"""
	Generate random text based on database and user input
	
	Arguments
		maxlength - maximum number of words returned by the method
		seedword  - indicates what word(s) should be in the returned string
		database  - indicates the database the text should be generated from
		verbose   - boolean for increased logging
		maxtries  - indicates how many times the method can try to produce a sentence
 	"""
	def generate_text(self, maxlength, seedword=None, database=u'default',
		verbose=False, maxtries=100):
		
		# No data exception
		if self.data[database] == {}:
			self._error(u'generate_text', u"No data is available yet in database '%s'." % (database))
		
		error = True
		attempts = 0
		
		if seedword == "I":
			specialWord = "I"

		# Change single keyword into list
		if type(seedword) in [str,unicode]:
			seedword = [seedword]

		# Loop until a sentence is produced
		while error:
			try:
				# Get word pairs from the database, shuffle so they are not always repeated
				keys = self.data[database].keys() 
				random.shuffle(keys)
				
				# Random seed if specified is not found or none 
				seed = random.randint(0, len(keys))
				w1, w2 = keys[seed]
				
				# Find word pair containing seed word
				if seedword != None:
					# Loop through the seed words
					while len(seedword) > 0:
						for i in xrange(len(keys)):
							
							# If 1 seedword check if it is part of a word pair
							# If > 1 seedword check that they match key
							if seedword[0] in keys[i] or \
								(tuple(seedword[0].split(u' ')) == \
								keys[i]):
								# Choose the words
								w1, w2 = keys[i]
								# Get rid of the seedwords
								seedword = []
								break
						# Get rid of the first keyword, if it was not
						# found in the word duos
						if len(seedword) > 0:
							seedword.pop(0)
				# Empty list to contain the generated words
                                words = []
				
				# Loop to get as many words as requested
				for i in xrange(maxlength):
					# Add the current first word
					words.append(w1)
					# Generare a new first and second word. Each key is a tuple (w1, w2), a random word from this list is selected
					w1, w2 = w2, random.choice(self.data[database][(w1, w2)])
				
				# Add the final word 
				words.append(w2)
				
				# Capitalise first word, single 'i's, and letters after a full stop
				for i in xrange(0, len(words)):
					if (i == 0) or (u'.' in words[i-1]) or \
						(words[i] == u'i'):
						words[i] = words[i].capitalize()
				
				# Loop through word last-to-first to find last word that contains relevant punctuation.
				ei = 0
				for i in xrange(len(words)-1, 0, -1):
					# If current word has proper punctuation, use the as the last word. 
					# Otherwise change to full stop
					if words[i][-1] in [u'.', u'!', u'?']:
						ei = i+1
					elif words[i][-1] in [u',', u';', u':']:
						ei = i+1
						words[i][-1] = u'.'
					# Break if word with punctuation found.
					if ei > 0:
						break
				# Strip back to the last word with proper punctuation.
				words = words[:ei]

				# Combine word into sentence
				sentence = u' '.join(words)

				if sentence != u'':
					error = False
				
			except:
				# Increase failed attempts
				attempts += 1
				if verbose:
					self._message(u'generate_text', u"Error generating text, will make %d more attempts" % (maxtries-attempts))
				# If max attempts were made, raise an error and stop
				if attempts >= maxtries:
					self._error(u'generate_text', u"Made %d attempts to generate text, all failed. " % (attempts))
		
		return sentence
	
	# Store database as a pickle file	
	def pickle_data(self, filename):
	
		with open(filename, u'wb') as f:
			pickle.dump(self.data, f)
	
	"""	
	Reads in text, this function only accepts text files	

	Arguments
                filename  - String path to a .txt file to be read by the bot
                database  - String name of the database you want to add the file's data to, or u'default' to add to the
                overwrite - Boolean indicates whether the existing data should be overwritten, default is False.
        """
	def read(self, filename, database=u'default', overwrite=False):
			
		# Clear the current data if required
		if overwrite:
			self.clear_data(database=database)
		
		# Check whether the file exists
		if not self._check_file(filename):
			self._error(u'read', u"File does not exist: '%s'" % (filename))
		
		# Read the words from the file as one string
		with open(filename, u'r') as f:
			contents = f.read()

		# Get contents in unicode
		contents = contents.decode(u'utf-8')
		
		# Split words into a list
		words = contents.split()
		
		# Create new database if required.
		if not database in self.data.keys():
			self._message(u'read', \
			u"Creating new database '%s'" % (database))
			self.data[database] = {}
		
		# Add the words and their likely following word to the database
		for w1, w2, w3 in self._triples(words):
			# Only use actual words and words with minimal punctuation
			if self._isalphapunct(w1) and self._isalphapunct(w2) and \
				self._isalphapunct(w3):
				# The key is a pair of words
				key = (w1, w2)
				# Check if the key is already part of the database dict
				if key in self.data[database]:
					# If the key is already in the database dict add the third word to the list
					self.data[database][key].append(w3)
				else:
					# If the key is not in the database dict yet, first make a new list for it, and then add the new word
					self.data[database][key] = [w3]
	
	"""
	Read database from pickle file
	
	Arguments
                filename  - String path to a .txt file to be read by the bot
                database  - String name of the database you want to add the file's data to, or u'default' to add to the
                overwrite - Boolean indicates whether the existing data should be overwritten, default is False.
	"""
	def read_pickle_data(self, filename, overwrite=False):
		
		# Check whether the file exists
		if not self._check_file(filename, allowedext=[u'.pickle', u'.dat']):
			self._error(u'read_pickle_data', \
				u"File does not exist: '%s'" % (filename))
		
		# Load a database from a pickle file
		with open(filename, u'rb') as f:
			data = pickle.load(f)
		
		# Store the data internally
		if overwrite:
			self.clear_data(database=None)
			self.data = copy.deepcopy(data)
		else:
			for database in data.keys():
				for key in data[database].keys():
					# If the key is not in the existing dataset yet, add it then copy the loaded data into the existing data
					if key not in self.data[database].keys():
						self.data[database][key] = copy.deepcopy(data[database][key])
					# If the key is already in the existing data, add the loaded data to the existing list
					else:
						self.data[database][key].extend(copy.deepcopy(data[database][key]))
		
		# Get rid of the loaded data
		del data
									
	""" 
	Checks if file exists and has required extension

	Arguments
	filename    - String path to desired file
	allowedtext - list of allowed extensions or none for all
	"""
	def _check_file(self, filename, allowedext=None):
		
		# Check whether the file exists
		ok = os.path.isfile(filename)
		
		# Check whether the extension is allowed
		if allowedext != None:
			name, ext = os.path.splitext(filename)
			if ext not in allowedext:
				ok = False
		
		return ok
	
	"""
	Raise error with involved method
	
	Arguments
	methodname - String name of method
	message - String error message
	"""	
	def _error(self, methodname, msg):
				
		raise Exception(u"ERROR in Markovbot.%s: %s" % (methodname, msg))

	"""
	Boolean to check if string characters are alpha, puntuation and > 1 character long

	Arguments
	string - String to be checked
	"""
	def _isalphapunct(self, string):
			
		if string.replace(u'.',u'').replace(u',',u'').replace(u';',u''). \
			replace(u':',u'').replace(u'!',u'').replace(u'?',u''). \
			replace(u"'",u'').isalpha():
			return True
		else:
			return False
	
	"""
	Print message including name of method involved
	"""	
	def _message(self, methodname, msg):
	
		print(u"MSG from Markovbot.%s: %s" % (methodname, msg))
        
	"""
	Grenerates a triplet from a word list

	Arguments
	words - list of strings
	"""
	def _triples(self, words):
		
		# Check if if there are at least three words left
		if len(words) < 3:
			return
		
		for i in range(len(words) - 2):
			yield (words[i], words[i+1], words[i+2])
		
