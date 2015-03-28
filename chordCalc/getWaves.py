# get waves.  This scrtipt downloads from github a set of soundfiles that are the notes for
# designated instruments.  Thay are places after appropriate renaming, into subdirectories in the 
# waves folder.

import urllib2, os, os.path, bs4,sys
import re
from shutil import copyfileobj

import bs4, requests


enharmo
 = {"Ab":"Gs",
           "Bb":"As",
           "Db":"Cs",
           "Eb":"Ds",
           "Gb":"Fs",
           }

def get_mp3_from_urlpath(urlpath,url_file,outdir,out_file):
	""" gets raw file from github heirarchy"""
	fmt = '{}/{}?raw=true'
	url = fmt.format(urlpath.replace('/tree/', '/blob/'),url_file)
	fullFilePath = os.path.join(outdir,out_file)
	print "writing ",fullFilePath,
	with open(fullFilePath, 'wb') as out_file:
		out_file.write(requests.get(url).content)
	print "...Done\n\n"

baseurl  = "https://github.com/polymerchm/midi-js-soundfonts/tree/master/FluidR3_GM" # forked from gleitz account
dirs = {
        'acoustic_guitar_steel-mp3':	'guitar',
        'acoustic_bass-mp3':					'bass',
        'banjo-mp3':									'banjo',
        'pizzicato_strings-mp3':			'pizzicato',
        'tremolo_strings-mp3':				'tremolo',
        }


if not os.path.exists('waves'):
	try:
		os.mkdir('waves')
	except:
		print "can't create base directory, abort"
		sys.exit(1)


soup = bs4.BeautifulSoup(requests.get(baseurl).text)
for link in soup.find_all('a'):
	dir = link.get('href')
	dir_unesc = urllib2.unquote(dir)
	head,tail = os.path.split(dir_unesc)
	if tail in dirs.keys():
		dir = dirs[tail]
		try:
			os.mkdir('waves/'+dir)
			print 'created directory for '+dir
		except:
			print "could not create {} subdirectory".format(dir)
			sys.exit(1)
			
		fileurl = os.path.join(baseurl,os.path.split(dir_unesc)[1])
		response = urllib2.urlopen(fileurl)
		html = response.read()
		soup2 = bs4.BeautifulSoup(html)
		for link2 in soup2.find_all('a'):
			file = link2.get('href')
			if (file != '/' and file.endswith('.mp3')):
				_,file_unesc = os.path.split(urllib2.unquote(file))			
				filename = os.path.join(fileurl,file_unesc)
				if file_unesc[0:2] in enharmo.keys():
					outname = enharmo[file_unesc[0:2]] + "_" + file_unesc[2:]
				else:
					outname = file_unesc[0] + "_" + file_unesc[1:]
				get_mp3_from_urlpath(fileurl,file_unesc,os.path.join('waves',dir),outname)
					
					

