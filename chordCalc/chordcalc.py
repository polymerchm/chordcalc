#!/usr/bin/python

"""
Chord Calculator
Version 0.3
Copyright (c) 28 Dec 2008, Gek S. Low

Modified to operate under Pythonista iOS ui environment
Copyright (c) August 19th, 2014 Steven K. Pollack
Version 2.01
January 13, 2015


Free for personal use. All other rights reserved.


USE AT YOUR OWN RISK!
This software is provided AS IS and does not make any claim that it actually works,
  or that it will not cause your computer to self-destruct or eat up your homework.

Note that some calculated chords may be playable only by aliens with 10 tentacles.
Please use your common sense. The author will not be responsible for any injuries
from attempts at impossible fingerings.

The author reserves the right to change the behavior of this software without prior notice.

View objects:
-------------
tableview_roots  	  - root tone of chord
tableview_type      - chord type
tableview_inst_tune - instrument/tuning selector
tableview_filters   - filters selection
tableview_find      - display and interogate found chords
tableview_scale			- display vaious scales
view_fretEnter			- custon view for fret number entry
view_neck           - drawing of neck/fingering
button_up           - previous chord shape/position
button_down         - next chord shape/position
button_arp          - play arpeggio
button_chord        - play chord
button_tuning       - play the open strings
button_cc_modew   	- change mode (show fingering for a chord, or calculate chords from a fingering
                                       of display scales)
button_find         - display ther calculated fingering
slider_volume				- set play volume
slider_arp					- set arpegio and scale playback speed
lbl_fullchord				- displays the notes in the display chord (full chord, no filters)
lbl_definition			- displays the scale tones in a the full chord
										- display relative major of greek mode
btn_sharpFlat				- forces shaprs for flats for non-standard keys (not in the circle of fifths)
sp_span							- spinner for changing the span and recalculating chords based on span
button_save					- bring up a menu to save the current state of the filters, capos and instrument
button_load					- bring up a menu to load a saved state
button_config				- save current configuration
button_new					- brings up the instrument builder
"""

import sys, os.path, re, ui, console, sound, time, math, json, dialogs
from PIL import Image
from copy import deepcopy
import chordcalc_constants as cccInit
from debugStream import debugStream
from Spinner import Spinner
from Shield import Shield




def rotate(list,index):
	''' take the input list and rotate it by indicated number of positions
			positive index move items form left side of list to right
			so list[0] become list[-1]
			negative is vice versa'''
			
	return list[index % len(list):] + list[:index % len(list)]	if index else list
			

	
def instrument_type(): # return the type of instrument based on current selected 
	text = currentState['instrument']['title']
	for type in 'guitar mando ukulele banjo'.split():
		if re.match("^{}".format(type),text,flags=re.I):
			return type
	return 'generic'
			
def uniqify(sequence, idfun=None):
	''' return a unique, order preserved version in input list'''
	if not idfun:
		def idfun(x): return x
	seen = {}
	result = []
	for item in sequence:
		marker = idfun(item)
		if marker in seen.keys(): 
			continue
		seen[marker] = 1
		result.append(item)
	return result
	
def fingeringToString(list):
	''' turn fingering to a text string for hashing'''
	hashcodes = 'abcdefghijklmnopqrstuvwxyz-'
	return ''.join([hashcodes[item] for item in list])
	
	
	
def calc_fingerings():
	'''calculate the fingerings and fretboard positions for the desired chord'''
	global currentState 
	try:
		key = currentState['root']['noteValue']
		note = currentState['root']['title']  # since "C" has a note value of zero, use note title as indicator
		chordtype = currentState['chord']['fingering']	
		tuning = currentState['instrument']['notes']
		instrument = currentState['instrument']
		filters = currentState['filters']
		span = currentState['instrument']['span']
	except:
		return
		
	if note and chordtype and tuning:
		fingerPositions = []	
		fingerings = []
		result = []
		console.show_activity()
		for position in range(0,fretboard.numFrets-span):
			fingeringThisPosition = findFingerings(key, chordtype, tuning, position, span)
			if fingeringThisPosition:
				fingerings = fingerings + fingeringThisPosition
		fingerings = uniqify(fingerings,idfun=(lambda x: tuple(x)))
		if fingerings:
			for fingering in fingerings:
				fingerMarker = fretboard.fingeringDrawPositions(key,chordtype,tuning,fingering)
				fingerPositions.append(fingerMarker)
			for fingering,drawposition in zip(fingerings,fingerPositions):
				chordTones = []
				for entry in drawposition:
					chordTones.append(entry[2])
				result.append((drawposition,chordTones,fingering))
			if filters:
				result = apply_filters(filters, result)
				if result:
					result = uniqify(result,idfun=(lambda x: tuple(x[2])))
		console.hide_activity()
	return result
			
def calc_two_octave_scale(startingStringFret,mode='normal'):
	''' given a starting (string,scaletoneIndex) calculate a two octave scale across the strings
	    returns a 2D tupple of strings and frets
	    modes: 
	    			normal 				: referenceFret is the starting fret
	          down   				: referenceFret continually updated
	          open   				: favor open strings
	          FourOnString 	: favor 4 notes per string (max)'''
	          
	global currentState
	try:
		key = currentState['root']['noteValue']
		scaleintervals = currentState['scale']['scaleintervals']
		tuning = currentState['instrument']['notes']
		instrument = currentState['instrument']
		fretboard = currentState['fretboard']
	except:
		return None
		
	intervals = [0]
	for letter in scaleintervals:
		if letter == 'S':
			intervals.append(1)
		elif letter == 'T':
			intervals.append(2)
		else:
			intervals.append((int(letter)))
			
	nextNote = key
	notesInScale = [nextNote]
	for interval in intervals[1:]:
		nextNote += interval
		notesInScale.append(nextNote % 12)
		
	scale_notes = fretboard.scale_notes
	fretsOnStrings = [] 
	tonesOnStrings = []
	
	for i,string in enumerate(scale_notes):
		frets = [x[0] for x in string]
		fretsOnStrings.append(frets)
		tones = [x[0] + tuning[i] for x in string]
		tonesOnStrings.append(tones)
	
	tonesOnStrings.append([-1 for x in range(len(tonesOnStrings[0]))])
	
	numNotes = 2*len(scaleintervals) + 1
	numStrings = len(tuning)
	thisString,thisStringFret = startingStringFret
	
	tone = thisStringFret + tuning[thisString]
	tonesInTwoOctaveScale = [tone]
	for octave in [1,2]:
		for interval in intervals[1:]:
			tone += interval
			tonesInTwoOctaveScale.append(tone)
	referenceFret = thisStringFret # used to anchor the scale
	thisIndex = fretsOnStrings[thisString].index(thisStringFret)
	scaleNotes = [startingStringFret]
	thisStringCount = 1
	nextStringNote = scale_notes[thisString+1][1]
	nextIndex = 0
	# always look to see if next note is on next string
	for nextTone in tonesInTwoOctaveScale[1:]: # first tone already in place		
		try:
			thisIndex = tonesOnStrings[thisString][thisIndex:].index(nextTone) + thisIndex
			onThisString = True
		except ValueError:
			onThisString = False 
		try: 
			nextIndex = tonesOnStrings[thisString+1][nextIndex:].index(nextTone) + nextIndex
			onNextString = True
		except ValueError:
			nextIndex = 0
			onNextString = False

		if not onThisString: #not on this string
			if not onNextString: # nor here, must be done.
				return scaleNotes
			else: # not on current string, is on next string, save and update
				scaleNotes.append((thisString+1,fretsOnStrings[thisString+1][nextIndex]))
				if mode == 'down':
					referenceFret = fretsOnStrings[thisString+1][nextIndex]
				thisString += 1
				if thisString == numStrings + 1: # on phantom string
					return scaleNotes
				thisIndex = nextIndex
				nextIndex = 0
				thisStringCount = 1
		else:
			if onNextString: # On both strings
				thisFret = fretsOnStrings[thisString][thisIndex]
				nextFret = fretsOnStrings[thisString+1][nextIndex]
				thisDelta = abs(referenceFret - thisFret)
				nextDelta = abs(referenceFret - nextFret)
				if mode == 'open':
					if nextFret == 0:
						scaleNotes.append((thisString+1,0))
						thisString += 1
						thisIndex = nextIndex
						continue # next tone
				if thisDelta < nextDelta: # stay in this string
					if mode == 'FourOnString' and thisStringCount == 4:
						thisString += 1
						scaleNotes.append((thisString,nextFret))
						thisIndex = nextIndex
						thisStringCount = 1
						continue
					scaleNotes.append((thisString,thisFret))
					if mode == 'down':
						referenceFret = thisFret
				else:
					thisString += 1
					scaleNotes.append((thisString,nextFret))
					if mode == 'down':
						referenceFret = nextFret
					thisIndex = nextIndex
					nextIndex = 0
					thisStringCount = 1
			else: #just on first string
				scaleNotes.append((thisString,fretsOnStrings[thisString][thisIndex]))
				thisStringCount += 1
				if mode == 'down':
					referenceFret = fretsOnStrings[thisString][thisIndex]
				
	return scaleNotes	
			
					
					
				
