import pygame,sys,random
from pygame.locals import *

PG = 20
GR = 50
GD = 150
BD = 350
GR_G = 0.5
BD_G = -2
PR_G = -6

class BMSData(object):
	#self.wavdict : sound file dict
	#self.data : data section w/o bgm data
	#self.bgm : bgm data section.
	def __init__(self, filename):
		f = open(filename, 'r')
		lines = f.readlines()
		f.close()
		prp_data = []
		isignored = False

		#Preprocessor
		for line in lines:
			(c, _, parameter) = line.partition(' ')
			command = c.upper()
			if command == "#RANDOM":
				randnum = random.randrange(1, int(parameter)+1)
			elif command == "#IF":
				if int(parameter) != randnum:
					isignored = True
			elif command == "#ELSE":
				if isignored == True:
					isignored = False
				else:
					isignored = True
			elif command == "#ENDIF":
				ifignored = False
			elif isignored == False and line[0] == '#':
				prp_data.append(line)
		del lines
		del isignored

		#Read header section, and extract data section
		pygame.mixer.pre_init(channels = 2,buffer=512000,frequency=44100)
		pygame.mixer.init()
		pygame.mixer.set_num_channels(32)
		self.wavdict = {}
		datalist = []
		self.title,self.artist,self.genre,self.playlevel,self.startbpm,self.rank='','','',0,130,3
		for line in prp_data:
			if line[-2:] == "\r\n":
				line = line[:-2]
			else:
				line = line[:-1]
			(c, _, parameter) = line.partition(' ')
			command = c.upper()
			if _ == " ":
				if command == "#PLAYER":
					if parameter == "1":
						self.issingle = True
					else:
						self.issingle = False
				elif command == "#TITLE":
					self.title = parameter
				elif command == "#ARTIST":
					self.artist = parameter
				elif command == "#GENRE":
					self.genre = parameter
				elif command == "#PLAYLEVEL":
					self.playlevel = int(parameter)
				elif command == "#BPM":
					self.bpm = float(parameter)
				elif command == "#RANK":
					self.rank = int(parameter)
				elif command[:4] == "#WAV":
					self.wavdict[command[4:]] = pygame.mixer.Sound(parameter)
			else:
				if line[7:] == "00":
					continue
				else:
					datalist.append(line)
		del prp_data

		#parse data section
		self.data = []
		eventchannel = ['1']
		for i in range(1000):
			self.data.append([])
		for line in datalist:
			if line[4] == "0":
				if line[5] in eventchannel:
					self.data[int(line[1:4])].append(line[4:])
			else:
				self.data[int(line[1:4])].append(line[4:])
		del datalist
		for a in reversed(range(1000)):
			if self.data[a] == []:
				self.data.pop()
			else:
				break
		
		self.bgmlist = []
		self.keylist = [[],[],[],[],[],[],[],[]]
		for measure in range(len(self.data)): #parse bgm section
			self.data[measure].sort()
			for b in range(len(self.data[measure])):
				if self.data[measure][b][:2] == "01":
					self.bgmlist.extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "11":
					self.keylist[1].extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "12":
					self.keylist[2].extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "13":
					self.keylist[3].extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "14":
					self.keylist[4].extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "15":
					self.keylist[5].extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "18":
					self.keylist[6].extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "19":
					self.keylist[7].extend(self.__calctime(measure, self.data[measure][b][3:]))
				elif self.data[measure][b][:2] == "16":
					self.keylist[0].extend(self.__calctime(measure, self.data[measure][b][3:]))
		self.bgmlist.sort(key=lambda tup: tup[0])
		for n in range(8):
			self.keylist[n].sort(key=lambda tup: tup[0])
			self.keylist[n].append([-1,"00"])
		for measure in range(len(self.data)):
			l = self.data.pop(measure)
			l_ = []
			for line in l:
				if line[:2] != "01":
					l_.append(line)
			self.data.insert(measure,l_)

	def __calctime(self, measure, data):
		gap = measure*240000//self.bpm
		divider = len(data)//2
		times = []
		for a in range(divider):
			note = data[2*a:2*a+2]
			if note != "00":
				times.append([int(gap+a*240000//divider//self.bpm),note])
		return times

	def keypress(self,time,linenum,preindex):
		preindex = 0
		while len(self.keylist[linenum])>2 and abs(self.keylist[linenum][preindex][0]-time) > abs(self.keylist[linenum][preindex+1][0]-time):
			preindex += 1
		#if preindex < len(self.keylist[linenum]) and self.keylist[linenum][preindex][0]-time < -1*BD:
		#	preindex += 1
		try:
			print(self.keylist[linenum][preindex])
		except:
			preindex -= 1
		else:
			if self.keylist[linenum][preindex][1] != "00":
				self.wavdict[self.keylist[linenum][preindex][1]].stop()
				self.wavdict[self.keylist[linenum][preindex][1]].play()
		return preindex

class BMSView(object):
	beamF = [0,0,0,0,0,0,0,0]
	xposlist = [1170,942,978,1006,1042,1070,1106,1134]
	lastcombo = 0
	judgeupdate = 0

	def __init__(self, width, height):
		pygame.display.init()
		self.screen = pygame.display.set_mode([width,height])
		pygame.display.set_caption('PyBMS 0.0.1')
		self.frame = pygame.image.load('pybms_res/frame.png')
		self.note_odd = pygame.image.load('pybms_res/note_odd.png')
		self.note_even = pygame.image.load('pybms_res/note_even.png')
		self.note_sc = pygame.image.load('pybms_res/note_sc.png')
		self.beam_odd = pygame.image.load('pybms_res/beam_odd.png')
		self.beam_even = pygame.image.load('pybms_res/beam_even.png')
		self.beam_sc = pygame.image.load('pybms_res/beam_sc.png')
		self.judge = pygame.image.load('pybms_res/judge.png')
		self.guage = pygame.image.load('pybms_res/guage.png')

	def render(self,time,keylist,bpm,recentjudge,combo,isjudgeupdated,guage):
		self.screen.fill((0,0,0))
		self.screen.blit(self.frame,(0,0))
		self.renderbeam(keyprlist)
		self.renderpos(keylist,time,500) #460
		self.renderjudge(recentjudge,combo,isjudgeupdated)
		self.renderguage(guage)
		pygame.display.flip()

	def renderguage(self, guage):
		if guage != 100:
			guage_ = guage//2
			if guage_ == 0:
				guage_ = 1
		else:
			guage_ = 50
		for a in range(1,51):
			if a<=40:
				if guage_>=a:
					self.screen.blit(self.guage,(1243-6*a,613),(6,0,6,21))
				else:
					self.screen.blit(self.guage,(1243-6*a,613),(18,0,6,21))
			else:
				if guage_>=a:
					self.screen.blit(self.guage,(1243-6*a,613),(0,0,6,21))
				else:
					self.screen.blit(self.guage,(1243-6*a,613),(12,0,6,21))
		l = len(str(int(guage_*2)))
		for b in str(int(guage_*2)):
			self.screen.blit(self.guage,(1022-32*l,563),(0+32*int(b),29,32,44))
			l -= 1

	def renderjudge(self, recentjudge, combo, isjudgeupdated):
		if isjudgeupdated == True:
			self.judgeupdate = 0
		else:
			self.judgeupdate += 1
		if self.judgeupdate < 36:
			combo_ = str(combo)
			if recentjudge == "PR":
				self.screen.blit(self.judge,(1086-71,343),(540,148,142,74))
			elif recentjudge == "BD":
				self.screen.blit(self.judge,(1086-56,343),(540,74,113,74))
			elif recentjudge == "GD":
				jwidth = 142+len(combo_)*37
				self.screen.blit(self.judge,(1086-jwidth//2,343),(540,0,142,74))
				for a in range(len(combo_)):
					c = int(combo_[len(combo_)-a-1])
					self.screen.blit(self.judge,(1086+jwidth//2-(a+1)*37,343),(170+37*c,222,37,74))
			elif recentjudge == "GR":
				jwidth = 170+len(combo_)*37
				self.screen.blit(self.judge,(1086-jwidth//2,343),(0,222,170,74))
				for a in range(len(combo_)):
					c = int(combo_[len(combo_)-a-1])
					self.screen.blit(self.judge,(1086+jwidth//2-(a+1)*37,343),(170+37*c,222,37,74))
			elif recentjudge == "PG":
				jwidth = 170+len(combo_)*37
				animation = 74*(self.judgeupdate%3)
				self.screen.blit(self.judge,(1086-jwidth//2,343),(0,0+animation,170,74))
				for a in range(len(combo_)):
					c = int(combo_[len(combo_)-a-1])
					self.screen.blit(self.judge,(1086+jwidth//2-(a+1)*37,343),(170+37*c,animation,37,74))
		return False

	def renderbeam(self, keyprlist):
		for a in range(8):
			if keyprlist[a] == True:
				self.beamF[a] = 8
			elif self.beamF[a] > 0:
				self.beamF[a] -= 1
			if self.beamF[a] != 0:
				if a in [1,3,5,7]:
					width = 34*self.beamF[a]//8
					self.screen.blit(self.beam_odd,(17+self.xposlist[a]-width//2,0),(0,0,width,474))
				elif a in [2,4,6]:
					width = 26*self.beamF[a]//8
					self.screen.blit(self.beam_even,(13+self.xposlist[a]-width//2,0),(0,0,width,474))
				else:
					width = 60*self.beamF[a]//8
					self.screen.blit(self.beam_sc,(30+self.xposlist[a]-width//2,0),(0,0,width,474))

	def renderpos(self, keylist, time, greennum): #greennum in ms.
		for a in range(8):
			for key in keylist[a]:
				if time-155<key[0]<time+greennum:
					ypos = min(474,474-(key[0]-time)*474//greennum)
					if a in [1,3,5,7]:
						self.screen.blit(self.note_odd,(self.xposlist[a],ypos))
					elif a in [2,4,6]:
						self.screen.blit(self.note_even,(self.xposlist[a],ypos))
					elif a == 0:
						self.screen.blit(self.note_sc,(self.xposlist[a],ypos))
				else:
					break

def get_judge(time,keylist,score, combo,recentjudge,guage):
	try:
		while keylist[0][0]-time>keylist[1][0]-time:
			keylist.pop(0)
		judge = abs(keylist[0][0]-time)
		isjudgeupdated = False
		if judge <= PG:
			score += 2
			combo += 1
			keylist.pop(0)
			recentjudge,isjudgeupdated = "PG",True
			guage += GR_G
		elif judge <= GR:
			score += 1
			combo += 1
			keylist.pop(0)
			recentjudge,isjudgeupdated = "GR",True
			guage += GR_G
		elif judge <= GD:
			combo += 1
			keylist.pop(0)
			recentjudge,isjudgeupdated = "GD",True
			guage += GR_G/2
		elif judge <= BD:
			combo = 0
			keylist.pop(0)
			recentjudge,isjudgeupdated = "BD",True
			guage += BD_G
		if guage > 100:
			guage = 100
		if guage < 0:
			guage = 0
		return score,combo,recentjudge,isjudgeupdated,guage
	except:
		print("judge exeption")
		return score,combo,recentjudge,False,guage

def checkpoor(time,keylist,combo,recentjudge,isjudgeupdated,guage):
	for a in range(8):
		while keylist[a] != [] and keylist[a][0][0]-time < -1*BD:
			combo = 0
			keylist[a].pop(0)
			recentjudge = "PR"
			isjudgeupdated = True
			guage += PR_G
	if guage < 0:
		guage = 0
	return combo,recentjudge,isjudgeupdated,guage

bms = BMSData("NOTSET.bms")
bmsview = BMSView(1280,720)
"""
print(bms.data)
print(bms.bgmlist)
for a in range(8):
	print(bms.keylist[a])
"""
keylist = bms.keylist[:]
pygame.init()
played = True
b = 0
bgmlen = len(bms.bgmlist)
time = 0
isend = False
tickcount = 0
timer = pygame.time.Clock()
p = [0,0,0,0,0,0,0,0]
score = 0
combo = 0
guage = 22.0
recentjudge = ""
isjudgeupdated = False
keyprlist = [False,False,False,False,False,False,False,False]
while True: #MAIN LOOP HERE
	time += timer.get_time()
	for event in pygame.event.get(): #event section
		if event.type == KEYDOWN:
			if event.key == K_a:
				p[1] = bms.keypress(time,1,p[1])
				score,combo,recentjudge,isjudgeupdated,guage = get_judge(time,keylist[1],score,combo,recentjudge,guage)
				keyprlist[1] = True
			if event.key == K_w:
				p[2] = bms.keypress(time,2,p[2])
				score,combo,recentjudge,isjudgeupdated,guage = get_judge(time,keylist[2],score,combo,recentjudge,guage)
				keyprlist[2] = True
			if event.key == K_d:
				p[3] = bms.keypress(time,3,p[3])
				score,combo,recentjudge,isjudgeupdated ,guage= get_judge(time,keylist[3],score,combo,recentjudge,guage)
				keyprlist[3] = True
			if event.key in [K_e,K_r,K_u,K_i]:
				p[4] = bms.keypress(time,4,p[4])
				score,combo,recentjudge,isjudgeupdated,guage = get_judge(time,keylist[4],score,combo,recentjudge,guage)
				keyprlist[4] = True
			if event.key == K_k:
				p[5] = bms.keypress(time,5,p[5])
				score,combo,recentjudge,isjudgeupdated,guage = get_judge(time,keylist[5],score,combo,recentjudge,guage)
				keyprlist[5] = True
			if event.key == K_o:
				p[6] = bms.keypress(time,6,p[6])
				score,combo,recentjudge,isjudgeupdated,guage = get_judge(time,keylist[6],score,combo,recentjudge,guage)
				keyprlist[6] = True
			if event.key == K_SEMICOLON:
				p[7] = bms.keypress(time,7,p[7])
				score,combo,recentjudge,isjudgeupdated ,guage= get_judge(time,keylist[7],score,combo,recentjudge,guage)
				keyprlist[7] = True
			if event.key == K_RETURN:
				p[0] = bms.keypress(time,0,p[0])
				score,combo,recentjudge,isjudgeupdated,guage = get_judge(time,keylist[0],score,combo,recentjudge,guage)
				keyprlist[0] = True
		if event.type == KEYUP:
			if event.key == K_a:
				keyprlist[1] = False
			if event.key == K_w:
				keyprlist[2] = False
			if event.key == K_d:
				keyprlist[3] = False
			if event.key in [K_e,K_r,K_u,K_i]:
				keyprlist[4] = False
			if event.key == K_k:
				keyprlist[5] = False
			if event.key == K_o:
				keyprlist[6] = False
			if event.key == K_SEMICOLON:
				keyprlist[7] = False
			if event.key == K_RETURN:
				keyprlist[0] = False
		if event.type == QUIT:
			pygame.quit()
			sys.exit()

	while b < bgmlen and bms.bgmlist[b][0] <= time: #update state section
		key = bms.bgmlist[b][1]
		bms.wavdict[key].stop()
		bms.wavdict[key].play()
		b += 1
	if b >= bgmlen:
		isend = True
	if isend == True and pygame.mixer.get_busy() == False:
		break
	
	combo,recentjudge,isjudgeupdated,guage = checkpoor(time,keylist,combo,recentjudge,isjudgeupdated,guage)

	if tickcount == 9: #render screen section
		isjudgeupdated = bmsview.render(time, keylist, bms.bpm,recentjudge,combo,isjudgeupdated,guage)
		tickcount = 0
	else:
		tickcount += 1
	timer.tick(600)
