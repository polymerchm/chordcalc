#!/usr/bin/python

"""
Chord Calculator
Version 0.3
Copyright (c) 28 Dec 2008, Gek S. Low

Modified to operate under Pythonista iOS ui environment
Copyright (c) August 19th, 2014						Steven K. Pollack
Free for personal use. All other rights reserved.

USE AT YOUR OWN RISK!
This software is provided AS IS and does not make any claim that it actually works, or that it will not cause your computer to self-destruct or eat up your homework.

Note that some calculated chords may be playable only by aliens with 10 tentacles. Please use your common sense. The author will not be responsible for any injuries from attempts at impossible fingerings.

The author reserves the right to change the behavior of this software without prior notice


 									
View objects:
	
tableview_root - 			root tone of chord
tableview_type - 			chord type
tableview_inst_tune - instrument/tuning selector
tableview_filters     filters selection 
view_neck					- 	drawing of neck/fingering
button_up							previous chord shape/position
button_down						next chord shape/position
button_arp						play arpeggio
button_chord					play chord 
button_tuning					play the open strings

"""

import sys, os.path, re, ui, console, sound, time
from PIL import Image
from copy import deepcopy
from chordcalc_constants import * 



def calc_fingerings(currentState):
	try:
		key = currentState['root']['noteValue']
		note = currentState['root']['title']  # since "C" has a note value of zero, use note title as indicator
	except:
		return
	try:
		chordtype = currentState['chord']['fingering']
	except:
		return
	try:
		tuning = currentState['instrument']['notes']
	except:
		return
	try:
		instrument = currentState['instrument']
	except:
		return
	try:
		filters = currentState['filters']
	except:
		return
	span = currentState['instrument']['span']
	option = 0
	
	if note and chordtype and tuning:
		fingerPositions = []	
		fingerings = []
		console.show_activity()
		for position in range(0,12,span):
			fingerings = fingerings + findFingerings(key, chordtype, tuning, position, span, option)
			#if no fingerings return, abandon the root, then 5th then 3rd.
			if fingerings:
				for fingering in fingerings:
					fingerMarker = fretboard.fingeringDrawPositions(key,chordtype,tuning,fingering)
					fingerPositions.append(fingerMarker)
		result = []
		for fingering,drawposition in zip(fingerings,fingerPositions):
			chordTones = []
			for entry in drawposition:
				chordTones.append(entry[2])
			result.append((drawposition,chordTones,fingering))
		console.hide_activity()
		if filters:
			return apply_filters(filters, result)
		else:
			return result
	
	
filter_constraint = {'FULL_CHORD':("R b3 3 #5 5".split(),3)}	
		
def apply_filters(filters,fingerings):
	filtered = []
	temp_fingerings = fingerings
	if not filters:
		return fingerings
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
		
					
	return temp_fingerings
	
		
	
	#given notes, return a string for tuning 
def tuningLabel(notes):
	global NOTE_NAMES
	note_string = ''
	for note in notes:
		note_range,base_note = divmod(note,12)
		note_char = re.split('/', NOTE_NAMES[base_note])[0]
		if not note_range:
			note_string += note_char
		elif note_range == 1:
			note_string += note_char.lower()
		elif note_range == 2:
			note_string += note_char.lower() + "'"
		note_string += ' '
	return note_string.strip()
	
	
# Given a fingering, gets the scale note relative to the key
def getScaleNotes(key, chordtype, tuning, fingering):
	scalenotes = []
	for i, v in enumerate(fingering):
		if v == -1:
			scalenotes.append('X')
		else:
			fingerednote = (tuning[i] + fingering[i]) % 12
			for chordrelnote in chordtype:
				chordnote = (key + chordrelnote) % 12
				if fingerednote == chordnote:
					scalenotes.append(SCALENOTES[chordrelnote])
	return scalenotes


# Finds the chord fingerings for a given tuning (number of strings implied)
# Pos is the "barre" position, span is how many frets to cover
# Returns a list of fingerings

def findFingerings(key, chordtype, tuning, pos, span, options):
	# Get valid frets on the strings
	validfrets = findValidFrets(key, chordtype, tuning, pos, span)

	# Find all candidates
	candidates = findCandidates(validfrets)


	# Filter out the invalid candidates
	candidates = filterCandidates(key, chordtype, tuning, candidates, options)

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
	for string in tuning:
		frets = []
		searchrange = range(pos, pos+span+1)
		if pos != 0: # include open strings is not at pos 0
			searchrange = [0] + searchrange
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
	#print "valid frets{}".format(validfrets)
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
	filters = currentState['filters'].filter_list
	if not filters:
		filters = ['None']
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