#	
#	
#	for string in range(thisString,numStrings): # look at next string always
#		for thisI in range(thisIndex+1,len(fretsOnStrings[0])):
#			thisStringNote = notesOnStrings[string][thisI]
#			if string == numStrings - 1: # rightmost string, so force to never check
#				nextStringNote = 100 # current tone always "smaller"
#			else:
#				nextStringNote =  notesOnStrings[string+1][0]
#			if nextStringNote != thisStringNote: # continue on this string
#				scaleNotes.append((string,fretsOnStrings[string][thisI]))
#				if len(scaleNotes) == numNotes:
#					return scaleNotes
#			else:
#				scaleNotes.append((string+1,fretsOnStrings[string+1][0]))
#				if len(scaleNotes) == numNotes: 
#					return scaleNotes
#				thisIndex = 0
#				nextIndex = 0
#				break
	return scaleNotes

def calc_chord_scale():
	global currentState
	try:
		key = currentState['root']['noteValue']
		chord = currentState['chord']['fingering']
		tuning = currentState['instrument']['notes']
		instrument = currentState['instrument']
		fretboard = currentState['fretboard']
	except:
		return []
					
	# calculate notes in the current key
	chordNotes = [(x+key) % 12 for x in chord]
	capoOffsets = capos.capoOffsets()
	scale = []
	for i,string in enumerate(tuning):
		thisString = []
		for fret in range(capoOffsets[i],fretboard.numFrets+1): # zero is the open string
			tone = (string + fret) %12
			if tone in chordNotes:
				thisString.append((fret-1,(tone-key)%12))
		scale.append(thisString)

	return scale
		
def calc_scale_notes():
	''' calculate the scale notes for the curent key, instrument and scale type'''
	global currentState
	try:
		key = currentState['root']['noteValue']
		scaleintervals = currentState['scale']['scaleintervals']
		tuning = currentState['instrument']['notes']
		instrument = currentState['instrument']
	except:
		return
	
	# format of the returned data is [[[fret, scalenote, scaletone, octave],.....numer on string
	#                                                                         ] length = numStrings
	# first unpack the scale spacing from the string
	capoOffsets = capos.capoOffsets()
	intervals = [0]
	for letter in scaleintervals:
		if letter == 'S':
			intervals.append(1)
		elif letter == 'T':
			intervals.append(2)
		else:
			intervals.append((int(letter)))
			
	nextNote = key
	notes = [nextNote]
	for interval in intervals[1:]:
		nextNote += interval
		notes.append(nextNote % 12)
		
	scaleNotes= []
	for i,string in enumerate(tuning):
		thisString = []  
		for fret in range(capoOffsets[i],fretboard.numFrets+1):
			note = (fret + string) % 12
			if note in notes:
				thisString.append((fret,note))
		scaleNotes.append(thisString)		
	return scaleNotes	
		
		
def apply_filters(filters,fingerings):
	''' for the current fingerings and filters, return only those chords that apply'''
	filter_constraint = {'FULL_CHORD':("R b3 3 #5 5".split(),3)}	
	instrumentType = instrument_type()
	if not filters:
		return fingerings
	filtered = []
	temp_fingerings = fingerings
	if 'FULL_CHORD' in filters:   # must have at least R,3 and 5 triad
		for fingering in temp_fingerings:	
			notes,numNotes = filter_constraint['FULL_CHORD']		
			if len(set(fingering[1]).intersection(notes)) == numNotes:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'NO_DEAD' in filters : #remove all with dead notes
		for fingering in temp_fingerings:
			if 'X' not in fingering[1]:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'NO_OPEN' in filters:
		for fingering in temp_fingerings:
			open_check = []
			for string in fingering[0]:
				open_check.append(string[3])
			if 'O' not in open_check:
				filtered.append(fingering)
		temp_fingerings = filtered 
		
	filtered = []
	if 'HIGH_4' in filters:
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i in [0,1]:
					if string[3] != 'X':
						validChord = False
						break
				else:
					if string[3] == 'X':
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'LOW_4' in filters:
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i in [4,5]:
					if string[3] != 'X':
						validChord = False
						break
				else:
					if string[3] == 'X':
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
								
	filtered = []
	if 'HIGH_3' in filters: #for mandolin, allow for root or 5th to be abandoned
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i == 0:
					if string[3] != 'X':
						if fingering[1][i] in ['R','#5', '5']:
							fingering[1][i] = 'X'
							fingering[0][i] = (fretboard.nutPosition[i][0],fretboard.nutPosition[i][1],'X','X')
							break
						validChord = False
						break
				else:
					if string[3] == 'X':
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
										
	filtered = []
	if 'LOW_3' in filters: 
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i == 3:
					if string[3] != 'X':
						if fingering[1][i] in ['R','#5','5'] :# for mandolin, allow for root or 5th to be abandoned
							fingering[1][i] = 'X'
							fingering[0][i] = (fretboard.nutPosition[i][0],fretboard.nutPosition[i][1],'X','X')
							break
						validChord = False
						break
				else:
					if string[3] == 'X': 
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'DOUBLE_STOPS' in filters and instrumentType == 'mando': # create adjacent string double stops for the chords
		numStrings = len(fingerings[0][1])
		for fingering in temp_fingerings:			
			for i,string in enumerate(fingering[1]):
				if i+1 == numStrings: 
					break
				else:
					nextString = fingering[1][i+1]
				if string == 'X' or nextString == 'X': continue
				if string != nextString: #rebuild the fingering as a double stop for this pair
					field1 = []
					field2 = []
					field3 = []
					j = 0
					while j < numStrings:
						if j < i or j > i+1:
							field1.append((fretboard.nutPosition[j][0],fretboard.nutPosition[j][1],'X','X'))
							field2.append('X')
							field3.append(-1)
							j += 1
						else:
							for index in [j,j+1]:
								field1.append(fingering[0][index])
								field2.append(fingering[1][index])
								field3.append(fingering[2][index])
							j += 2
					entry = (field1,field2,field3)
					filtered.append(entry)
		temp_fingerings = filtered				
							
	filtered = []
	if 'NO_WIDOW' in filters: #remove isolated dead string (but not first or last)
		numStrings = len(fingerings[0][1])
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[1]):
				if (i == 0 or i == numStrings-1) and string == 'X' : #outside strings
					continue
				if string == 'X':
					validChord = False
					break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered				
	unique =  uniqify(temp_fingerings,idfun=(lambda x: fingeringToString(x[2])))	
	return unique
	
	
def tuningLabel(notes):
	'''return the notes for the current tuning'''
	note_string = ''
	for note in notes:
		note_range,base_note = divmod(note,12)
		note_char = re.split('/', ccc['NOTE_NAMES'][base_note])[0]
		if not note_range:
			note_string += note_char
		elif note_range == 1:
			note_string += note_char.lower()
		elif note_range == 2:
			note_string += note_char.lower() + "'"
		note_string += ' '
	return note_string.strip()
	
def getScaleNotes(key, chordtype, tuning, fingering):
	'''Given a fingering, gets the scale note relative to the key'''

	scalenotes = []
	for i, v in enumerate(fingering):
		if v == -1:
			scalenotes.append('X')
		else:
			effTuning = tuning[i]
			if instrument.is5StringBanjo and i == 0: #neeed to correct for short string
				effTuning = tuning[i] - fretboard.fret5thStringBanjo		
			fingerednote = (effTuning + fingering[i]) % 12
			for chordrelnote in chordtype:
				chordnote = (key + chordrelnote) % 12
				if fingerednote == chordnote:
					scalenotes.append(SCALENOTES[chordrelnote])
	return scalenotes
	
	



# Finds the chord fingerings for a given tuning (number of strings implied)
# Pos is the "barre" position, span is how many frets to cover
# Returns a list of fingerings

def findFingerings(key, chordtype, tuning, pos, span):
	# Get valid frets on the strings
	validfrets = findValidFrets(key, chordtype, tuning, pos, span)

	# Find all candidates
	candidates = findCandidates(validfrets)


	# Filter out the invalid candidates
	candidates = filterCandidates(key, chordtype, tuning, candidates)

	# Filter out "impossible" fingerings?
	# To be implemented...

	# Perhaps also some sorting options?

	return candidates

# For a given list of starting frets and span, find the ones that are in the chord for that tuning
# Returns a list of valid frets for each string
# Open strings are included if valid

