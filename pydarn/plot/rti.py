import pydarn,numpy,math,matplotlib,calendar,datetime,utils,pylab
import matplotlib.pyplot as plot
import matplotlib.lines as lines
from matplotlib.ticker import MultipleLocator
from matplotlib.collections import PolyCollection

def plotRti(dateStr,rad,beam=7,time=[0,2400],fileType='fitex',params=['velocity','power','width'], \
scales=[],channel='a',coords='gate',colors='lasse',yrng=-1,gsct=0,pdf=0):
	"""
	*******************************
	
	plotRti(dateStr,rad,beam,[time],[fileType]):
	
	crate an rti plot for a secified radar and time period

	INPUTS:
		dateStr: a string containing the target date in yyyymmdd format
		rad: the 3 letter radar code, e.g. 'bks'
		[beam]: the beam to plot
			default: 7
		[times]: the range of times for which the file should be read,
			in SIMPLIFIED [hhmm,hhmm] format, eg [29,156], 
			instead of [0029,0156]
			note that an end time of 2400 will read to the end of the file
			default = [0,2400]
		[fileType]: one of ['fitex','fitacf','lmfit']
			default = 'fitex'
		[params]: a list of the fit parameters to plot, allowable values are:
			['velocity','power','width','elevation','phi0']
			default: ['velocity','power','width']
		[scales]: a list of the min/max values for the color scale for
			each param.  If omitted, default scales will be used.  If present,
			the list should be n x 2 where n is the number of
			elements in the params list.  Use an empty list for default range,
			e.g. [[-250,300],[],[]]
			default: [[-200,200],[0,30],[0,150]]
		[channel]: the channel you wish to plot, the allowable values are
			'a' and 'b'
			default: 'a'
		[coords]: the coordinates to use for the y axis.  The allowable values are
			'gate','rng','geo'
			default: 'gate'
		[colors]: a string indicating what color bar to use, valid inputs are
			['lasse','aj']
			default: 'lasse'
		[yrng]: a list indicating the min and max values for the y axis in the
			chosen coordinate system, or a -1 indicating to plot everything
			default: -1
		[gsct]: a flag indicating whether to plot ground scatter as transparent
			default: 0 (ground scatter plotted normally)
	OUTPUTS:

	EXAMPLE:
		plotRti('20120101','bks',beam=12,time=[10,1453],fileType='fitex',
		params=['vel','power'],scales=[[-200,200],[]],channel='b',
		coords='mag'):
		
	Written by AJ 20120807
	*******************************
	"""
	
	
	#check the inputs
	assert(isinstance(dateStr,str) and len(dateStr) == 8),'error, dateStr must be a string 8 chars long'
	assert(isinstance(rad,str) and len(rad) == 3),'error, dateStr must be a string 3 chars long'
	assert(coords == 'gate' or coords == 'rng' or coords == 'geo'),"error, coords must be one of 'gate','rng','geo'"
	assert(isinstance(beam,int)),'error, beam must be integer'
	assert(0 < len(params) < 6),'error, must input between 1 and 5 params in LIST form'
	for i in range(0,len(params)):
		assert(params[i] == 'velocity' or params[i] == 'power' or params[i] == 'width' or \
		params[i] == 'elevation' or params[i] == 'phi0'), \
		"error, allowable params are 'velocity','power','width','elevation','phi0'"
	assert(scales == [] or len(scales)==len(params)), \
	'error, if present, scales must have same number of elements as params'
	assert(yrng == -1 or (isinstance(yrng,list) and yrng[0] <= yrng[1])), \
	'error, yrng must equal -1 or be a list with the 2nd element larger than the first'
	assert(colors == 'lasse' or colors == 'aj'),"error, valid inputs for color are 'lasse' and 'aj'"
	
	tscales = []
	for i in range(0,len(params)):
		if(scales == [] or scales[i] == []):
			if(params[i] == 'velocity'): tscales.append([-200,200])
			elif(params[i] == 'power'): tscales.append([0,30])
			elif(params[i] == 'width'): tscales.append([0,150])
			elif(params[i] == 'elevation'): tscales.append([0,50])
			elif(params[i] == 'phi0'): tscales.append([-numpy.pi,numpy.pi])
		else: tscales.append(scales[i])
	scales = tscales
			
	#read the radar data
	myData = pydarn.io.radDataRead(dateStr,rad,time=time,fileType=fileType,vb=0,beam=beam)
	
	myData = myData.getChannel(channel)
	
	assert(myData.nrecs > 0),'error, no data available'
	
	rtiFig = plot.figure()
	
	rtiTitle(myData,dateStr,beam)
	
	plotNoise(myData,rtiFig)
	
	plotFreq(myData,rtiFig)
	
	plotCpid(myData,rtiFig)
	

		
	figtop = .77
	figheight = .72/len(params)
	for i in range(0,len(params)):
		plotData(myData,rtiFig,params[i],scales[i],i==len(params)-1, \
		coords=coords,pos=[.1,figtop-figheight*(i+1)+.02,.76,figheight-.02],\
		yrng=yrng,colors=colors,gsct=gsct)
	
	print 'done plot'
	

	t1 = datetime.datetime.now()
	if(pdf):
		rtiFig.savefig('/home/miker/temp.png',orientation='landscape', papertype='letter',format='png',dpi=750)
	else:
		rtiFig.show()
	print datetime.datetime.now()-t1