def filterCandidates(key, chordtype, tuning, candidates,option):
	newlist = []
	if not candidates:
		return None
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
			fingerednote = (tuning[i] + fingering[i]) % 12
			for chordrelnote in chordtype:
				chordnote = (key + chordrelnote) % 12
				if fingerednote == chordnote:
					scalenotes.append(SCALENOTES[chordrelnote])
	return scalenotes

	
# Fretboard Class

class Fretboard(ui.View): # display fingerboard and fingering of current chord/inversion/file
#note that this is instanciated by the load process.  

	def did_load(self):
		global currentState,middle_label
		self.currentstate = currentState
		self.fbWidth = int(self.bounds[2])
		self.fbHeight = int(self.bounds[3])
		self.nutOffset = 20	
		self.numFrets = 12
		self.offsetFactor = 0.1		
		self.scale = 2*(self.fbHeight - self.nutOffset) 
		self.markerRadius = 10
		self.fingerRadius = 15
		self.image = ''
		self.instrument = self.currentstate['instrument']
		self.chord = self.currentstate['chord']
		self.root = self.currentstate['root']
		self.ChordPositions = [] #set of fingerings for current chord/key/instrument/filter setting
		self.currentPosition = 0 # one currently being displayed
		self.fingerings = []
		self.loaded = True
		self.snd = self.set_needs_display
		self.chord_num = None
		self.num_chords = None
		self.nutPositions = []
				
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
		numStrings = len(self.instrument['notes'])
		offset = int(self.offsetFactor*self.fbWidth)
		return (numStrings,offset,int((self.fbWidth-2*offset)/float(numStrings-1)))
		
	def PathCenteredCircle(self,x,y,r):
		""" return a path for a filled centered circle """
		return ui.Path.oval(x -r, y -r, 2*r,2*r)		


	def draw(self):
		self.tuning = self.currentstate['instrument']
		self.root = self.currentstate['root']
		self.chord = self.currentstate['chord']
		if self.tuning:
			fretboard = ui.Path.rect(0, 0, self.fbWidth, self.fbHeight)
			ui.set_color('#4C4722')
			fretboard.fill()
		
			nut = ui.Path.rect(0,0,self.fbWidth,self.nutOffset)
			ui.set_color('#ECF8D7')
			nut.fill()
		
			ui.set_color('white')
			fretSpace = int((self.fbHeight - 2*self.nutOffset)/(self.numFrets))

			for index in range(self.numFrets):
				yFret = self.fretDistance(self.scale,index+1)
				fret = ui.Path()
				fret.line_width = 3
				fret.move_to(0,yFret)
				fret.line_to(self.fbWidth,yFret)
				fret.stroke()
		
			for index in [3,5,7,9]:		
				markeryPos = self.fretboardYPos(index)
				marker= self.PathCenteredCircle(int(0.5*self.fbWidth), markeryPos, self.markerRadius)
				marker.fill()
			
			markery12 = markeryPos = self.fretboardYPos(12)
			for xfraction in [0.25,0.75]:
				marker= self.PathCenteredCircle(int(xfraction*self.fbWidth), markery12, self.markerRadius)
				marker.fill()
		
		#assume width is 1.5" and strings are 1/8" from edge
			numStrings,offset,ss = self.stringSpacing()
			self.nutPosition = []
			ui.set_color('grey')
			for index in range(numStrings):
				xString = offset + index*ss
				string = ui.Path()
				string.line_width = 3
				string.move_to(xString,0)
				string.line_to(xString,self.fbHeight)
				string.stroke()
				self.nutPosition.append((xString,int(0.5* self.nutOffset)))
					
			if self.ChordPositions: # if there are some, draw current fingering
				self.num_chords.text = "{}".format(len(self.ChordPositions))
				self.chord_num.text = "{}".format(self.currentPosition+1)
				middle_field.text = 'of'

			 	fingering,chordTones,fretPositions = self.ChordPositions[self.currentPosition]

			 	ui.set_color('red')
			 	for string in fingering:
					x,y,chordtone,nutmarker = string

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
						               
			elif self.root and self.chord:
				sound.play_effect('Woosh_1')
				self.chord_num.text = "Try dropping"
				middle_field.text = "root, 3rd" 
				self.num_chords.text = "or 5th"


				