def findValidFrets(key, chordtype, tuning, pos, span):
	if not tuning:
		return None
	strings = []
	nutOffsets = currentState['capos'].capoOffsets()
	for i,string in enumerate(tuning):
		# offset 5 string banjo 
		if instrument.is5StringBanjo and i == 0:
			string -= fretboard.fret5thStringBanjo 
		frets = []
		if nutOffsets[i] <= pos:
			start = pos
			stop = pos+ span+1
		elif pos <= nutOffsets[i] <= pos+span+1:
			start = nutOffsets[i]
			stop = pos + span+1
		else: #behind the capo
			continue
		searchrange = range(start,stop)
		if pos != 0: # include open strings is not at pos 0
			searchrange = [nutOffsets[i]] + searchrange
		for fret in searchrange:
			for chordrelnote in chordtype:
				note = (string + fret) % 12
				chordnote = (key + chordrelnote) % 12
				if note == chordnote:
					frets.append(fret)
		strings.append(frets) 
	return strings



# Finds all candidate fingerings, given all valid frets
# Includes strings that should not be played
# Note that this is just a permutation function and is independent of keys, tunings or chords



def findCandidates(validfrets):
	# Set up the counter which will track the permutations
	max_counter = []
	counter = []
	candidatefrets = []
	if not validfrets:
		return None
	for string in validfrets:
		# Include the possibility of not playing the string
		# Current approach prioritises open and fretted strings over unplayed strings
		candidatefrets.append(string + [-1])
		max_counter.append(len(string))
		counter.append(0)
	l = len(counter)-1

	# Number of possible permutations
	numperm = 1
	for c in max_counter:
		numperm *= c+1

	candidates = []
	# Permute
	for perm in range(numperm):
		# get the candidate
		candidate = []
		for string, fret in enumerate(counter):

			candidate.append(candidatefrets[string][fret])

		# increment counter, starting from highest index string
		for i, v in enumerate(counter):
			if counter[l-i] < max_counter[l-i]:
				counter[l-i] += 1
				break
			else:
				counter[l-i] = 0
	
		candidates += [candidate]
	return candidates



# Tests whether a fingering is valid
# Should allow various possibilities - full chord, no 5th, no 3rd, no root, etc

def isValidChord(key, chordtype, tuning, candidate):
	filters = currentState['filters']
	if not filters:
		filters = []
		
	result = True

	# which chord notes are present?
	present = {}
	for chordrelnote in chordtype:
		# assume chord notes are not present
		present[chordrelnote] = False
		chordnote = (key + chordrelnote) %12
		for i, v in enumerate(candidate):
			# ignore unplayed strings
			if candidate[i] != -1:
				note = (tuning[i] + candidate[i]) % 12
				if chordnote == note:
					present[chordrelnote] = True
					break


	# do we accept this fingering? depends on the option
	for note in present.keys():
		if present[note] == False:
			if 'FULL_CHORD' in filters:
				result = False
				break
			if 'NO3RD_OK' in filters:
				if note == 4 or note == 3:
					continue
			if 'NO5TH_OK' in filters:
				if note == 7:
					continue
			if 'NOROOT_OK' in filters:
				if note == 0:
					continue
		result = result & present[note]
	return result


# Tests if a given note is in the chord
# Not used here

def isInChord(key, chordtype, note):
	for chordrelnote in chordtype:
		chordnote = (key + chordrelnote) % 12
		if note == chordnote:
			return True
	return False

# Filter out the invalid chords from the list of candidates
# Criteria for invalid chords may vary
# Returns the list of valid chords

def filterCandidates(key, chordtype, tuning, candidates):
	if not candidates:
		return None
	newlist = []
	for candidate in candidates:
		if isValidChord(key, chordtype, tuning, candidate):
			newlist += [candidate]
	return newlist

# Given a fingering, gets the scale note relative to the key
def getScaleNotes(key, chordtype, tuning, fingering):
	scalenotes = []
	for i, v in enumerate(fingering):
		if v == -1:
			scalenotes.append('X')
		else:
			effTuning = tuning[i]
			if instrument.is5StringBanjo and i == 0:
				effTuning = tuning[i] - fretboard.fret5thStringBanjo
				
			fingerednote = (tuning[i] + fingering[i]) % 12
			for chordrelnote in chordtype:
				chordnote = (key + chordrelnote) % 12
				if fingerednote == chordnote:
					scalenotes.append(ccc['SCALENOTES'][chordrelnote])
	return scalenotes
	
def setChordSpelling():
	''' calculate and display the current Chord Spelling'''
	global currentState
	
	try:
		chordTones = currentState['chord']['fingering']
		key = currentState['root']['noteValue']
		keyName = currentState['root']['title']
	except:
		return
	outString = ''
	defString = ''
	for tone in chordTones:
		outChar = ccc['NOTE_NAMES'][(tone + key) % 12].split('/')
		if len(outChar) == 1:
			outChecked = outChar[0]
		else:
			try:
				sf = CIRCLE_OF_FIFTHS[keyName]
			except:
				sf = 1
			if sf > 0:
				outChecked = outChar[0]
			else:
				outChecked = outChar[1]
		outString += outChecked + ' '
		defString += ccc['SCALENOTES'][tone] + ' '
	mainView['lbl_fullchord'].hidden = False
	mainView['lbl_fullchord'].text = outString.strip()
	mainView['lbl_definition'].hidden = False
	mainView['lbl_definition'].text = defString.strip()

def relativeMajorDisplay():
	''' display the relative major for a greek mode'''
	global currentState
	try:
		key = currentState['root']['noteValue']
		scale = currentState['scale']['title']
	except:
		return
	
	if scale in ccc['TRUE_ROOT'].keys():
		text = "relative to {}".format(ccc['NOTE_NAMES'][(key-ccc['TRUE_ROOT'][scale])%12])
		mainView['lbl_definition'].text = text		
		mainView['lbl_definition'].hidden = False
	else:
		mainView['lbl_definition'].hidden = True

	
	
	
# Fretboard Class