def plotData(myData,myFig,param,scale,bottom,yrng=-1,coords='gate',pos=[.1,.05,.76,.72],colors='lasse',gsct=0):
	"""
	*******************************
	
	plotData(myData,myFig,param,scale,bottom,[yrng],[coords],[pos],[colors]):
	
	plots a frequency and Nave panel on Figure myFig at position pos

	INPUTS:
		myData: a radarData object containing the data to be plotted
		myFig: the figure to plot the panel on
		param: a list of the fit parameters to plot, allowable values are:
			['velocity','power','width','elevation','phi0']
			default: ['velocity','power','width']
		scale: a list of the min/max values for the color scale for
			each param.  The list should be n x 2 where n is the number of
			elements in the params list
			default: [[-200,200],[0,30],[0,150]]
		[pos]: the position of the panel, [xmin, ymin, xsize, ysize]
		[coords]: the coordinates to use for the y axis.  The allowable values are
			'gate','rng','geo','mag'
			default: 'gate'
		[colors]: a string indicating what color bar to use, valid inputs are
			['lasse','aj']
			default: 'lasse'
		[yrng]: a list indicating the min and max values for the y axis in the
			chosen coordinate system, or a -1 indicating to plot everything
			default: -1
		[gsct]: a flag indicating whether to plot ground scatter as transparent
			default: 0 (ground scatter plotted normally)
	OUTPUTS:

		
	Written by AJ 20120807
	*******************************
	"""
	
	#add an axes to the figure
	ax = myFig.add_axes(pos)
	ax.yaxis.set_tick_params(direction='out')
	ax.xaxis.set_tick_params(direction='out')
	ax.yaxis.set_tick_params(direction='out',which='minor')
	ax.xaxis.set_tick_params(direction='out',which='minor')

	rcnt = 0
	oldrsep = None
	rswitch = []
	for i in range(0,myData.nrecs):
		t = myData.times[i]
		if(myData[t]['prm']['rsep'] != oldrsep):
			oldrsep = myData[t]['prm']['rsep']
			rcnt = rcnt+1
			rswitch.append(i)
		
	if(rcnt > 1 and coords == 'gate'):
		print 'rsep changes during the day, switching coords to slant range'
		coords = 'rng'
		
	#draw the axes
	ax.plot_date(matplotlib.dates.date2num(myData.times), numpy.arange(len(myData.times)), fmt='w', \
	tz=None, xdate=True, ydate=False, alpha=0.0)
	
	ymin,ymax,pcoll = [],[],[]
	for i in range(0,rcnt):
		
		if(i == rcnt-1): endrec = myData.nrecs
		else: endrec = rswitch[i+1]
		
		myFov = None
		if(coords == 'geo' or coords == 'mag'):
			rmax=-1
			for j in range(rswitch[i],endrec):
				if(myData[myData.times[j]]['prm']['nrang'] > rmax): rmax = myData[myData.times[j]]['prm']['nrang']
			site = pydarn.radar.network().getRadarById(myData[myData.times[0]]['prm']['stid']).getSiteByDate(myData.times[rswitch[i]])
			if(myData[myData.times[0]]['prm']['bmnum'] > site.maxbeam): bmax = myData[myData.times[0]]['prm']['bmnum']
			else: bmax = site.maxbeam
			myFov = pydarn.radar.radFov.fov(site=site, ngates=rmax+1,nbeams=bmax+1,rsep=myData[myData.times[rswitch[i]]]['prm']['rsep'])

		
		#check if we want default y axis
		if(yrng == -1):
			ymin.append(0)
			ymax.append(-1)
			#find maxrange
			for j in range(rswitch[i],endrec):
				if(myData[myData.times[j]]['prm']['nrang'] > ymax[i]): ymax[i] = myData[myData.times[j]]['prm']['nrang']
			#check for coords type
			n_y = ymax[i]
			if(coords == 'geo' or coords == 'mag'):
				ymin[i]=myFov.latFull[myData[myData.times[rswitch[i]]]['prm']['bmnum']][ymin[i]]
				ymax[i]=myFov.latFull[myData[myData.times[rswitch[i]]]['prm']['bmnum']][ymax[i]]
			elif(coords == 'rng'):
				ymin[i] = ymin[i]*myData[myData.times[rswitch[i]]]['prm']['rsep']
				ymax[i] = ymax[i]*myData[myData.times[rswitch[i]]]['prm']['rsep']

		
		#make the y coords array
		if(coords == 'gate'): y_arr = numpy.arange(n_y)
		else:
			y_arr = []
			for j in range(0,n_y): 
				if(coords == 'geo' or coords == 'mag'): y_arr.append(myFov.latFull[myData[myData.times[0]]['prm']['bmnum']][j])
				elif(coords == 'rng'): y_arr.append(j*myData[myData.times[rswitch[i]]]['prm']['rsep']+myData[myData.times[rswitch[i]]]['prm']['frang'])
			y_arr = numpy.array(y_arr)
			

		verts,intensities,gs_flg = [],[],[]
		
		#collect the data into a list of vertices to be plotted
		for j in range(rswitch[i],endrec):
			t = myData.times[j]
			x1 = matplotlib.dates.date2num(t)
			if(j < endrec-1): 
				x2 =  matplotlib.dates.date2num(myData.times[j+1])
				if(x2-x1 > 4./1440.): x2 = x1+2./1440.
			else: x2 = x1+1./1440.
		
			#loop through gates with scatter
			for k in range(0,len(myData[t]['fit']['slist'])):
				r = myData[t]['fit']['slist'][k]
				#range gate numbers
				y1,y2 = r,r+1
				#get geo or mag coords if desired
				if(coords == 'geo' or coords == 'mag'):
					y1,y2 = fov.latFull[myData[t]['prm']['bmnum']][y1],fov.latFull[myData[t]['prm']['bmnum']][y2]
				#get slant raneg if desired
				if(coords == 'rng'):
					y1 = myData[t]['prm']['rsep']*y1+myData[t]['prm']['frang']
					y2 = y1+myData[t]['prm']['rsep']
					
				#save the polygon vertices
				verts.append(((x1,y1),(x1,y2),(x2,y2),(x2,y1)))
				
				#save the param to use as a color scale
				if(param == 'velocity'): intensities.append(myData[t]['fit']['v'][k])
				elif(param == 'power'): intensities.append(myData[t]['fit']['p_l'][k])
				elif(param == 'width'): intensities.append(myData[t]['fit']['w_l'][k])
				elif(param == 'elevation' and myData[j]['prm']['xcf']): intensities.append(myData[t]['fit']['elv'][k])
				elif(param == 'phi0' and myData[j]['prm']['xcf']): intensities.append(myData[t]['fit']['phi0'][k])
				if(gsct): gs_flg.append(myData[t]['fit']['gflg'][k])

		if(gsct == 0):
			inx = numpy.arange(len(verts))
		else:
			inx = numpy.where(numpy.array(gs_flg)==0)
			x=PolyCollection(numpy.array(verts)[numpy.where(numpy.array(gs_flg)==1)], closed=False, facecolors='.5',edgecolors='None')
			ax.add_collection(x, autolim=True)

		pcoll.append(PolyCollection(numpy.array(verts)[inx], closed=False, edgecolors='face',linewidths=.01))
		#set color array to intensities
		pcoll[i].set_array(numpy.array(intensities)[inx])
		#add the collection of polygons to the axes
		ax.add_collection(pcoll[i], autolim=True)

		
	#format the x axis
	ax.xaxis.set_minor_locator(matplotlib.dates.MinuteLocator(interval=20))
	plot.xticks(size=9)
	if(not bottom):
		loc,lab = plot.xticks()
		plot.xticks(loc,(' '))
	else:
		ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
		ax.xaxis.set_label_text('UT')
	
	#set ytick size
	plot.yticks(size=9)
	ymin=min(ymin)
	ymax=max(ymax)
	#format y axis depending on coords
	if(coords == 'gate'): 
		ax.yaxis.set_label_text('Range gate',size=10)
		ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%d'))
		ax.yaxis.set_major_locator(MultipleLocator((ymax-ymin)/5.))
		ax.yaxis.set_minor_locator(MultipleLocator((ymax-ymin)/25.))
	elif(coords == 'geo' or coords == 'mag'): 
		if(coords == 'mag'): ax.yaxis.set_label_text('Mag Lat [deg]',size=10)
		else: ax.yaxis.set_label_text('Geo Lat [deg]',size=10)
		ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%0.2f'))
		ax.yaxis.set_major_locator(MultipleLocator((ymax-ymin)/5.))
		ax.yaxis.set_minor_locator(MultipleLocator((ymax-ymin)/25.))
	elif(coords == 'rng'): 
		ax.yaxis.set_label_text('Slant Range [km]',size=10)
		ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%d'))
		ax.yaxis.set_major_locator(MultipleLocator(500))
		ax.yaxis.set_minor_locator(MultipleLocator(100))
	
	#check fi we want custom y range
	if(isinstance(yrng,list)):
		ax.set_ylim(bottom=yrng[0],top=yrng[1])
	else:
		ax.set_ylim(bottom=ymin,top=ymax)
		
	for i in range(0,rcnt+1):
		#generate the colormap
		pydarn.plot.plotUtils.genCmap(myFig,pcoll,param,scale,pos=pos,colors=colors)
		

	
