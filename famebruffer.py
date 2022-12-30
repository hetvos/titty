'''
Python raw framebuffer library (for Linux)
Copyright @raspiduino 2020
Date created 8:30 PM 31/12/2020
'''

import os
import mmap # Memory map library
import vmap

class Framebuffer():
	'''
	Framebuffer class
		Varriables:
			screenx: x screen size
			screeny: y screen size
			bpp    : Bit per pixel
			fbpath : Framebuffer path
			fbdev  : Framebuffer opened as normal file
			fb     : Framebuffer memory mapped object
		Functions:
			__init__ : init function
			drawpixel: function to draw a single pixel
			clear    : function to clear the screen

	'''
	def __init__(self, fbpath="/dev/fb0"):
		'''
		__init__ function
		Optional: Require frame buffer path. Default is /dev/fb0
		'''
		# Get screen size
		_ = open("/sys/class/graphics/fb0/virtual_size", "r")
		__ = _.read()
		self.screenx,self.screeny = [int(i) for i in __.split(",")]
		_.close()

		# Get bit per pixel
		_ = open("/sys/class/graphics/fb0/bits_per_pixel", "r")
		self.bpp = int(_.read()[:2])
		_.close()

		# Open the framebuffer device
		self.fbpath = fbpath
		self.fbdev = os.open(self.fbpath, os.O_RDWR)

		# Map framebuffer to memory
		self.realfb = mmap.mmap(self.fbdev, self.screenx*self.screeny*self.bpp//8, mmap.MAP_SHARED, mmap.PROT_WRITE|mmap.PROT_READ, offset=0)
		self.fb = vmap.vmap(self.screenx*self.screeny*self.bpp//8)

	def drawpixel(self, x, y, r, g, b, t=0):
		'''
		drawpixel function
		Draw a single pixel with color
		Require:
			x: x coordinate of the pixel
			y: y coordinate of the pixel
			
			RGB color:
				r: Red color (0 -> 255)
				g: Green color (0 -> 255)
				b: Blue color (0 -> 255)

			t: transparency (default set to 0)
		'''
		self.fb.seek((y*self.screenx+x)*(self.bpp//8)) # Set the pixel location

		if self.bpp == 32:
			# 32 bit per pixel
			self.fb.write(b.to_bytes(1, byteorder='little')) # Write blue
			self.fb.write(g.to_bytes(1, byteorder='little')) # Write green
			self.fb.write(r.to_bytes(1, byteorder='little')) # Write red
			self.fb.write(t.to_bytes(1, byteorder='little')) # Write transparency

		else:
			# 16 bit per pixel
			self.fb.write(r.to_bytes(1, byteorder='little') << 11 | g.to_bytes(1, byteorder='little') << 5 | b.to_bytes(1, byteorder='little'))

	def flush(self):
		self.realfb.seek(0)
		self.realfb.write(bytes(self.fb.byteobj[:self.fb.size]))
		self.realfb.flush()

	def clear(self, r=255, g=255, b=255, t=0):
		'''
		clear function
		Clear the screen with color
		Require:
			RGB color:
					r: Red color (0 -> 255)
					g: Green color (0 -> 255)
					b: Blue color (0 -> 255)

			t: transparency (default set to 0)
		'''
		self.fb.seek(0)
		self.fb.write((b.to_bytes(1, byteorder='little')+
					   g.to_bytes(1, byteorder='little')+
					   r.to_bytes(1, byteorder='little')+
					   t.to_bytes(1, byteorder='little'))
					   * self.screenx * self.screeny)
	
	def horline_until_end(self, x,y,r=255,g=255,b=255,t=0,width=1,length=None):
		if length == None: length = self.screenx - x
		for i in range(0,width):
			self.fb.seek(((y+i)*self.screenx+x)*(self.bpp//8)) # Set the pixel location
			self.fb.write((b.to_bytes(1, byteorder='little')+
						   g.to_bytes(1, byteorder='little')+
						   r.to_bytes(1, byteorder='little')+
						   t.to_bytes(1, byteorder='little'))
						   * length)

	
	def clear_from(self, y, r=255, g=255, b=255, t=0):
		'''
		clear function
		Clear the screen with color
		Require:
			RGB color:
					r: Red color (0 -> 255)
					g: Green color (0 -> 255)
					b: Blue color (0 -> 255)

			t: transparency (default set to 0)
		'''
		self.fb.seek((y*self.screenx)*(self.bpp//8))
		self.fb.write((b.to_bytes(1, byteorder='little')+
					   g.to_bytes(1, byteorder='little')+
					   r.to_bytes(1, byteorder='little')+
					   t.to_bytes(1, byteorder='little'))
					   * self.screenx * (self.screeny-y))

import sys
import monobit
import string

fb = Framebuffer("/dev/fb0")


from itertools import chain

font = {}

for char in monobit.load("./terminus.yaff")[0].glyphs:
	font[char.char.value] = bytes(char.as_text(),"utf-8").split(b"\n")
	font[char.char.value].remove(b"")
	
	#l = list(chain(*char.as_matrix()))
	#for i in range(0,6*12):
	#	if l[i] == 1: font[char.char.value].append([i%6,i//6])

font[" "] = [b"."*6]*12

#print(font)

#from ter import ter as font

def dpx_scale(s,x,y,r,g,b,t=0):
	for ys in range (0,s):
		for xs in range(0,s):
			fb.drawpixel(x*s+xs,y*s+ys,r,g,b,t)

from p256colors import p256colors

class FbOutFile:
	def __init__(self,font,scale,color):
		self.font = font
		self.scale = scale
		self.colorscheme = color
		self.color = self.colorscheme[15]
		self.bgcolor = self.colorscheme[0]
		fb.clear(*self.bgcolor)
		self.fonth = 12
		self.fontw = 6
		self.hspace = 0
		self.scrollregion = [1,fb.screeny//self.fonth]
		self.x = 0
		self.y = 0
		self.waitforeseq = False
		self.curreseq = ""
		self.lastchar = ""
		fb.flush()

	def writechar(self,char,x,y):
		bgcolor = self.ctb(self.bgcolor)
		color = self.ctb(self.color)
		char = font[char]
		for i in range(0,self.fonth):
			line = char[i]
			line = line.replace(b".",bgcolor).replace(b"@",color)
			fb.fb.seek(((y+i)*fb.screenx+x)*(fb.bpp//8))
			fb.fb.write(line)
	
	def write(self,text):
		charc = 0
		for char in text:
			if not self.waitforeseq:
				if char == "\n":
					self.y += self.fonth
					if self.y >= self.scrollregion[1]*self.fonth:
						self.y = (self.scrollregion[1]-1)*self.fonth
						fb.fb.move((self.scrollregion[0]-1)*self.fonth*fb.screenx*(fb.bpp//8), self.scrollregion[0]*self.fonth*fb.screenx*(fb.bpp//8), (len(range(*self.scrollregion))*self.fonth)*fb.screenx*(fb.bpp//8))
						fb.fb.seek((self.y*fb.screenx)*(fb.bpp//8))
						fb.fb.write(self.ctb(self.bgcolor) * fb.screenx * self.fonth)
					self.x = 0
				elif char == "\r":
					self.x = 0
				elif char == "\b":
					self.x -= self.fontw
				elif char == "\x1b":
					self.waitforeseq = True
				elif char in ["\0", "\a"]:
					pass
				else:
					try:
						self.writechar(char,self.x,self.y)
						charc += 1
					except Exception as e:
						pass
						#print(e,file=sys.stderr)
					self.x += (self.fontw + self.hspace)
					self.lastchar = char
			else:
				self.curreseq += char
				print(self.curreseq,file=sys.stderr)
				if self.curreseq[0] != "]" and (char in string.ascii_letters+"=\\%" or self.curreseq in [" 7"," 8",")0"]) or char in ["\x07","R"]:
					if self.curreseq.startswith("("):
						pass
					elif self.curreseq == "[H":
						self.x = 0
						self.y = 0
					elif char in ["H","f"] and self.curreseq[0] == "[":
						line, col = self.curreseq.strip("[Hf").split(";")
						self.x = (int(col)-1) * self.fontw
						self.y = (int(line)-1) * self.fonth
					elif char == "d" and self.curreseq[0] == "[":
						line = self.curreseq.strip("[d")
						self.y = (int(line)-1) * self.fonth
					elif char == "A":
						arg = self.curreseq.strip("[ABCDZ")
						if arg == "": arg = "1"
						self.y -= min(self.y,int(arg)*self.fonth)
					elif char == "B":
						arg = self.curreseq.strip("[ABCDZ")
						if arg == "": arg = "1"
						self.y = min(self.y + int(arg)*self.fonth, fb.screeny)
					elif char == "C":
						arg = self.curreseq.strip("[ABCDZ")
						if arg == "": arg = "1"
						self.x = min(self.x + int(arg)*self.fontw, fb.screenx)
					elif char == "D":
						arg = self.curreseq.strip("[ABCDZ")
						if arg == "": arg = "1"
						self.x -= min(self.x,int(arg)*self.fontw)
					elif char == "Z":
						arg = self.curreseq.strip("[ABCDZ")
						if arg == "": arg = "1"
						self.x -= min(self.x,int(arg)*self.fontw)	
					elif self.curreseq in ["[K","[0K"]:
						fb.horline_until_end(self.x,self.y,*self.bgcolor,width=self.fonth)
					elif self.curreseq == "[2K":
						fb.horline_until_end(0,self.y,*self.bgcolor,width=self.fonth)
					elif char == "m" and not ">" in self.curreseq and self.curreseq[0] == "[":
						args = self.curreseq.strip("[m").split(";")
						for arg in args:
							if arg == "": arg = 0
							else: arg = int(arg)

							if arg >= 30 and arg <= 37:
								self.color = self.colorscheme[arg-30]
							if arg >= 90 and arg <= 97:
								self.color = self.colorscheme[arg-82]
							elif arg == 38:
								try:
									fmt = int(args.pop(1))
									r = int(args.pop(1))
									if fmt == 5 and r <= 15:
										self.color = self.colorscheme[r]
									elif fmt == 5 and r >= 16:
										self.color = p256colors[r-16]
									elif fmt == 2:
										g = int(args.pop(1))
										b = int(args.pop(1))
										self.color = (r,g,b)
								except:
									pass
							elif arg == 39:
								print("set color 39",file=sys.stderr)
								self.color = self.colorscheme[15]
							elif arg >= 40 and arg <= 47:
								self.bgcolor = self.colorscheme[arg-40]
							elif arg >= 100 and arg <= 107:
								self.bgcolor = self.colorscheme[arg-92]
							elif arg == 48:
								try:
									fmt = int(args.pop(1))
									r = int(args.pop(1))
									if fmt == 5 and r <= 15:
										self.bgcolor = self.colorscheme[r]
									elif fmt == 5 and r >= 16:
										self.bgcolor = p256colors[r-16]
									elif fmt == 2:
										g = int(args.pop(1))
										b = int(args.pop(1))
										self.bgcolor = (r,g,b)
								except:
									pass
							elif arg == 49:
								print("set color 49",file=sys.stderr)
								self.bgcolor = self.colorscheme[0]
							elif arg == 1:
								pass
							elif arg == 0:
								self.color = self.colorscheme[15]
								self.bgcolor = self.colorscheme[0]
					elif self.curreseq in ["[J","[0J"]:
						fb.horline_until_end(self.x,self.y,*self.bgcolor,width=self.fonth)
						if self.y//self.fonth < fb.screeny//self.fonth: fb.clear_from(self.y+self.fonth,*self.bgcolor)
					elif self.curreseq == "[2J":
						fb.clear(*self.bgcolor)
					elif char == "b":
						num = int(self.curreseq.strip("[b"))
						self.curreseq = ""
						self.waitforeseq = False
						sys.stdout.write(self.lastchar*num)
					elif char == "r":
						args = self.curreseq.strip("[r")
						if args == "": self.scrollregion = [1,fb.screeny//self.fonth]
						elif len(args.split(";")) == 2: self.scrollregion = [int(args.split(";")[0]),int(args.split(";")[1])]

					self.curreseq = ""
					self.waitforeseq = False
		fb.flush()
		fb.realfb.seek(((self.y+11)*fb.screenx+self.x)*(fb.bpp//8))
		fb.realfb.write(self.ctb(self.color)*6)
		fb.realfb.flush()
		return charc

	def ctb(self,color):
		return color[2].to_bytes(1,"little")+color[1].to_bytes(1,"little")+color[0].to_bytes(1,"little")+b'\x00'

	def flush(self):
		fb.flush()


sys.stdout = FbOutFile(font,1,[(0x17,0x15,0x19), (0xbf,0x33,0x57), (0x4b,0x8e,0x3f), (0xd3,0x86,0x4c), (0x23,0x6c,0xaa), (0x9d,0x56,0xb2), (0x46,0x8b,0x96), (0x84,0x7e,0x90), (0x27,0x23,0x2b), (0xee,0x69,0x8b), (0x85,0xc9,0x78), (0xe8,0xa2,0x6c), (0x5e,0x99,0xcc), (0xb9,0x83,0xc9), (0x87,0xb6,0xbd), (0xf6,0xf4,0xff)])