class Fretboard(ui.View): # display fingerboard and fingering of current chord/inversion/file
#note that this is instanciated by the load process.  
	global currentState,middle_label
	def did_load(self):
		self.fbWidth = int(self.bounds[2])
		self.fbHeight = int(self.bounds[3])
		self.nutOffset = 20	
		self.numFrets = 14
		self.offsetFactor = 0.1		
		self.scale = 2*(self.fbHeight - self.nutOffset) 
		self.markerRadius = 10
		self.fingerRadius = 15
		self.image = ''
		self.instrument = currentState['instrument']
		self.chord = currentState['chord']
		self.root = currentState['root']
		self.ChordPositions = [] #set of fingerings for current chord/key/instrument/filter setting
		self.currentPosition = 0 # one currently being displayed
		self.scale_notes = []
		self.fingerings = []
		self.loaded = True
		self.snd = self.set_needs_display
		self.chord_num = None
		self.num_chords = None
		self.nutPositions = []
		self.stringX = []
		self.fretY = []
		self.PrevFretY = 0
		self.touched = {} # a dictionary of touched fret/string tuples as keys, note value
		self.location = (0,0)
		self.cc_mode = 'C' # versus 'identify6'
		self.scale_display_mode = 'degree'
		self.scale_mode = 'normal'
		self.showChordScale = False
		self.ChordScaleFrets = []
		self.arpMin = 0.05
		self.arpMax = 0.5
		self.arpSpeed = (self.arpMax + self.arpMin)/2.0
		self.sharpFlatState = '#'
		self.fret5thStringBanjo = 5
		
	def sharpFlat(self,sender): #toggle
		self.sharpFlatState = 'b' if self.sharpFlatState == '#' else '#'
		self.set_needs_display()
		
					
	def set_tuning(self,instrument): # store current value of tuning parameters
		self.tuning = instrument.get_tuning()
		
	def set_chord(self,chordlist): # store current value of chord
		self.chord = chordlist.get_chord()
		
	def set_root(self,root):
		self.root = keylist.get_key() # get value of key
		
	def set_chordnum(self,chord_num,num_chords):
		self.chord_num = chord_num
		self.num_chords = num_chords
		
	def set_fingerings(self,fingerings):
		self.ChordPositions = fingerings
		self.currentPosition = 0
	
	def set_scale_notes(self, scale_notes):
		'''save scale notes'''
		self.scale_notes = scale_notes

	def set_chord_num(self,number):
		self.currentPosition = number
		
	def get_chord_num(self):
		return self.currentPosition
		
	def get_num_chords(self):
		return len(self.ChordPositions)

	def fretDistance(self,scalelength, fretnumber):
		import math
		return int(scalelength - (scalelength/math.pow(2,(fretnumber/float(self.numFrets)))))

	
	def fretboardYPos(self,fret):
		return int((self.fretDistance(self.scale,fret) + self.fretDistance(self.scale,fret-1))/2.0)	
		
	def stringSpacing(self):
		global currentState
		numStrings = len(currentState['instrument']['notes'])
		offset = int(self.offsetFactor*self.fbWidth)
		return (numStrings,offset,int((self.fbWidth-2*offset)/float(numStrings-1)))
		
	def PathCenteredCircle(self,x,y,r):
		""" return a path for a filled centered circle """
		return ui.Path.oval(x -r, y -r, 2*r,2*r)		

	def PathCenteredSquare(self,x,y,r):
		""" return a path for a filled centered circle """
		return ui.Path.rect(x -r, y -r, 2*r,2*r)		
		
		
	def drawCapo(self,fret):
		global currentState
		width = self.fbWidth
		numStrings,offset,ss = self.stringSpacing()
		segment = int(width/float(numStrings))
		capos = currentState['capos'].capos
		mask = capos[fret]
		if not instrument.is5StringBanjo: #conventional instrument
			padHeight = self.fretDistance(self.scale,fret) - self.fretDistance(self.scale,fret-1) - 10
			padY = self.fretDistance(self.scale,fret-1)	+	5
			padStartX = 0
			for i,flag in enumerate(mask):
				if not flag:
					padStartX += segment
				else:
					index = i
					break
			padEndX = index*segment
			for i in range(index,len(mask)):
				if mask[i]:
					padEndX += segment
					continue
				else:
					break
			pad = ui.Path.rect(padStartX,padY,padEndX-padStartX,padHeight)
			ui.set_color('#800040')
			pad.fill()
		
		
			barHeight = int((self.fretDistance(self.scale,14) - self.fretDistance(self.scale,13))*.75)
			barY = self.fretboardYPos(fret) - barHeight/2
			barX = 0
			bar = ui.Path.rounded_rect(barX,barY,width,barHeight,10)
			ui.set_color('#E5E5E5')
			bar.fill()
		elif len(mask) != 1: #is a banjo, main capo  partial capos
			padHeight = self.fretDistance(self.scale,fret) - self.fretDistance(self.scale,fret-1) - 10
			padY = self.fretDistance(self.scale,fret-1)	+	5
			padStartX = segment
			width -= segment
			barX = segment
			pad = ui.Path.rect(padStartX,padY,width,padHeight)
			ui.set_color('#800040')
			pad.fill()					
			barHeight = int((self.fretDistance(self.scale,14) - self.fretDistance(self.scale,13))*.75)
			barY = self.fretboardYPos(fret) - barHeight/2
			bar = ui.Path.rounded_rect(barX,barY,width,barHeight,10)
			ui.set_color('#E5E5E5')
			bar.fill()
		else: # is banjo, 5th string spike
			x = self.stringX[0]
			y = self.fretboardYPos(fret)
			spike = self.PathCenteredSquare(x,y,20)
			ui.set_color('#E5E5E5')
			spike.fill()
			

		
		
		
	def drawFingerboard(self):
		global currentState
		if self.tuning:
			
			# draw fingerboard
			
			startX = 0
			startY = 0
			width = self.fbWidth
			height = self.fbHeight
			if instrument.is5StringBanjo:
				segment = int(width/5.0)
				width -= segment
				startX = segment
			fretboard = ui.Path.rect(startX, startY, width, height)
			ui.set_color('#4C4722')
			fretboard.fill()
					
			# draw nut
			
			nut = ui.Path.rect(startX,startY,width,self.nutOffset)
			ui.set_color('#ECF8D7')
			nut.fill()
			
			if instrument.is5StringBanjo: # draw 5th string segment
				radius = 30
				fret5SB = self.fret5thStringBanjo
				ui.set_color('#4C4722')
				fretboard = ui.Path.rect(0,self.fretDistance(self.scale,fret5SB-1)+radius,segment,height-radius)
				fretboard.fill()
				fretboard = ui.Path.rect(radius,self.fretDistance(self.scale,fret5SB-1),segment-radius,radius)
				fretboard.fill()
				semi = ui.Path()
				semi.move_to(radius,self.fretDistance(self.scale,fret5SB-1)+radius)
				semi.add_arc(radius,self.fretDistance(self.scale,fret5SB-1)+radius,radius,0,270)
				semi.close()
				semi.fill()