def rtiTitle(myData,dateStr,beam,xmin=.1,xmax=.86):
	"""
	*******************************
	
	rtiTitle(myData,dateStr,beam,[xmin],[xmax]):
	
	prints a title on an rti plot

	INPUTS:
		myData: a radarData object containing the data to be plotted
		dateStr: the date in yyyymmdd format
		beam: the beam number
		[xmin]: coord for left alignment
		[xmax]: coord for right alignment
	OUTPUTS:

		
	Written by AJ 20120807
	*******************************
	"""
	n=pydarn.radar.network()
	r=n.getRadarById(myData[myData.times[0]]['prm']['stid'])
	
	plot.figtext(xmin,.95,r.name+'  ('+myData.ftype+')',ha='left',weight=550)
	
	d = utils.yyyymmddToDate(dateStr)
	plot.figtext((xmin+xmax)/2.,.95,str(d.day)+'/'+calendar.month_name[d.month][:3]+'/'+str(d.year), \
	weight=550,size='large',ha='center')
	
	plot.figtext(xmax,.95,'Beam '+str(beam),weight=550,ha='right')
	
def plotCpid(myData,myFig,pos=[.1,.77,.76,.05]):
	"""
	*******************************
	
	plotCpid(myData,myFig,[pos]):
	
	plots a cpid panel on Figure myFig at position pos

	INPUTS:
		myData: a radarData object containing the data to be plotted
		myFig: the figure to plot the panel on
		[pos]: the position of the panel, [xmin, ymin, xsize, ysize]
	OUTPUTS:

		
	Written by AJ 20120807
	*******************************
	"""
	oldCpid = -9999999
	
	#add an axes to the figure
	ax = myFig.add_axes(pos)
	ax.yaxis.tick_left()
	ax.yaxis.set_tick_params(direction='out')
	ax.set_ylim(bottom=0,top=1)
	ax.yaxis.set_minor_locator(MultipleLocator(1))
	ax.yaxis.set_tick_params(direction='out',which='minor')
	
	#draw the axes
	ax.plot_date(matplotlib.dates.date2num(myData.times), numpy.arange(len(myData.times)), fmt='w', \
	tz=None, xdate=True, ydate=False, alpha=0.0)
	
	for i in range(0,myData.nrecs):
		if(myData[myData.times[i]]['prm']['cp'] != oldCpid):
			
			ax.plot_date([matplotlib.dates.date2num(myData.times[i]),matplotlib.dates.date2num(myData.times[i])],\
			[0,1], fmt='k-', tz=None, xdate=True, ydate=False)
			
			oldCpid = myData[myData.times[i]]['prm']['cp']
			
			s = ' '+pydarn.radar.radUtils.getCpName(oldCpid)
		
			istr = ' '
			if(myData[myData.times[i]]['prm']['ifmode'] == 1): istr = ' IF'
			if(myData[myData.times[i]]['prm']['ifmode'] == 0): istr = ' RF'
			
			ax.text(myData.times[i],.5,' '+str(oldCpid)+s+istr,ha='left',va='center', size=10)
			
	#remove the x tick labels
	loc,lab = plot.xticks()
	plot.xticks(loc,(' '))
	#use only 2 major yticks
	plot.yticks([],(' '))
	plot.figtext(pos[0]-.07,pos[1]+pos[3]/2.,'CPID',ha='center',va='center', \
	size=8.5,rotation='vertical')
	
		
