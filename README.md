chordcalc Version 4.0
=================

Turning  Gek S. Low's chordcalc python script into a full-featured chord calculator/player 
Updated to be a full featured stringed instrument chord analysis tool by Steven K Pollack




- **makeWaves.py**

generates a set of 96 2 second wave files  used by chordcalc.py to play the sound of the notes.

- **getWaves.py**

downloads realistic sounds from github

- **chordcalc.py**

- **chordcalc_constants.py**

- **debugStream.py**

- **Spinner.py**

- **Shield.py**

The new features in 4.0 are:
	
- constants can now be reloaded. No longer "globals"

- Chord, Capo, Filter and Instrument Tableviews can be edited to re-order or delete rows

- The current configuration of the tables can be saved or the "factory standard" restored

- The current settings for chord, capo and filters can be saved under/loaded from a named setting.  The settings list can be edited.

- Sweep gestures and long-touch on the fingerboard are enabled

- sounds will now try to use "realistic sounds" if they have been downloaded using getWaves.py

*Editing the Tables*

The labels of the editable tables are actually buttons that enable/disable deleting rows or re-ordering each editable table.  If you wish to save this new "configuration", you hit the "Config" button.  It will give you the option of saving the current setup, or restoring the "factory setting"  (from the file chordcalc_constants.py).  The configuration is stored as a json object in the file "config.ini"

*Saving the Settings*

The Save and Load buttons allow the user to save the current instrument, filters and capos as a named entry in the "Settings" list.  If an existing default setting is changed, the user is prompted to confirm the overwrite.  There also the option to edit the list (delete rows/reorder). The data for this list is stored in a file called "settings.ini"

*Instrument Editor*

Hitting the New button on the main menu brings up an instrument editor.  It will take the current selected instrument/tuning and allow you to adjust the tuning.  You can then save this to the Intrument/tuning list.  You will be forced to use a new name.  If you want to delete it later, you can edit the intrument/tuning list to remove it.  To have this intrument saved fo rhte next time you run chord calc, hit the "config" button to save it.  


*Capos:*

The list (lower right hand corner) allows the user to select one or more capos. When you select a capo, you are prompted for a fret to place it.  All subsequent operations acccount for the presence of the capos.  The full capo will adjust to the number of strings (except 5-string banjo, see below)  A partial capo will only fret a subset of strings.  As supplied these assume a 6-stringed instrument.  The standard partial capos predefined are the "drop E" capo that only covers 5 consecutive guitar strings (when placed on the second fret, accomplishes a drop D tuning, up a tone without retuning) and the "sus2" capo (covers the "ADG" strings or the "DGB" strings of a guitar).  Five string banjo capos are one for the "normal" four strings and a one strng capo for the 5th string.  Multiple capos are allowed.  

There are three modes of operation: Calc, Identify and Scale.  These are selected by the C, I and S buttons.  The active mode is highlighted

*Calc Mode:*

Select an instrument/tuning (upper right-hand corner), a root (key) (left-most side) and a chord type, (second column on left), and all possible fingerings will be displayed on the fretboard.  You cycle through them with the up and down arrows.  

**New Feature**.  If you sweep up or down the fretboard, it will "fast forward" the chords in proportion to the distance you sweep.  If you sweep across, it will jump in smaller increments.  If you do a long-touch (> 1/2 second), the present chords will jump to the closest chord to that fret. 

By choosing various filters (center right-hand list), you can  reduce the number and type of chords displayed. For example, 'LOW_3' is a mandolin filter that only presents chords played on the lower 3 strings and leaves the high E string unplayed.  The 'DOUBLE_STOP' filter (also for mandolin) will show all valid double stops for a given chord (2 note chord partials). 'NO_DEAD' will only show chords where every string is sounded.  