#
				square = ui.Path.rect(segment-radius,self.fretDistance(self.scale,fret5SB-1)-radius,radius,radius)
				square.fill()
				semi = ui.Path()
				semi.move_to(segment-radius,self.fretDistance(self.scale,fret5SB-1)-radius)
				semi.add_arc(segment-radius,self.fretDistance(self.scale,fret5SB-1)-radius,radius,90,180)
				ui.set_color('white')
				semi.fill()
				
		#draw frets
		
			ui.set_color('white')
			fretSpace = int((self.fbHeight - 2*self.nutOffset)/(self.numFrets))

			self.fretY = [0]
			for index in range(self.numFrets):
				yFret = self.fretDistance(self.scale,index+1)
				self.fretY.append(yFret)
				self.PrevFretY = yFret
				fret = ui.Path()
				fret.line_width = 3
				if instrument.is5StringBanjo and index < fret5SB-1:
					fret.move_to(startX,yFret)
				else:
					fret.move_to(0,yFret)
				fret.line_to(self.fbWidth,yFret)
				fret.stroke()

			
			markers = [3,5,7]
			if instrument_type() == 'ukulele':
				markers.append(10)
			else:
				markers.append(9)
			for index in markers:		
				markeryPos = self.fretboardYPos(index)
				marker= self.PathCenteredCircle(int(0.5*self.fbWidth), markeryPos, self.markerRadius)
				marker.fill()
			

			markery12 = markeryPos = self.fretboardYPos(12)
			for xfraction in [0.25,0.75]:
				marker= self.PathCenteredCircle(int(xfraction*self.fbWidth), markery12, self.markerRadius)
				marker.fill()
				
		# draw strings
		
		#assume width is 1.5" and strings are 1/8" from edge
			numStrings,offset,ss = self.stringSpacing()
			self.nutPosition = []
			ui.set_color('grey')
			self.stringX = []
			for index in range(numStrings):
				startY = 0
				if instrument.is5StringBanjo and index == 0:
					startY = (self.fretDistance(self.scale,fret5SB)+self.fretDistance(self.scale,fret5SB-1))/2
				xString = offset + index*ss
				self.stringX.append(xString)
				string = ui.Path()
				string.line_width = 3
				string.move_to(xString,startY)
				string.line_to(xString,self.fbHeight)
				string.stroke()
				self.nutPosition.append((xString,int(0.5* self.nutOffset)))
				
				
		# if 5 string banjo, draw tuning peg
		
			if instrument.is5StringBanjo:
				pegX = self.stringX[0]
				pegY = (self.fretDistance(self.scale,fret5SB)+self.fretDistance(self.scale,fret5SB-1))/2
				peg = self.PathCenteredCircle(pegX,pegY,15)
				ui.set_color('#B2B2B2')
				peg.fill()
				peg = self.PathCenteredCircle(pegX-7,pegY-6,2)
				ui.set_color('white')
				peg.fill()
		
		
	def draw(self):
		global currentState
		self.tuning = currentState['instrument']
		self.root = currentState['root']
		self.chord = currentState['chord']
		try:
			self.key = currentState['root']['noteValue']
			self.keySignature = currentState['root']['title']
		except:
			pass
		
		try:
			self.scaleType = currentState['scale']['title']
		except:
			pass
		

		self.drawFingerboard()
		
		capos = currentState['capos']
			
		for key in capos.capos.keys():
			self.drawCapo(key)
		
		if self.tuning:			
			capoOffsets = capos.capoOffsets()
			if self.ChordPositions and self.cc_mode == 'C': 
				# if there are some, draw current fingering or chord tone frets
				if not self.showChordScale:
					self.num_chords.text = "{}".format(len(self.ChordPositions))
					self.chord_num.text = "{}".format(self.currentPosition+1)
					middle_field.text = 'of'
				 	fingering,chordTones,fretPositions = self.ChordPositions[self.currentPosition]
				 	ui.set_color('red')
				 	for i,string in enumerate(fingering):
						x,y,chordtone,nutmarker = string
						if i == 0 and instrument.is5StringBanjo:
							if fretPositions[i] == -1:
								y = (self.fretDistance(self.scale,self.fret5thStringBanjo)+self.fretDistance(self.scale,self.fret5thStringBanjo-1))/2
						try:
							if fretPositions[i] == capoOffsets[i]:
								nutmarker = True
						except:
							console.hud_alert('fretPositions[i] == capoOffsets[i] i= {}'.format(i),'error',5)
	
						if not nutmarker:
							ui.set_color('red')
							marker= self.PathCenteredCircle(x,y,self.fingerRadius)
							marker.fill()
							ui.set_color('white')
							size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',
							                                         22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							               font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
				 		else:
				 			size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							               font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER,color='black')
							size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							               font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER,color='red')	
				elif self.ChordScaleFrets:
					for string,fret_note_pairs in enumerate(self.ChordScaleFrets):
						for fret,note in fret_note_pairs:
							chordtone = ccc['SCALENOTES'][note]
							x = self.stringX[string]
							if fret != -1:
								y = self.fretboardYPos(fret+1)
							else:
								if string == 0 and instrument.is5StringBanjo:
									y = (self.fretDistance(self.scale,fret5SB)+self.fretDistance(self.scale,fret5SB-1))/2
								else:
									y = self.nutPosition[0][1]
							ui.set_color('red')
							if note == 0:
								marker= self.PathCenteredSquare(x,y,self.fingerRadius)
							else:
								marker= self.PathCenteredCircle(x,y,self.fingerRadius)
							marker.fill()
							ui.set_color('white')
							size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',
							                                         22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							               font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
						               
			elif self.root and self.chord and self.cc_mode == 'C':
				sound.play_effect('Woosh_1')
				self.chord_num.text = "Try dropping"
				middle_field.text = "root, 3rd" 
				self.num_chords.text = "or 5th"			

			
			elif self.cc_mode == 'I':# identify mode
				for key in self.touched.keys():
					values = self.touched[key]
					x = self.stringX[values[2]]
					y = self.fretboardYPos(values[3])
					outchar = ccc['NOTE_NAMES'][values[0]%12].split('/')[0]
					if values[3]:
						ui.set_color('red')
						marker= self.PathCenteredCircle(x,y,self.fingerRadius)
						marker.fill()
						ui.set_color('white')
						size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',
						                                         22),alignment=ui.ALIGN_CENTER)
						ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
						               font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
					else:
						y = self.nutPosition[0][1]
						size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER)
						ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
						               font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER,color='black')
						size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
						ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
						               font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER,color='red')	
				               
			elif self.cc_mode == 'S': # display scale notes
				ui.set_color('red')
				if self.scale_notes:
				 	for i,string in enumerate(self.scale_notes):
						for fret,note in string:
							if fret < capoOffsets[i]:
								continue
							x = self.stringX[i]
							if fret == 1:
								y = self.fretboardYPos(fret) + 12
							elif fret:
								y = self.fretboardYPos(fret)
							else:
								y = self.nutPosition[0][1] + self.fingerRadius*0.3
							ui.set_color('red')
							if note == self.key:
								marker= self.PathCenteredSquare(x,y,self.fingerRadius)
							else:
								marker= self.PathCenteredCircle(x,y,self.fingerRadius)
							marker.fill()
							if self.scale_display_mode == 'degree':
								outchar = ccc['SCALENOTES'][(note - self.key) % 12]
							else:
								outchar = self.noteName(note)
							ui.set_color('white')
							size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',
						                                         22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
						               font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
				if self.scaleFrets: # mark the scale notes
					ui.set_color('yellow')
					self.fifthPresent = False # prevent 5 and 5# from both being highlighted chord tones.
					
					for string,fret in self.scaleFrets:
						if fret < capoOffsets[i]:
							continue
						x = self.stringX[string]				
						if fret == 1:
							y = self.fretboardYPos(fret) + 12
						elif fret:
							y = self.fretboardYPos(fret)
						else:
							y = self.nutPosition[0][1] + self.fingerRadius*0.3
						self.chordtone_color(string,fret)
						marker= self.PathCenteredCircle(x,y,self.fingerRadius + 10)
						marker.line_width = 3
						marker.stroke()
			else:
				pass

	def chordtone_color(self,string,fret):
		# convert from string/fret to note
		key = fretboard.key
		thisString = self.scale_notes[string]
		for thisFret,thisNote in thisString:
			color = 'red'
			if fret == thisFret:
				scaleTone = (thisNote - key) % 12
				if scaleTone == 0:
					color = 'green'
					break
				elif scaleTone in (3,4): # b3 and 3
					color = 'yellow'
					break
				elif scaleTone in (7,8): # 5 and 5#
					if scaleTone == 7:
						color = 'white'
						self.fifthPresent = True
						break
					elif scaleTone == 8 and not self.fifthPresent:
						color = 'white'
						break
				elif scaleTone in (10,11):
					color = 'orange'
					break
		ui.set_color(color)
		return

	def noteName(self,note):
		'''return the name of the note with proper use of sharps or flats'''
		key = self.key
		keySig = self.keySignature
		if keySig in ccc['CIRCLE_OF_FIFTHS'].keys():
			sf = ccc['CIRCLE_OF_FIFTHS'][keySig]
		else:
			console.hud_alert('{} not in COF'.format(keySig),'error',2)
			sf = 1 if self.sharpFlatState == '#' else -1 # use preference
		if self.scaleType in ccc['TRUE_ROOT'].keys():
			origKeySig = keySig	
			key = (key - ccc['TRUE_ROOT'][self.scaleType]) % 12
			keySig = ccc['NOTE_NAMES'][key].split('/')
			origSF = sf 
			if len(keySig) == 1:
				keySig = keySig[0]
			else:
				if origKeySig in ccc['CIRCLE_OF_FIFTHS'].keys():
					origSF = ccc['CIRCLE_OF_FIFTHS'][origKeySig]
				else:
					origSF = 1 if self.sharpFlatState == '#' else -1
			sf = origSF
		outchar = ccc['NOTE_NAMES'][note].split('/')
		index = 0
		if len(outchar) > 1:
			if sf < 0:
				index = 1
		return outchar[index]
				
	def distance(self,x,a): 
		'''return a list of distances from x to each element in a'''
		return [math.sqrt((x-item)*(x-item)) for item in a]
		
	def closest(self,x,a):
		''' return index of closest element in a to x'''	
		deltas = self.distance(x,a)
		index,value = min(enumerate(deltas),key=lambda val:val[1])
		return index

	def touch_began(self,touch):
		if self.cc_mode == 'I':
			offsets = capos.capoOffsets()
			x,y = touch.location
			string = self.closest(x,self.stringX)
			fret = self.closest(y,self.fretY)
			if fret < offsets[string]:
				return
			location = (string,fret)
			if location in self.touched.keys():
				del self.touched[location]
			else:	
				for key in self.touched.keys():
					if key[0] == string:
						del self.touched[key]
						break
				self.touched[location] = (self.tuning['notes'][string]+fret,self.tuning['octave'],string,fret)
				octave,tone = divmod((self.tuning['notes'][string]+fret),12)
				waveName = 'waves/' + ccc['NOTE_FILE_NAMES'][tone] + "{}.wav".format(octave+self.tuning['octave'])
				sound.play_effect(waveName)
			self.set_needs_display()
		elif self.cc_mode == 'S': # label the two octave scale starting at this root
			x,y = touch.location
			string = self.closest(x,self.stringX)
			fret = self.closest(y,self.fretY)
			self.location = (string,fret)
			octave,tone = divmod((self.tuning['notes'][string]+fret),12)
			if tone != self.key: 
				sound.play_effect('Drums_01')
				return None
			self.scaleFrets = calc_two_octave_scale(self.location,mode=self.scale_mode)
			self.set_needs_display()
		elif self.cc_mode == 'C': # switch display to chord tones
			self.showChordScale = not self.showChordScale
			if self.showChordScale:
				#toggle on the scaleortone buttons
				self.ChordScaleFrets = calc_chord_scale()
			else:
				#toggle off the scaleotone buttons
				self.ChordScaleFrets = []
			self.set_needs_display()
			
		

#####################################
# fingering positions for drawing

	def fingeringDrawPositions(self,key,chordtype,tuning,fingering):
		""" given a fingering,chord and tuning information and virtual neck info,
		    return the center positions all markers.  X and open strings will be 
		    marked at the nut"""
		scaleNotes = getScaleNotes(key, chordtype, tuning, fingering)
		#if len(scaleNotes) != len(fingering):
		chordDrawPositions = []
		numStrings,offset,ss = self.stringSpacing()
		for i,fretPosition in enumerate(fingering): #loop over strings, low to high
			try:
				note = scaleNotes[i]
			except:
				continue
			atNut = None
			xpos = offset + i*ss	
			if fretPosition in [-1,0]: #marker at nut
				ypos = int(0.5* self.nutOffset) 
				atNut = 'X' if fretPosition else 'O'
			else:
				ypos = self.fretboardYPos(fretPosition)
			chordDrawPositions.append((xpos,ypos,note,atNut))		
			
		
		return chordDrawPositions		

	def get_instrument(self):
		return self.instrument
		
##########################################################
# instrument/tuning object
	
class Instrument(object):	
	global currentState
	def __init__(self, items, fb):
		self.items = items
		self.fb = fb
		self.instrument = currentState['instrument']
		self.is5StringBanjo = False
	
	
	def onEdit(self,button):
		pass
	
	
	def __getitem__(self,key):
		try:
			return self.tuning[key]
		except:
			return None
			 
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
	
	def updateScaleChord(self):
		mode = currentState['mode']
		if mode == 'C':
			self.fingerings = calc_fingerings()
			if self.fb.showChordScale:
				self.fb.ChordScaleFrets = calc_chord_scale()
			self.fb.set_fingerings(self.fingerings)
		elif mode == 'S':
			self.scale_notes = calc_scale_notes()
			self.fb.set_scale_notes(self.scale_notes)
		
		self.fb.touched = {}
		self.fb.set_needs_display()
		tuningDisplay.title = tuningLabel(self.tuning['notes'])
		