def plotNoise(myData,myFig,pos=[.1,.88,.76,.06]):
	"""
	*******************************
	
	plotNoise(myData,myFig,[pos]):
	
	plots a noise panel on Figure myFig at position pos

	INPUTS:
		myData: a radarData object containing the data to be plotted
		myFig: the figure to plot the panel on
		[pos]: the position of the panel, [xmin, ymin, xsize, ysize]
	OUTPUTS:

		
	Written by AJ 20120807
	*******************************
	"""
	#read the data
	sky=[]
	search = []
	for i in range(0,myData.nrecs):
		sky.append(myData[myData.times[i]]['prm']['noise.sky'])
		search.append(myData[myData.times[i]]['prm']['noise.search'])
	
	#add an axes to the figure
	ax = myFig.add_axes(pos)
	ax.yaxis.tick_left()
	ax.yaxis.set_tick_params(direction='out')
	ax.set_ylim(bottom=0,top=6)
	ax.yaxis.set_minor_locator(MultipleLocator())
	ax.yaxis.set_tick_params(direction='out',which='minor')

	
	#plot the sky noise data
	ax.plot_date(matplotlib.dates.date2num(myData.times), numpy.log10(sky), fmt='k-', \
	tz=None, xdate=True, ydate=False)
	#remove the x tick labels
	loc,lab = plot.xticks()
	plot.xticks(loc,(' '))
	#use only 2 major yticks
	plot.yticks([0,6],(' '))
	
	#left y axis annotation
	plot.figtext(pos[0]-.01,pos[1]+.004,'10^0',ha='right',va='bottom',size=8)
	plot.figtext(pos[0]-.01,pos[1]+pos[3],'10^6',ha='right',va='top',size=8)
	plot.figtext(pos[0]-.07,pos[1]+pos[3]/2.,'N.Sky',ha='center',va='center', \
	size=8.5,rotation='vertical')
	l=lines.Line2D([pos[0]-.06,pos[0]-.06], [pos[1]+.01,pos[1]+pos[3]-.01], \
	transform=myFig.transFigure,clip_on=False,ls='-',color='k',lw=1.5)                              
	ax.add_line(l)
	
	
	#add an axes to the figure
	ax2 = myFig.add_axes(pos,frameon=False)
	ax2.yaxis.tick_right()
	ax2.yaxis.set_tick_params(direction='out')
	ax2.set_ylim(bottom=0,top=6)
	ax2.yaxis.set_minor_locator(MultipleLocator())
	ax2.yaxis.set_tick_params(direction='out',which='minor')
	
	#plot the search noise data
	ax2.plot_date(matplotlib.dates.date2num(myData.times), numpy.log10(search), fmt='k:', \
	tz=None, xdate=True, ydate=False,lw=1.5)
	
	#remove the x tick labels
	loc,lab = plot.xticks()
	plot.xticks(loc,(' '))
	#use only 2 major yticks
	plot.yticks([0,6],(' '))
	
	#right y axis annotation
	plot.figtext(pos[0]+pos[2]+.01,pos[1]+.004,'10^0',ha='left',va='bottom',size=8)
	plot.figtext(pos[0]+pos[2]+.01,pos[1]+pos[3],'10^6',ha='left',va='top',size=8)
	plot.figtext(pos[0]+pos[2]+.06,pos[1]+pos[3]/2.,'N.Sch',ha='center',va='center',size=8.5,rotation='vertical')
	l=lines.Line2D([pos[0]+pos[2]+.07,pos[0]+pos[2]+.07], [pos[1]+.01,pos[1]+pos[3]-.01], \
	transform=myFig.transFigure,clip_on=False,ls=':',color='k',lw=1.5)                              
	ax2.add_line(l)
	
