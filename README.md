chordcalc
=========

Turning  Gek S. Low's chordcalc python script into a full-featured chord calculator/player 
Updated to be a full featured stringed instrument chord analysis tool by Steven K Pollack

- **makeWaves.py**


generates a set of 96 2 second wave files  used by chordcalc.py to play the sound of the notes.

- **chordcalc.py**

- **chordcalc_constants.py**

- **debugStream.py**



*calc mode:*



Select an instrument/tuning, a root (key), and a chord type, and all possible fingerings will be displayed on the fretboard.
You cycle through them with the up and down arrows.  By choosing various filters, you can  reduce the number and type of chords of  chords displayed.
For example, LOW_3 is a mandolin filter that only presents chords played on the lower 3 strings and leaves the high E string
unplayed.  The "DOUBLE_STOP' filter (also for mandolin) will show all valid double stops for a give chord (2 note chord partials).
'NO_DEAD' will only show chords where every string is sounded.  

If a given instrument/tuning cannot represent the chord an appropriate ofensive noise and message is displayed.  
The filters NO_ROOT, NO_3RD and NO_5TH will find chord shapes for 
mandolin (you notice the mandolin empahsis here) that allow the those chord tones not to be 
ignored in testing for vaid fingerings.  On mandolins, and other 4 stringed instrumetns, the player often abandons the root, 5th or 3rd.

Hitting the chord button will play the chord (see makeWaves.py above).  Hitting the arpeggio button will play the notes one by one.
Hitting the button which describes the individual string tunings will play the sound of the instrument when un-fretted.

*Identify mode (new)*


Switching modes by hitting the ident or calc button  changes the operation.  In identify mode, you touch the fingerboard to indicate a fingering 
When yo hit FInd, all possible "names" for the chord are given.  If the fingering is a chord partial, then the missing chord 
tones are indicated.  

You can add new instruments/tunings in the chordcalc_constants.py file.  

- **debugStream.py** 

is a handy class for creating output that doesn't bog down the pythonista console and slow debuging down.  

Usage:

```
out = debugStream()

out.push("this {} is formated to here {}",'string1','string2')
.
.
.
.
out.send()
```

first parameter is   string that would be used with the `.format` method.  Any number of arguments that correspond to fields in the format string can follow.



Have fun