#####################################
# fingering positions for drawing

	def fingeringDrawPositions(self,key,chordtype,tuning,fingering):
		""" given a fingering,chord and tuning information and virtual neck info,
		    return the center positions all markers.  X and open strings will be 
		    marked at the nut"""
		scaleNotes = getScaleNotes(key, chordtype, tuning, fingering)
		self.chordPositions = []
		numStrings,offset,ss = self.stringSpacing()
		for i,fretPosition in enumerate(fingering): #loop over strings, low to high
			note = scaleNotes[i]
			atNut = None
			xpos = offset + i*ss	
			if fretPosition in [-1,0]: #marker at nut
				ypos = int(0.5* self.nutOffset) 
				if fretPosition:
					atNut = 'X'
				else:
					atNut = 'O'
			else:
				ypos = self.fretboardYPos(fretPosition)
			self.chordPositions.append((xpos,ypos,note,atNut))		
		return self.chordPositions		

	def get_instrument(self):
		return self.instrument
		
##########################################################
# instrument/tuning object
	
class Instrument(object):	
	
	def __init__(self , currentstate, items, fb):
		self.items = items
		self.currentstate = currentstate
		self.fb = fb
		self.instrument = currentstate['instrument']




		
	def __getitem__(self,key):
		try:
			return self.tuning[key]
		except:
			return None
			 
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
	def instrument_type(self): # return the type of instrument based on current selected 
		text = self.currentstate['instrument']['title']
		if re.match('^guitar',text,flags=re.I):
			return 'guitar'
		elif re.match("^mando",text,flags=re.I):
			return 'mandolin'
		else:
			return 'generic'
	
		
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
		if self.isChecked(row):
			self.items[row]['accessory_type'] = 'none'
		else:
			self.items[row]['accessory_type'] = 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row):
		global tuningDisplay
	
		self.toggleChecked(row)
		try:
			self.toggleChecked(self.tuning['row'])
		except:
			pass
		tableView.reload_data()	
		thisRow = self.items[row]
		self.tuning = {'title':thisRow['title'],
		                'notes':thisRow['notes'],
		                'span':thisRow['span'],
		                'octave':thisRow['octave'],
		                'row':row}
		self.currentstate['instrument'] = self.tuning
		

		self.filters.set_filters() 
		self.tvFilters.reload_data()

		
		fingerings = calc_fingerings(self.currentstate)
		
		self.fb.set_fingerings(fingerings)
		self.fb.set_needs_display()
		tuningDisplay.title = tuningLabel(self.tuning['notes'])
		
		
		
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
				

				
				
	def accumulateFingeringPositions(self,key,chordtype,tuning):
		self.chordFingerings = []
		for fingering in self.fingerings:
			if fingering:
				self.chordFingerings.append(self.fingeringDrawPositions(key,chordtype,tuning,fingering))


###################################################
# chord type



class Chord(object):
	
	def __init__(self , currentstate,items,fb):
		self.items = items
		self.currentstate = currentstate
		self.chord = self.currentstate['chord']
		self.fb = fb
		
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
		if self.isChecked(row):
			self.items[row]['accessory_type'] = 'none'
		else:
			self.items[row]['accessory_type'] = 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row):	
	
		self.toggleChecked(row)
		try:
			self.toggleChecked(self.chord['row'])
		except:
			pass
		tableView.reload_data()	
		self.chord = {'title': self.items[row]['title'], 'fingering': self.items[row]['fingering'], 'row':row}
		self.currentstate['chord'] = self.chord
		
		fingerings = calc_fingerings(self.currentstate)
		
		self.fb.set_fingerings(fingerings)
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
		
		

	
###################################################
# root tone


import ui