# when new instrument is chosen, update the global and 
# redraw the fretboard
# also draw first chord for the current root/type 
##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry
		
	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'


##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row): # Instrument
		global tuningDisplay, spanSpinner, currentState
	
		self.toggleChecked(row)
		try:
			self.toggleChecked(self.tuning['row'])
		except:
			pass
		tableView.reload_data()	
		thisRow = self.items[row]
		self.tuning = { 
		               'title':		thisRow['title'],
		                'notes':	thisRow['notes'],
		                'span':		thisRow['span'],
		                'octave':	thisRow['octave'],
		                'row':		row
		               }
		currentState['instrument'] = self.tuning

		self.is5StringBanjo = True if instrument_type() == 'banjo' and len(thisRow['notes']) == 5 else False

		currentState['span'].value = thisRow['span']
		currentState['span'].limits  = (1,thisRow['span']+2)
		self.filters.set_filters() 
		self.tvFilters.reload_data()
		currentState['capos'].reset()
		self.fb.scaleFrets = []
		self.updateScaleChord()

		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1

	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)

	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		import ui
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
				
###################################################
# chord type



class Chord(object):
	global curentState
	def __init__(self,items,fb):
		self.items = items
		self.chord = currentState['chord']
		self.fb = fb
		
		
	def onEdit(self,button):
		pass
		
	def __getitem__(self,key):
		try:
			return self.chord[key]
		except:
			return None	
			
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
		
# when new chord is chosen, update the global

##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry
		
	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row):	#Chord
	
		self.toggleChecked(row)
		try:
			self.toggleChecked(self.chord['row'])
		except:
			pass
		tableView.reload_data()	
		self.chord = {'title': self.items[row]['title'], 'fingering': self.items[row]['fingering'], 'row':row}
		currentState['chord'] = self.chord
		
		setChordSpelling()
		
		fingerings = calc_fingerings()
		self.fb.set_fingerings(fingerings)
		if self.fb.showChordScale:
			self.fb.ChordScaleFrets = calc_chord_scale()
		self.fb.set_needs_display()
		
		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1

	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)

	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def get_chord(self):
		return self.chord
		
		

class Scale(object):
	global currentState
	def __init__(self, items,fb):
		self.items = items
		self.fb = fb
		
	def onEdit(self,button):
		pass
		
	def __getitem__(self,type):
		try:
			return self.scale[type]
		except:
			return None

	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
		
# when new chord is chosen, update the global

##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry
		
	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row):	#Scale
	
		self.toggleChecked(row)
		try:
			self.toggleChecked(self.scale['row'])
		except:
			pass
		tableView.reload_data()	
		self.scale = {'title': self.items[row]['title'], 
									'scaleintervals': self.items[row]['scaleintervals'], 'row':row}
		currentState['scale'] = self.scale
		
		self.scale_notes = calc_scale_notes()		
		relativeMajorDisplay()
		self.fb.set_scale_notes(self.scale_notes)
		self.fb.scaleFrets = []
		self.fb.set_needs_display()	
		
		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1

	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)

	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def get_scale(self):
		return self.scale
		
	
###################################################
# root tone


import ui

class Root(object):
	global currentState
	def __init__(self, items,fb):
		self.items = items
		self.root = currentState['root']
		self.fb = fb
		
	def __getitem__(self,key):
		try:
			return self.root[key]
		except:
			return None
			
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry
		
	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row): #Root
		
		self.toggleChecked(row)
		try:
			self.toggleChecked(self.root['row'])
		except:
			pass
		tableView.reload_data()	
		self.root = {'title': self.items[row]['title'], 'noteValue': self.items[row]['noteValue'], 'row':row}
		currentState['root'] = self.root
		
		mode = currentState['mode']
		if mode == 'C':
			self.fingerings = calc_fingerings()
			setChordSpelling()
			self.fb.set_fingerings(self.fingerings)
			if self.fb.showChordScale:
				self.fb.ChordScaleFrets = calc_chord_scale()
		elif mode == 'S':
			relativeMajorDisplay()
			self.scale_notes = calc_scale_notes()
			self.fb.scaleFrets = []
			self.fb.set_scale_notes(self.scale_notes)			
		

		self.fb.set_needs_display()
		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1

	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)

	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def get_root(self):
		try:
			return self.root
		except:
			return None
			
			
##################################################			
# 

class Filters(ui.View):
	global currentState,instrument_type
	def __init__(self,fb):
		self.fb = fb
		self.filter_list = []
		self.items = ccc['FILTER_LIST_CLEAN']
		
	def onEdit(self,button):
		pass
	
	def set_filters(self):
		self.filter_list = []
		self.items = ccc['FILTER_LIST_CLEAN']
		it = instrument_type()
		if it == 'guitar':
			self.items = self.items + ccc['GUITAR_LIST_CLEAN']
		elif it == 'mando':
			self.items = self.items + ccc['MANDOLIN_LIST_CLEAN']
		else: # generic
			pass
		for item in self.items:
			item['accessory_type'] = 'none'
			
	
	def reconsile_filters(self,filter):
		if filter in ccc['FILTER_MUTUAL_EXCLUSION_LIST'].keys():
			exclude = ccc['FILTER_MUTUAL_EXCLUSION_LIST'][filter]
			for exclusion in exclude:
				if exclusion in self.filter_list:
					self.filter_list.remove(exclusion)
					for item in self.items:
						if item['title'] == exclusion:
							item['accessory_type'] = 'none'
					
			
		

##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry
		
	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'

	def offChecked(self,row):
		self.items[row]['accessory_type'] = 'none'
		
	def onChecked(self,row):
		self.items[row]['accessory_type'] = 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row):	#Filters
	
		self.toggleChecked(row)
		filtername = self.items[row]['title']

		if self.isChecked(row):
			if not filtername in self.filter_list:
				self.filter_list.append(filtername)
				self.reconsile_filters(filtername)		
		else:
			if filtername in self.filter_list:
				self.filter_list.remove(filtername)
				

		tableView.reload_data()	
		currentState['filters'] = self.filter_list
		self.fingerings = calc_fingerings()
		self.fb.set_fingerings(self.fingerings)
		self.fb.set_needs_display()		
				
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1

	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)

	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def get_chord(self):
		return self.chord
		
		
class Capos(object):
	global currentState
	def __init__(self, items):
		self.items = items
		self.capos = {}
		currentState['capos'] = self		
		self.fb = currentState['fretboard']
	
	def onEdit(self,button):
		pass
		
	def __getitem__(self,key):
		try:
			return self.root[key]
		except:
			return None
			
	def reset(self):
		for row in range(len(self.items)):
			self.items[row]['fret'] = 0
			self.items[row]['accessory_type'] = 'none'	
		self.row = 0
		self.capos = {}
		tvCapos.reload_data()
		
	def capoOffsets(self):
		''' calculate and return the offsets due to the applied capos'''
		global currentState
		capos = currentState['capos'].capos
		numStrings = len(currentState['instrument']['notes'])
		isFSB = instrument.is5StringBanjo
		offsets = [0]*numStrings
		if not isFSB:
			for fret in capos.keys():
				mask = capos[fret]
				for i in range(numStrings):
					value = fret if mask[i] else 0
					offsets[i] = max(offsets[i],value)
		else: # 5 string banjo
			offsets = [fretboard.fret5thStringBanjo,0,0,0,0]
			for fret in capos.keys():
				mask = capos[fret]
				if len(mask) == 1:
				# is the fifth string
					offsets[0] = max(offsets[0],fret)
				else:
					for i in range(1,5):
						value = fret if mask[i] else 0
						offsets[i] = max(offsets[i],value)
		return offsets
			
		
		
			
##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry
		
	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row): #capos
		global currentState,mainView
		fb = currentState['fretboard']
		self.row = row
		fret = self.items[row]['fret']
		if self.isChecked(row):
			# uncheck and remove the entry in the dictionary
			self.toggleChecked(row)
			self.items[row]['fret'] = 0
			del self.capos[fret]
			tableView.reload_data()
			instrument.updateScaleChord()
			fb.set_needs_display()
		else:
			# need to handle the rest via special data entry view
			numFrets = fretboard.numFrets
			fretEnter = mainView['view_fretEnter']
			minFret = fretEnter.min = 1
			maxFret = fretEnter.max = numFrets
			if self.items[row]['title'] == 'Banjo 5th':
				if instrument_type() != 'banjo':
					return None
				else:
					minFret = fretEnter.min = fretboard.fret5thStringBanjo + 1
			fretEnter.label.text = "Enter fret # {}-{}".format(minFret,maxFret)
			fretEnter.hidden = False
			
		

		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1

	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)

	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		fret = self.items[row]['fret']
		text = self.items[row]['title']
		cell.text_label.text = "{} at fret {}".format(text,fret) if fret else text
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		

					
		