If a given instrument/tuning cannot represent the chord,  an appropriate offensive noise is sounded and message is displayed.  The filters NO_ROOT, NO_3RD and NO_5TH will find chord shapes for 
mandolin (you notice the mandolin emphasis here) that allows those chord tones not to be 
ignored in testing for valid fingerings.  On mandolins, and other 4 stringed instrumetns, the player often abandons the root, 5th or 3rd.

Hitting the chord button will play the chord (see makeWaves.py above).  Hitting the arpeggio button will play the notes one by one. Hitting the button which describes the individual string tunings will play the sound of the instrument when un-fretted (when a capo(s) is applied, it effects the tones appropriately)

The slider at the bottom is a volume control and the slider at the top determines the "speed" of the arpeggio.

For any chord, touching the fretboard will display all of the chordtones on the entire fretboard.  Touching it again displays the current chord.

The chord tones and notes are displayed in the upper right 

*Identify mode*

In identify mode, you touch the fingerboard to indicate a fingering  When you hit Find, all possible "names" for the chord are given.  If the fingering is a chord partial, then the missing chord tones are indicated.  If there are capos, you will be prevented from fretting "behind" the capo.

*Scale Mode*

In scale mode, you select a key (the root) and the scale type (second column on left).  All notes on the scale across the entire fretboard are displayed.  If you touch a root position, a two octave display is highlighted.  Hitting the scale button plays the scale.  The speed/volume sliders are also effective here.  If the mode is one of the greek modes, then the base key is displayed in the upper right hand corner (for example, A Aoelian is based on C Ionian (major), A Dorian is actually the key of G Ionian (major)). Every effort is made to have the appropriate anharmonics (sharps or flats) display based on the  key signature (or for the greeek modes, its base).  You can toggle the display between scale notes and scale degrees and, for "ambiguous" key signatures (like A#/Bb), you can toggle anharmonic notes between sharps and flats.  **New Feature**.  A Spinner is presented to allow for different modes of calculating a 2 0ctave scale.  This is experimental at this point.  


- **debugStream.py** 

is a handy class for creating output that doesn't bog down the pythonista console which can slow debugging down.  

Usage:

```python
out = debugStream()

out.push("this {} is formated to here {}",'string1','string2')
.
.
.
.
out.send()
```

first parameter is the format string that would be used with the `.format` method.  Any number of arguments that correspond to fields in the format string can follow.

- **Spinner.py**

is a custom view class that creates a spinner view, consisting of a value field and and up/down button pair.  The spinner values can be scalar (int/float) or lists.  In the former case, you can specify an increment that represents the effect of the buttons and limits that prevent the buttons from going past the limits.  You can associate two actions, one for a successful button push (before reaching a limit) and one that fires when you push a button at a limit.  You can set/get value or position in a  list.

Usage:
	
```
	spinner = Spinner(name='spinner',  # useful for dictionary type reference to subview
										initialValue= 10, # can be a list or tuple
										limits=(0,100),   # only relevant for scalar 
										action=None, # done if action was successful
										limitAction=None, #done if hit a limit
										textFraction = 0.75, # for width of spinner, defines portion that value field occupies
										fontSize = 12,       # font size of displayed value (system font)
										spinnerSize=(80,80)  # width,height of spinner
	                  )
	spinner.position = (200,200)	# positions spinner in containing view. 
	where = spinner.position			# returns current position
	fred = spinner.value 					# returns current value
	spinner.value = 25 						# sets current value
	spinner.increment = 2					# sets increment
	spinner.pointer = 5						# set where in a list value to display
	index = spinner.pointer				# returns the pointer
```

- **Shield.py**

is a custom view that creates a translucent "shield" to prevent views behind it from being responsive to touches.  Simplifying having only the topmost view respond to touches.  

```
v = ui.View(frame=(0,0,500,500))
vShield = Shield(v)  # created a shield instance the size and position of the argument view
v.present()
vShield.conceal()   # turns on the shield
vShield.reveal()    #turns off the shield
vShield.isActive()  # returns that status
vShield.delete()		# destroys the shield object.
```

Have fun
