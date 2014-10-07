class debugStream():
	""" create buffered output to speed up console printing"""
	def __init__(self):
		self.out = ''
		
	def push(self,string,*args):
		string += '\n'
		self.out += string.format(*args)
	
	def send(self):
		print self.out
		self.out = ''