class FretEnter(ui.View):
	''' implement routines for fret entry'''
	def did_load(self):
		self.row = 0
		self.entry = 0
		self.min = 0
		self.max = 0
		
		for subview in self.subviews:
			name = subview.name
			if name.startswith('btn'):
				subview.action = self.onButton
			elif name.startswith('tf'):
				self.textfield = subview
			elif name.startswith('lab'):
				self.label = subview
				
			
			
	def onButton(self,button): #business end of fretEnter
		global currentState
		capos = currentState['capos']
		numFrets = fretboard.numFrets
		row = capos.row
		
		if button.name.endswith('Cancel'):
			mainView['view_fretEnter'].hidden = True
		else:
			entry = self.textfield.text
			if not entry.isnumeric():
				console.hud_alert('invalid entry','error')
				return None
			value = int(entry)
			if self.min <= value <= self.max: #valid
				capos.items[row]['fret'] = value
				capos.toggleChecked(row)
				capos.capos[value] = capos.items[row]['mask']
				mainView['view_fretEnter'].hidden = True
				tvCapos.reload_data()
				instrument.updateScaleChord()
				fretboard.set_needs_display()
			else:
				console.hud_alert('fret outside allowed range','error')
				self.textfield.text = '0'
				
						
			

#
# Display routines

def parseChordName(chordstr):
	p = re.compile('([A-G][#b]{0,1})(.*)', re.IGNORECASE)
	m = p.match(chordstr)
	if m != None:
		return m.group(1,2) # key and chordtype
	else:
		return ['','']

##########################################
##########################################
# S. Pollack Code below



###################################################
# previous/next chord form

def onPrevNext(button):
	global currentState
	try:
		fretboard = currentState['fretboard']
	except:
		return
	if fretboard.ChordPositions:
		cn = fretboard.get_chord_num()
		nc = fretboard.get_num_chords()
		if button.name == 'button_down':
			if cn < nc-1:
				cn +=1 
		else:
			cn -= 1
			if cn < 0:
				cn = 0
		fretboard.set_chord_num(cn)
		fretboard.set_needs_display()
					
	
###################################################
# play arpeggio

def play(button):
	global currentState
	fretboard = currentState['fretboard']
	if os.path.exists('waves'):
		baseOctave = currentState['instrument']['octave']
		strings = currentState['instrument']['notes']
		if fretboard.cc_mode == 'C':
			cc = fretboard.ChordPositions[fretboard.currentPosition]
			frets = cc[2]
			dead_notes = [item[3] == 'X' for item in cc[0]]
			tones = []
			for fret,string,dead_note in zip(frets,strings,dead_notes):
				if  dead_note:
					continue
				octave,tone = divmod(string + fret,12) 
				tones.append((tone,octave+baseOctave))
		elif fretboard.cc_mode == 'I': # identify
			positions = [string_fret for string_fret in fretboard.touched.keys()]
			positions = sorted(positions,key=lambda x:x[0])
			position_dict = {}
			for string,fret in positions:
				position_dict[string] = fret
			tones = []
			for i,pitch in enumerate(strings):
				if position_dict.has_key(i):
					octave,tone = divmod(pitch + position_dict[i],12)
					tones.append((tone,octave+baseOctave))
		
		else: #scale
			pass
			
		for tone,octave in tones:
			waveName = 'waves/' + ccc['NOTE_FILE_NAMES'][tone] + "{}.wav".format(octave)
			sound.play_effect(waveName)
			time.sleep(0.05)
			if button.name == 'button_arp':
				time.sleep(fretboard.arpSpeed)
	

def play_tuning(button):
	global currentState
	fretboard = currentState['fretboard']
	if os.path.exists('waves'):
		try:
			cc = fretboard.ChordPositions[fretboard.currentPosition]
			frets = cc[2]
			dead_notes = [item[3] == 'X' for item in cc[0]]
		except:
			pass
		strings = currentState['instrument']['notes']
		baseOctave = currentState['instrument']['octave']
		tones = []
		for string in strings:
			octave,tone = divmod(string,12)
			tones.append((tone,octave+baseOctave))
		for tone,octave in tones:
			waveName = 'waves/' + ccc['NOTE_FILE_NAMES'][tone] + "{}.wav".format(octave)
			sound.play_effect(waveName)
			time.sleep(fretboard.arpSpeed)
			
def playScale(button):	
	global currentState
	fretboard = currentState['fretboard']
	if os.path.exists('waves') and fretboard.scaleFrets:
		for string,fret in fretboard.scaleFrets:
			octave,tone = divmod((fretboard.tuning['notes'][string]+fret),12)
			waveName = 'waves/' + ccc['NOTE_FILE_NAMES'][tone] + "{}.wav".format(octave+fretboard.tuning['octave'])
			sound.play_effect(waveName)	
			time.sleep(fretboard.arpSpeed)

def toggle_mode(button):
	global currentState #,fretboard,tvFind,tvScale
	fretboard = currentState['fretboard']
	tvFind = currentState['tvFind']
	tvScale = currentState['tvScale']
	mainView = currentState['mainView']
	try:
		capos.reset()
	except:
		pass


	mode = button.title
	hideshow = {}
	hideshow = {'I':  {'hide':
	                					'tableview_root tableview_type tableview_scale label1 button_scale_notes button_scale_tones chord_num label_middle button_play_scale num_chords lbl_chord lbl_fullchord lbl_definition btn_sharpFlat sp_span lbl_span sp_scale'.split(),
											'show':
														('tableview_find', 'button_find', 'button_chord', 'button_arp')
										},						
 							'C':	{'hide':
										 				'tableview_find button_find button_scale_tones button_scale_notes tableview_scale button_play_scale lbl_chord lbl_fullchord btn_sharpFlat sp_scale'.split(),
										'show': 'tableview_root tableview_type label1 chord_num num_chords label_middle button_chord button_arp sp_span lbl_span'.split()
										},
							'S': 	{'hide': 
										 					'tableview_type tableview_find button_find chord_num num_chords label_middle button_chord button_arp lbl_chord lbl_fullchord lbl_definition sp_span lbl_span'.split(),
											'show': 'tableview_scale tableview_root button_scale_tones button_scale_notes button_play_scale btn_sharpFlat sp_scale'.split()
										}
								}

	fretboard.cc_mode = mode
	
	for thisButton in "button_scale button_ident button_calc".split():
		mainView[thisButton].background_color = 'white'

	button.background_color =  '#FFCC66'
	
	currentState['mode'] = mode
	mode_hs = hideshow[mode]
	for view in mode_hs['hide']:		
		mainView[view].hidden = True
	for view in mode_hs['show']:			
		try:
			mainView[view].hidden = False
		except:
			print view
	
	if mode == 'C': # special stuff for identify
		mainView['button_edit_chord'].title = 'type'
	elif mode == 'S':
		mainView['button_edit_chord'].title = 'mode'
	else: # 'I'
		mainView['button_edit_chord'].title = ''		
		tvFind.data_source.items = []
		
	fretboard.set_needs_display()
	mainView.set_needs_display()
	
	
def set_scale_display(button):
	global currrentState
	fretboard = currentState['fretboard']
	fretboard.scale_display_mode = button.title
	fretboard.set_needs_display()
	
def find_chords(button):
	global currentState
	fretboard = currentState['fretboard']
	tvFind = currentState['tvFind']
	fingered = [fretboard.touched[key][0] for key in fretboard.touched.keys()]
	if fingered:
		fingered = sorted([x%12 for x in fingered])
		pure = []
		missing_1 = []
		missing_2 = []
		chord_list = []
		for root in range(12):
			notes_in_key = rotate(range(12),root)
			present = {}
			notevals = []
			for i,note in enumerate(notes_in_key):
				present[i] = True if note in fingered else False
				if present[i]: 
					notevals.append(i)
			for chord in ccc['CHORDTYPE']:
				deltas = set(notevals) ^ set(chord[1]) #those notes not in both (symmetric difference)
				if not deltas:
					pure.append("{}{}".format(ccc['NOTE_NAMES'][root],chord[0]))
				if deltas == set([0]):
					missing_1.append("{}{} (no root)".format(ccc['NOTE_NAMES'][root],chord[0]))
				if deltas == set([3]) or deltas == set([4]):
					missing_1.append("{}{} (no 3rd)".format(ccc['NOTE_NAMES'][root],chord[0]))				
				if deltas == set([7]):
					missing_1.append( "{}{} (no 5th)".format(ccc['NOTE_NAMES'][root],chord[0]))
				if deltas == set([0,7]):
					missing_2.append("{}{} (no root or 5th)".format(ccc['NOTE_NAMES'][root],chord[0]))
		for list in [pure,missing_1,missing_2]:
			if list:
				chord_list += list
				chord_list.append("-------")
		tvFind.data_source.items = chord_list
		tvFind.reload_data()	
		
def on_slider(sender):
	sound.set_volume(sender.value)
	
