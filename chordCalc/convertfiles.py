#rename file
import os,sys,os.path

enharmo = {"Ab":"Gs",
           "Bb":"As",
           "Db":"Cs",
           "Eb":"Ds",
           "Gb":"Fs",
           }
           
folders = ['banjo','guitar','bass']

print enharmo

for folder in folders:
	path = os.path.join("waves",folder)
	files = os.listdir(path)
	newname = ""
	for i,file in enumerate(files):
		if file[0:2] in enharmo.keys():
			newname = "{}_{}".format(enharmo[file[0:2]],file[2:])
		else:
			newname = "{}_{}".format(file[0], file[1:])
		src = os.path.join(path,file)
		dst = os.path.join(path,newname)
		os.rename(src, dst)