class Root(object):
	
	def __init__(self , currentstate, items,fb):
		self.items = items
		self.currentstate = currentstate
		self.root = currentstate['root']
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
		if self.isChecked(row):
			self.items[row]['accessory_type'] = 'none'
		else:
			self.items[row]['accessory_type'] = 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row):
		
		self.toggleChecked(row)
		try:
			self.toggleChecked(self.root['row'])
		except:
			pass
		tableView.reload_data()	
		self.root = {'title': self.items[row]['title'], 'noteValue': self.items[row]['noteValue'], 'row':row}
		self.currentstate['root'] = self.root
		
		fingerings = calc_fingerings(self.currentstate)
		
		self.fb.set_fingerings(fingerings)
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
	def __init__(self,currentstate,fb):
		self.currentstate = currentstate
		self.fb = fb
		self.filter_list = []
		self.items = deepcopy(FILTER_LIST_CLEAN)
		
	def set_filters(self):
		self.filter_list = []
		self.items = deepcopy(FILTER_LIST_CLEAN)
		it = self.instrument.instrument_type()
		if it == 'guitar':
			self.items = self.items + deepcopy(GUITAR_LIST_CLEAN) 
		elif it == 'mandolin':
			self.items = self.items + deepcopy(MANDOLIN_LIST_CLEAN)
		else: # generic
			pass
		for item in self.items:
			item['accessory_type'] = 'none'
			
	
	def reconsile_filters(self,filter):
		if filter in FILTER_MUTUAL_EXCLUSION_LIST.keys():
			
			exclude = FILTER_MUTUAL_EXCLUSION_LIST[filter]
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
		if self.isChecked(row):
			self.items[row]['accessory_type'] = 'none'
		else:
			self.items[row]['accessory_type'] = 'checkmark'

	def offChecked(self,row):
		self.items[row]['accessory_type'] = 'none'
		
	def onChecked(self,row):
		self.items[row]['accessory_type'] = 'checkmark'

##############################################
# action for select
		
	def tableview_did_select(self,tableView,section,row):	
	
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
		self.currentstate['filters'] = self.filter_list
		fingerings = calc_fingerings(self.currentstate)
		self.fb.set_fingerings(fingerings)
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
	if os.path.exists('waves'):
		cc = fretboard.ChordPositions[fretboard.currentPosition]
		frets = cc[2]
		dead_notes = [item[3] == 'X' for item in cc[0]]
		strings = currentState['instrument']['notes']
		baseOctave = currentState['instrument']['octave']
		tones = []
		for fret,string,dead_note in zip(frets,strings,dead_notes):
			if  dead_note:
				continue
			octave,tone = divmod(string + fret,12) 
			tones.append((tone,octave+baseOctave))
		for tone,octave in tones:
			waveName = 'waves/' + NOTE_FILE_NAMES[tone] + "{}.wav".format(octave)
			sound.play_effect(waveName)
			time.sleep(0.05)
			if button.name == 'button_arp':
				time.sleep(0.5)
	

def play_tuning(button):
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
			waveName = 'waves/' + NOTE_FILE_NAMES[tone] + "{}.wav".format(octave)
			sound.play_effect(waveName)
			time.sleep(0.6)



##############################################
if __name__ == "__main__":	
	if not os.path.exists('waves'):
		console.alert('waves sound files not present, run makeWave.py')
		sys.exit(1)
	currentState = {'root':None,'chord':None,'instrument':None,'filters':None}	
	mainView = ui.load_view()
	num_chords = mainView['num_chords']
	chord_num = mainView['chord_num']
	middle_field = mainView['label_middle']
	fretboard = mainView['fretboard']
	tvRoot = mainView['tableview_root']
	root_list = deepcopy(ROOT_LIST_CLEAN)
	root = Root(currentState,root_list,fretboard)
	tvRoot.data_source = tvRoot.delegate = root
	
	tvType = mainView['tableview_type']
	chord_list = deepcopy(CHORD_LIST_CLEAN)
	chord = Chord(currentState,chord_list,fretboard)
	chord.reset()
	tvType.data_source = tvType.delegate = chord
	
	tvInst = mainView['tableview_inst_tune']
	tuningDisplay = mainView['button_tuning']
	tuningDisplay.title = ''
	tuningDisplay.action = play_tuning

	# fretboard is a custom view and is instanciated by the ui.load_view process
	tuning_list = deepcopy(TUNING_LIST_CLEAN)
	instrument = Instrument(currentState,tuning_list,fretboard)
	instrument.reset()
	tvInst.data_source = tvInst.delegate = fretboard.instrument = instrument
	
	tvFilters = mainView['tableview_filters']
	filter_list = deepcopy(FILTER_LIST_CLEAN)
	filters = Filters(currentState,fretboard)
	instrument.tvFilters = tvFilters
	instrument.filters = filters
	filters.instrument = instrument
	tvFilters.data_source = tvFilters.delegate = filters
	currentState = {'root':root,'chord':chord,'instrument':instrument,'filters':filters}
	fretboard.set_chordnum(chord_num,num_chords)
	
	mainView['button_arp'].action = play
	mainView['button_chord'].action = play
	
	mainView['button_up'].action = mainView['button_down'].action = onPrevNext
	
	mainView.present()