def on_slider_arp(sender):
	global currentState
	fretboard = currentState['fretboard']
	v = sender.value
	fretboard.arpSpeed = fretboard.arpMin*v + (1.0-v)*fretboard.arpMax
	
def onSpanSpinner(sender):
	''' repond to changes in span'''
	global currentState
	value = sender.value
	thisInstrument = currentState['instrument']
	if thisInstrument:
		currentState['instrument']['span'] = value
		instrument.updateScaleChord()

def setState(sfObj):
	''' inputs the state file object and uses to allow for a selection of the current state'''
	stateObj = json.loads(sfObj)
	
	
	
def initStateObj():
	''' create a state file object that stores the settings of the capos, filerters and the current instrument
	
	the structure of the file is a set of names "states"
		each state has the sets of capos, filters and the instrument
		the last "loaded" state is the default
'''
	stateObj = {'default': 		
	                 			{'capos': [],     #rows in the capos.items
	            					 'filters': [],   #rows in the filters.items
	            					 'instrument': 0, # row in the instruments.items
	            					}, 
	            }
	return json.dumps(stateObj)
	
	
def applyState(state):
	''' apply the values in the stateObj'''
	global instrument,capos,filters
	if state['capos']:
		pass
		
	if state['filters']:
		pass
	
	instrumentRow = int(state['instrument'])
	
	for row in range(instrument.items):
		instrument.items[row]['accessory_type'] = 'checkmark' if row == instrumentRow else 'none'
			
	thisRow = instrument.items[instrumentRow]
	instrument.tuning = { 
		               'title':		thisRow['title'],
		                'notes':	thisRow['notes'],
		                'span':		thisRow['span'],
		                'octave':	thisRow['octave'],
		                'row':		instrumentRow
		               }
	currentState['instrument'] = instrument.tuning

	instrument.is5StringBanjo = True if instrument_type() == 'banjo' and len(thisRow['notes']) == 5 else False

	currentState['span'].value = thisRow['span']
	currentState['span'].limits  = (1,thisRow['span']+2)
	instrument.filters.set_filters() 
	tvFilters.reload_data()
	tvCapos.reload_data()
	tvInst.relaod_data()
	instrument.fb.scaleFrets = []
	instrument.updateScaleChord()
	
	
class SettingsView(ui.View):
	pass
	
	
class InstrumentEditor(ui.View):
	pass
	
	
		
def onSaveState(button):
	pass
	
def onLoadState(button):
	pass
	
def createConfig():
	global ccc
	if os.path.exists('config'):
		try:
			resp = console.alert('config exists','Restore the "factory settings"?','OK')
			os.remove('config')
		except KeyboardInterrupt as e:
			return
# read in the non-local data and write it out as a json object
	ccc = {}
	for constant in cccInit.__dict__.keys():
		if constant[0] != '_' and constant[0].isupper(): # a real constant
			ccc[constant] = cccInit.__dict__[constant]
			
	fh = open('config','wb')
	json.dump(ccc,fh)
	fh.close()
		


		
	
def restoreConfig():
	global ccc
	if not os.path.exists('config'):
		console.hud_alert('config file missing, restoring','error',2)
		createConfig()
	fh = open('config','rb')
	ccc = json.load(fh)
		
		
		
def onScaleSpinner(sender):
	fretboard.scale_mode = sender.value
	fretboard.scaleFrets = calc_two_octave_scale(fretboard.location,mode=fretboard.scale_mode)
	fretboard.set_needs_display()
		
##############################################
##############################################
if __name__ == "__main__":	
	
	
	
	if not os.path.exists('waves'):
		console.alert('waves sound files not present, run makeWave.py')
		sys.exit(1)
		
	if not os.path.exists('config'):
		createConfig() 
	else:
		restoreConfig()
		
	currentState = {'root':None,'chord':None,'instrument':None,'filters':None,'scale': None,'mode':'C'}	
	mainView = ui.load_view()
	
	num_chords = mainView['num_chords']
	chord_num = mainView['chord_num']
	middle_field = mainView['label_middle']
	fretboard = mainView['fretboard']
	tvRoot = mainView['tableview_root']
	root_list = ccc['ROOT_LIST_CLEAN']
	root = Root(root_list,fretboard)
	tvRoot.data_source = tvRoot.delegate = root
	
	tvType = mainView['tableview_type']
	chord_list = ccc['CHORD_LIST_CLEAN']
	chord = Chord(chord_list,fretboard)
	chord.reset()
	tvType.data_source = tvType.delegate = chord
	mainView['button_edit_chord'].action = chord.onEdit
	
	tvInst = mainView['tableview_inst_tune']
	tuningDisplay = mainView['button_tuning']
	tuningDisplay.title = ''
	tuningDisplay.action = play_tuning


	# fretboard is a custom view and is instanciated by the ui.load_view process
	tuning_list = ccc['TUNING_LIST_CLEAN']
	instrument = Instrument(tuning_list,fretboard)
	mainView['button_edit_instrument'].action = instrument.onEdit
	instrument.reset()
	tvInst.data_source = tvInst.delegate = fretboard.instrument = instrument
	
	tvFilters = mainView['tableview_filters']
	filter_list = ccc['FILTER_LIST_CLEAN']
	filters = Filters(fretboard)
	instrument.tvFilters = tvFilters
	instrument.filters = filters
	filters.instrument = instrument
	tvFilters.data_source = tvFilters.delegate = filters
	tvFilters.hidden = False
	mainView['button_edit_filters'].action = filters.onEdit

	tvFind = mainView['tableview_find']
	tvFind.data_source.items = []
	tvFind.hidden = True

	tvScale = mainView['tableview_scale']
	tvScale.data_source.items = []
	tvScale.hidden = True	
	scale_list = ccc['SCALE_LIST_CLEAN']
	scale = Scale(scale_list,fretboard)
	tvScale.data_source = tvScale.delegate = scale
	
	
	
	mainView['button_arp'].action = play
	mainView['button_chord'].action = play
	mainView['button_ident'].action = toggle_mode
	mainView['button_calc'].action = toggle_mode
	mainView['button_scale'].action = toggle_mode
	mainView['button_scale_notes'].action = set_scale_display
	mainView['button_scale_tones'].action = set_scale_display
	mainView['button_find'].action = find_chords
	mainView['button_find'].hidden = True
	mainView['button_up'].action = mainView['button_down'].action = onPrevNext
	mainView['button_scale'].action = toggle_mode
	mainView['button_play_scale'].action = playScale
	mainView['btn_sharpFlat'].action = fretboard.sharpFlat
	mainView['btn_sharpFlat'].hidden = True
	mainView['slider_arp'].action = on_slider_arp
	mainView['lbl_chord'].hidden = True
	mainView['lbl_fullchord'].hidden = True
	mainView['lbl_definition'].hidden = True

	
	currentState['tvFind'] = tvFind
	currentState['tvScale'] = tvScale
	currentState['fretboard'] = fretboard
	currentState['mainView'] = mainView
	
	tvCapos = mainView['tableview_capos']
	capo_list = ccc['CAPOS']
	capos = Capos(capo_list)
	mainView['button_edit_capos'].action = capos.onEdit
	tvCapos.data_source = tvCapos.delegate = capos
	
	spanSpinner = Spinner(spinnerSize=(100,50),
	                      
	                      name='sp_span',
	                      fontSize = 18,
	                      initialValue=ccc['SPAN_DEFAULT_UNKNOWN'],
	                      limits=(2,ccc['SPAN_DEFAULT_UNKNOWN']+2),
	                      action=onSpanSpinner)
	mainView.add_subview(spanSpinner)
	spanSpinner.position((580,443))
	
	scaleSpinner = Spinner(spinnerSize=(120,40),
	                       name='sp_scale',
	                       fontSize = 12,
	                       initialValue=['normal','down','open','FourOnString'],
	                       action=onScaleSpinner)
	mainView.add_subview(scaleSpinner)
	scaleSpinner.position((570,300))
	scaleSpinner.hidden = True
	
	mainView['view_fretEnter'].hidden = True
	mainView['sp_span'].hidden = True
	currentState['span'] = mainView['sp_span']
	
	mainView['button_save'].action = onSaveState
	mainView['button_load'].action = onLoadState
	
	mainView['view_settingsView'].hidden = True
	mainView['view_instrumentEditor'].hidden = True
	
	
	
	fretboard.set_chordnum(chord_num,num_chords)
	toggle_mode(mainView['button_calc'])
	sound.set_volume(0.5)
	
# implement state file 

	STATE_FILE = 'state.json'
	if os.path.exists(STATE_FILE):
		stateFile = open(STATE_FILE,'rb')
		stateFileObj = stateFile.read()
		stateFile.close()
		setState(stateFileObj)
	else:
		stateFileObj = initStateObj()
		stateFile = open(STATE_FILE, 'wb')
		stateFile.write(stateFileObj)
		stateFile.close()
		
	
	mainView.present(style='full_screen',orientations=('landscape',))
