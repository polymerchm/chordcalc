#Sheild 
# covers the designated view to suppress touch events. 

import ui

class Shield(object):
	def __init__(self,view,tint=(1.0, 1.0, 1.0),alpha=0.7,local=False): # view is view to cover
		self.view = view
		self.shield = ui.View(frame=view.frame,background_color=tint,flex='WH',name='shield')
		self.shield.alpha = alpha
		self._frame = self.shield.frame
		self._position = (self._frame[:2])
		if local:
			self.view.add_subview(self.shield)
		else:
			self.view.superview.add_subview(self.shield)
		self.shield.send_to_back()
		self.shield.hidden = True
		self.status = False
		
	def isActive(self):
		return self.status

	@property
	def position(self):
		return self._position
		
	@position.setter
	def position(self,input):
		self._position = input
		self._frame = (input[0],input[1],self._frame[2],self._frame[3])
		self.shield.frame = self._frame

	def conceal(self): # ui seems to ignore multiple requests to add the same subview.  Good.
		self.status = True
		self.shield.bring_to_front()
		self.shield.hidden = False

	def reveal(self): #ui is also happy to ignore requests to remove an non-existant subview.  Also good.
		self.status = False
		self.shield.send_to_back()
		self.shield.hidden = True



if __name__ == '__main__':

	class LDS(ui.ListDataSource):
		def __init__(self,items=None):
			super(LDS,self).__init__(items)

		def tableview_did_select(self,tv,section,row):
			t1.text = self.items[row]

	def shieldsUp(sender):
		s1.conceal()
		s2.conceal()
	def shieldsDown(sender):
		global s1
		s1.reveal()
		s2.reveal()


	v = ui.View(frame=(0,0,600,600),name='main')

	tv = ui.TableView(name='tv')
	lds = LDS(items='one two three four five'.split())
	tv.data_source = tv.delegate = lds
	v.add_subview(tv)
	tv.frame=(10,10,400,500)

	b1 = ui.Button(frame=(450,10,100,50),
				   background_color = 'white',
				   title = 'Shields up!',
				   )
	b2 = ui.Button(frame=(450,100,100,50),
				   background_color = 'white',
				   title = 'Shields down',
				   )
	b1.action = shieldsUp
	b2.action = shieldsDown

	v.add_subview(b1)
	v.add_subview(b2)

	t1 = ui.TextView()
	v.add_subview(t1)
	t1.frame=(100,550,200,30)
	t1.text = 'READY'
	s1 = Shield(tv)
	s2 = Shield(t1)

	v.present('sheet')
	v.wait_modal()