def plotFreq(myData,myFig,pos=[.1,.82,.76,.06]):
	"""
	*******************************
	
	plotFreq(myData,myFig,[pos]):
	
	plots a frequency and Nave panel on Figure myFig at position pos

	INPUTS:
		myData: a radarData object containing the data to be plotted
		myFig: the figure to plot the panel on
		[pos]: the position of the panel, [xmin, ymin, xsize, ysize]
	OUTPUTS:

		
	Written by AJ 20120807
	*******************************
	"""
	y=[]
	nave=[]
	for i in range(0,myData.nrecs):
		y.append(myData[myData.times[i]]['prm']['tfreq']/1e3)
		if(y[i] > 16): y[i] = 16
		if(y[i] < 10): y[i] = 10
		nave.append(myData[myData.times[i]]['prm']['nave'])
		
		
	#FIRST, DO THE TFREQ PLOTTING
	ax = myFig.add_axes(pos)
	ax.yaxis.tick_left()
	ax.yaxis.set_tick_params(direction='out')
	ax.set_ylim(bottom=10,top=16)
	ax.yaxis.set_minor_locator(MultipleLocator())
	ax.yaxis.set_tick_params(direction='out',which='minor')
	
	ax.plot_date(matplotlib.dates.date2num(myData.times), y, fmt='k-', \
	tz=None, xdate=True, ydate=False,markersize=2)
	
	loc,lab = plot.xticks()
	plot.xticks(loc,(' '))
	#customize yticks
	plot.yticks([10,16],(' '))
	
	plot.figtext(pos[0]-.01,pos[1],'10',ha='right',va='bottom',size=8)
	plot.figtext(pos[0]-.01,pos[1]+pos[3]-.003,'16',ha='right',va='top',size=8)
	plot.figtext(pos[0]-.07,pos[1]+pos[3]/2.,'Freq',ha='center',va='center',size=9,rotation='vertical')
	plot.figtext(pos[0]-.05,pos[1]+pos[3]/2.,'[MHz]',ha='center',va='center',size=7,rotation='vertical')
	l=lines.Line2D([pos[0]-.04,pos[0]-.04], [pos[1]+.01,pos[1]+pos[3]-.01], \
	transform=myFig.transFigure,clip_on=False,ls='-',color='k',lw=1.5)                              
	ax.add_line(l)
	
	
	#NEXT, DO THE NAVE PLOTTING
	ax2 = myFig.add_axes(pos,frameon=False)
	ax2.yaxis.tick_right()
	ax2.yaxis.set_tick_params(direction='out')
	ax2.set_ylim(bottom=0,top=80)
	ax2.yaxis.set_minor_locator(MultipleLocator(20))
	ax2.yaxis.set_tick_params(direction='out',which='minor')
	
	ax2.plot_date(matplotlib.dates.date2num(myData.times), nave, fmt='k:', \
	tz=None, xdate=True, ydate=False,markersize=2)
	
	loc,lab = plot.xticks()
	plot.xticks(loc,(' '))
	#customize yticks
	plot.yticks([0,80],(' '))
	
	plot.figtext(pos[0]+pos[2]+.01,pos[1]+.004,'0',ha='left',va='bottom',size=8)
	plot.figtext(pos[0]+pos[2]+.01,pos[1]+pos[3],'80',ha='left',va='top',size=8)
	plot.figtext(pos[0]+pos[2]+.06,pos[1]+pos[3]/2.,'Nave',ha='center',va='center',size=8.5,rotation='vertical')
	l=lines.Line2D([pos[0]+pos[2]+.07,pos[0]+pos[2]+.07], [pos[1]+.01,pos[1]+pos[3]-.01], \
	transform=myFig.transFigure,clip_on=False,ls=':',color='k',lw=1.5)                              
	ax2.add_line(l)