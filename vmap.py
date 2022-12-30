class vmap:
	def __init__(self,size):
		self.size = size
		self.byteobj = bytearray(size)
		self.position = 0
	def seek(self,pos):
		self.position = pos
	def move(self,dest,src,count):
		self.byteobj[dest:dest+count] = self.byteobj[src:src+count]
	def write(self,content):
		self.byteobj[self.position:self.position+len(content)] = content
		self.position += len(content)
	def flush(self):
		pass
