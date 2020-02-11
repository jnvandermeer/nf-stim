#!/usr/bin/env python2 (obviously)
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 15:25:56 2018

@author: johan
"""

#%% COMMENTS
''' So the thing is to deconstruct the bigger problem into a lot of solutions 
for much smaller problems. This is especially true, for the EFL with
visual, auditory and stop-inhibition (staircased) components that operate
interleaved

There's no way one could do this with builder, but (hopefully) with coder
and some help from asyncio, things could work.
'''



#%% Importing Statements
# importing statements:
import re
import random
import os
import pickle
import socket
import sys
import traceback
import time
# import pdb


# import pyglet
from psychopy import visual, clock, data, event, logging, sound, parallel
import numpy as np

# the assync stuff:
import trollius as asyncio
from trollius import From

# my helper:
import visualHelper


#%% Some REALLY global variables

LOGDIR='log'  # for if you want to change this...
LOGFILEBASE='efl'  # how to call our logfile --> it adds a number each time
IPADDRESS='localhost'  # port and ip to send codes towards to
PORT=6050  # which port is nice?  
BUTTONS = ['lctrl', 'rctrl']  # the button codes coming out of event.getStim()
tooSoonTime=0.0  # if it's pressed before this time --> discard + error
FPS=60.  # frames per second of your screen
LPT_TRIGGER_WAIT=0.005  # how long are the LPT port pulses?
RECORDFRAMEINTERVALS = True  # for debugging..
DO_VISUAL = False
DO_AUDIO = False
DO_GNG = True
EXTRA_FLIPS=4000  # allowing a too-long gonogo to properly finish up
GNGSPEED=1.0

#%% Initialize the Window

win=visual.Window(size=(800,600), fullscr=False, allowGUI=True, winType='pyglet', waitBlanking=False)
win.recordFrameIntervals = RECORDFRAMEINTERVALS  # record frame intervals...

# access with: win.frameIntervals

# since we're dealing with a couple of loops that are intermixed, and global variables are evil, at least
# do this -- make a dict that contains all variables that are needed so that the intermixed loops all
# require only ONE input argument, which helps me with the async stuff later on.




#%% The birth of Glob

#
# global variable with references to desired memory locations is easier to pass around.
G=dict()
mainClock=clock.Clock()
G['mainClock']=mainClock
# only use the G if it's going to be used later on in the gonogo, in the stop or in the visual.
G['DO_VISUAL']=DO_VISUAL
G['DO_AUDIO']=DO_AUDIO
G['DO_GNG']=DO_GNG



#%% LOGGING I - The psychopy Logfile

# figure out if there's a log directory, if not --> make it:
if not os.path.exists(LOGDIR):
    os.makedirs(LOGDIR)

# figure out which files reside within this logfile directory:
if len(os.listdir(LOGDIR)) == 0:
    logcounter=0
else:
    # figure out biggest number:
    #logcounter = max([int(match.group(1)) 
    #for match in [re.match(LOGFILEBASE+'([0-9]*)'+'.log',item) 
    #for item in os.listdir(LOGDIR)]])

    # figure out biggest number:
    matches=[match for match in [re.match(LOGFILEBASE+'([0-9]*)'+'.log',item) for item in os.listdir(LOGDIR)]]
    newlist=[]
    for match in matches:
        if match is not None:
            newlist.append(match.group(1))
    logcounter = max([int(n) for n in newlist])



# so make just another logfile on top of this one -- it'll be timestamped    
logcounter += 1

# this is the new logfile:
newLogFile=os.path.join(LOGDIR, LOGFILEBASE+'%d.log' % logcounter)
print('Logfile for off-line analysis: %s\n' % newLogFile)


# open up a log:
expLogger = logging.LogFile(newLogFile, logging.EXP) # the correct loglevel should be EXP!
logging.setDefaultClock(G['mainClock'])
# this ensures that all kinds of Exp thingies are written. DATA, WARNING and ERROR are higher
# but INFO and DEBUG won't be used.
# this is actually useful.


# so -- write stuff away with logging.data('blabla'); logging;flush()
# then -- logging.data('message') --> will give timestamped stuff
# logging.flush() --> to ACTUALLY WRITE it to the file!

# many (!!) of the stimuli also create a logging trigger, but you'd need to flush it
# in order to write it as-you-go
# otherwise it'll only happen at the end of the experiment
# and if there is an error of some sort --> bad luck, if you relied on loggin
# for your experimental logfile data crawlers, you just lost EVERYTHING.
G['expLogger']=expLogger


#%% Define Visual and GoNogo Stimuli
# make the dicts of visual and stop-inhibition stimuli:
# build a dict of visuals:
vstims=dict()
sstims=dict()
radialFreq=6
angleFreq=6
checkerSize=1.5
cicleSize=checkerSize/12*2
stimSize=checkerSize/12*1.5

AUTOLOGIT = True


checkr=visual.RadialStim(win, tex='sqrXsqr', ori=0, size=checkerSize, 
                     visibleWedge=(0, 181),
                     angularCycles=angleFreq, radialCycles=radialFreq, autoLog=AUTOLOGIT)


checkrf=visual.RadialStim(win, tex='sqrXsqr', ori=-90, size=checkerSize, 
                     visibleWedge=(90, 271),
                     angularCycles=angleFreq, radialCycles=radialFreq, autoLog=AUTOLOGIT)

checkl=visual.RadialStim(win, tex='sqrXsqr', ori=0, size=1.5, 
                     visibleWedge=(180, 360),
                     angularCycles=angleFreq, radialCycles=radialFreq, autoLog=AUTOLOGIT)


checklf=visual.RadialStim(win, tex='sqrXsqr', ori=90, size=1.5, 
                     visibleWedge=(90, 271),
                     angularCycles=angleFreq, radialCycles=radialFreq, autoLog=AUTOLOGIT)

circ=visual.Circle(win, radius=cicleSize, fillColor=[0,0,0], lineColor=[0, 0, 0], autoLog=AUTOLOGIT)

fa=.1;fb=1
fixationVert = [(fa, fa),(fa, fb),(-fa, fb),(-fa, fa),(-fb, fa),(-fb, -fa),
                (-fa, -fa),(-fa, -fb),(fa, -fb),(fa, -fa),(fb, -fa), (fb, fa)]
fixation = visual.ShapeStim(win, vertices=fixationVert, fillColor='red', 
                         size=.025, ori=0, lineColor='red', autoLog=AUTOLOGIT)


vstims['r']=[checkr, circ, fixation]
vstims['rf']=[checkrf, circ, fixation]
vstims['l']=[checkl, circ, fixation]
vstims['lf']=[checklf, circ, fixation]


stimcirc1=visual.Circle(win, radius=stimSize, fillColor=[1, 1, 1], lineColor=[1, 1, 1], autoLog=AUTOLOGIT)
stimcirc2=visual.Circle(win, radius=stimSize/1.5*1.37, fillColor=[0, 0, 0], lineColor=[1, 1, 1], autoLog=AUTOLOGIT)


#al=visual.ImageStim(win, image=u'stims/arrow.png')

arrowPinch=1.75;
arrowVert = [(-0.7071, -0.7071/arrowPinch), (0, -0.7071/arrowPinch),
              (0, -1), (1, 0),
              (0, 1),(0, 0.7071/arrowPinch), 
              (-0.7071, 0.7071/arrowPinch)]

arrowl = visual.ShapeStim(win, vertices=arrowVert, fillColor='white', 
                         size=.095, ori=180, lineColor='white', autoLog=AUTOLOGIT)

arrowr = visual.ShapeStim(win, vertices=arrowVert, fillColor='white', 
                         size=.095, ori=0, lineColor='white', autoLog=AUTOLOGIT)

arrowlr = visual.ShapeStim(win, vertices=arrowVert, fillColor='darkred', 
                         size=.095, ori=180, lineColor='darkred', autoLog=AUTOLOGIT)

arrowrr = visual.ShapeStim(win, vertices=arrowVert, fillColor='darkred', 
                         size=.095, ori=0, lineColor='darkred', autoLog=AUTOLOGIT)


sstims['pre']=[stimcirc1, stimcirc2]
sstims['fix']=[fixation]

sstims['al']=[stimcirc1, stimcirc2, arrowl]
sstims['ar']=[stimcirc1, stimcirc2, arrowr]
sstims['alr']=[stimcirc1, stimcirc2, arrowlr]
sstims['arr']=[stimcirc1, stimcirc2, arrowrr]




# the eyes closed stimulus:
eyesclosed = visual.TextStim(win, '\t\tEyes Closed\n\n20 seconds, do not count!',
                      color=(1, 1, 1), colorSpace='rgb', autoLog=AUTOLOGIT)



G['vstims']=dict()
G['vstims']['V']=vstims
G['vstims']['S']=sstims
G['vstims']['eyesclosed']=eyesclosed

G['vstims']['eyesclosed']=eyesclosed


#%% LOGGING II - Spread Markers to All The World
# these are the visual evt codes that I conceived a while ago:
    
        
# customized message handler + how-to-send codes that won't break equipment
# just make sure that the code < 255, always.
MSGDICT={
        
        # Stop / Inhibit Response Codes
        'BeginGoL':1,
        'BeginGoR':2,
        'BeginStopL':3,
        'BeginStopR':4,
        
        'RespL':5,
        'RespR':6,

        # somce some responses are not logged (because of too soon or too late or multiple presses)
        # log the keyboard separately.
        'KeyL': 7,        
        'KeyR': 8,
        'WrongKey': 9,

        'CorrectGoL':11,
        'CorrectGoR':12,
        'CorrectStopL':13,
        'CorrectStopR':14,
        'ErrorCommission':15,
        
        # don't expect too many of these:
        'ErrorOmission':21,
        'PressedTooSoon':22,
        'PressedTooLate':23,
        'TooManyResponses':24,
        'WrongSideErrorCommission':25,
        'WrongSideGo':26,
        
        'gonogo_BEGIN': 30,
        'gonogo_END': 31,

        

        # visual SSVEP checkerboard codes (8 and 13 Hz)
        #
        # when the contrast inverts, for SSVEP deconvolution
        'vis_l8':81,
        'vis_r8':82,
        'vis_l13':131,
        'vis_r13':132,

        # begin and end markers (for EEG frequency analysis), 8Hz and 13Hz
        'vis_bl8':83,
        'vis_br8':84,
        'vis_el8':85,
        'vis_er8':86,
 
        'vis_bl13':133,
        'vis_br13':134,
        'vis_el13':135,
        'vis_er13':136,

        'vis_BEGIN': 80,
        'vis_END': 140,

        # audio SSVEP codes (40 Hz and 55 Hz)
        #
        # when audio sample starts -- one audio sample contains 32 
        'aud_l40':41,
        'aud_r40':42,
        'aud_l55':51,
        'aud_r55':52,

        'aud_bl40':43,
        'aud_br40':44,
        'aud_el40':45,
        'aud_er40':46,
 
        'aud_bl55':53,
        'aud_br55':54,
        'aud_el55':55,
        'aud_er55':56,
        
        'aud_BEGIN': 40,
        'aud_END': 60,
            
        }        
        



import multiprocessing
class eventHandler(multiprocessing.Process):
    def __init__(self, 
                 messagedict,
                 clock, 
                 destip='127.0.0.1', 
                 destport=6500, 
                 LPTAddress=0x0378,
                 LPTTriggerWaiting=0.005,
                 filename='log/triggerlog.log',
                 sendParallel=True, 
                 sendTcpIp=True, 
                 sendLogFile=True,
                 printToTerminal=True,
                 printToTerminalAllowed=range(256)
                 ):
        '''
        we check parallel port, network port, and a file here (and we use the
        logger to do all of that log stuff)
        '''
        
        super(eventHandler, self).__init__()
        
        self.messagedict=messagedict
        self.clock=clock
        self.sendParallel=sendParallel
        self.sendTcpIp=sendTcpIp
        self.sendLogFile=sendLogFile
        self.destip=destip
        self.destport=destport
        self.LPTTriggerWaiting=float(LPTTriggerWaiting)
        self.printToTerminal=printToTerminal
        self.printToTerminalAllowed=printToTerminalAllowed
        
        # do we even have a parallel port?
        try:
            self._port=parallel.ParallelPort(LPTAddress)
            self._port.setData(0)  # this is the 'reset' to 0
            self._port_doreset=False  # once done we shouldn't do it..
            self._port_waitttime=0.005  # wait 5 msec after a trigger..
            
        except OSError:
            self._port=None
            self._port_doreset=False
            self._port_waitttime=None
            print('OS Does not seem to have a parallel port')
            # deactivate our parallel...
            self.sendParallel=False
            
        self._queue = multiprocessing.Queue()
        
        self._timequeue = multiprocessing.Queue()
        
        self._shutdown = multiprocessing.Event()
        

        
        # check whether there's another logfile - in log directory
        # make efl_triggers version of it, too.
        logdir=os.path.dirname(filename)
        logbasename, ext = os.path.splitext(os.path.basename(filename))

        
        # figure out if there's a log directory, if not --> make it:
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        
        # figure out which files reside within this logfile directory:
        if len(os.listdir(logdir)) == 0:
            logcounter=0
        else:
            # figure out biggest number:
            matches=[match for match in [re.match(logbasename+'([0-9]*)'+ext,item) for item in os.listdir(logdir)]]
            newlist=[]
            for match in matches:
                if match is not None:
                    newlist.append(match.group(1))
            logcounter = max([int(n) for n in newlist])
                    
                    
        
        # so make just another logfile on top of this one -- it'll be timestamped    
        logcounter += 1
        
        # this is the new logfile:
        self.newLogFile=os.path.join(logdir,logbasename+'%d'%logcounter + ext )
        
        
        print('logfile for markers: %s\n ' % self.newLogFile)
        # open up a log:
        # self.expLogger = logging.LogFile(newLogFile, logging.EXP) # the correct loglevel should be EXP!
        
        
        # so that's the logfile -- open op the socet, too:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        
        


    def send_message(self,message):
        '''
        it'll put the message into the queue, to be processed by 'run'
        '''
        self._queue.put(message)
        self._timequeue.put(self.clock.getTime())
        
        
    def run(self):
        '''
        This part runs - with a copy of memory upon its creation - in the separate process
        So it should just look at the queue, see if something's up, and send
        a trigger when it does.
        '''
        
        # do some while loop, checking for messages, and when one arrives -->
        # process it with both logfile (possibly) and with sending parallel
        # and also with.
        
        to_be_lpted=[]  # we start off empty here.
        to_be_written=[]  # for sending it to a file.
        to_be_written_messages=[]
        lpt_decay_clock=clock.Clock()
        code_sending_in_progress=False
        send_last_one=False
        
        
        if self.sendLogFile:
            expLogger = open(self.newLogFile,'w')  # , logging.EXP)
            print('Opened: %s\n' % expLogger)

        
        while not self._shutdown.is_set():
            
            time.sleep(0.0005) # take it easy on the CPU
            
            while not self._queue.empty():
                
                
                try:
                
                    message =  self._queue.get()
                    senttime = self._timequeue.get()  # I want to check how long it takes to deal with the queue like this.
                    code_to_send=self.messagedict[message]
                
                except:
                    
                    print('That code doesn\'''t exist: %s\n' % message)
                    break
                    
                
                # print(message)
                # print(code_to_send)
                if self.sendParallel:
                    
                    # put em into our to-be-sent-by-lpt list:
                    
                    to_be_lpted.append(code_to_send)
                    # self._port.setData(code_to_send)
                    
                    # following code is to reset to 0 of the LPT code output, after X msec.
                    # only evaluate if the queue is empty == dealing with the latest marker.
                    #if self._queue.empty():
                    #    lasttime=self.clock.getTime()
                    #    self._port_doreset=True
                        
                
                if self.sendTcpIp:
                    
                    # this is ultra-fast -- so no need to deal with this later.
                    self.sock.sendto(unicode(code_to_send), (self.destip, self.destport))

                    
                if self.sendLogFile:
                    
                    # might be slow - better make sure all codes are sent first
                    to_be_written.append(code_to_send)
                    to_be_written_messages.append(message)

                    
                    
            # heretime2=self.clock.getTime()
            # print('code: %d\t time sent: %.6f time logged: %.6f, diff = %.6f' % (code_to_send, senttime, heretime2, heretime2-senttime))
            # print('writing stuff took: %.3f msec' % ((heretime2-heretime)*1000));
            if self.sendParallel:   # avoid jamming up and missing triggers -- at the cost of making sure some temporal inaccuracy.
                                    # IF not too many codes to send out, things should work out. 
                if  not code_sending_in_progress and len(to_be_lpted) > 0:
                    tmpcode=to_be_lpted.pop(0)
                    self._port.setData(tmpcode)
                    lpt_decay_clock.reset()   # reset the clock...    
                    code_sending_in_progress=True
                    if len(to_be_lpted) == 0:  # after popping, see if we need to send the mast one.
                        send_last_one = True  # so send the last one (as 0)


                if not code_sending_in_progress and send_last_one:
                    self._port.setData(0)
                    lpt_decay_clock.reset()   # reset the clock...    
                    send_last_one=False
                    code_sending_in_progress=True
                                     

                if code_sending_in_progress and lpt_decay_clock.getTime() > self.LPTTriggerWaiting:
                    code_sending_in_progress=False  # so we can move on to the next code.
                    
                 
            if self.sendLogFile:
                
                if len(to_be_written) > 0:
                    wtmpcode = to_be_written.pop(0)
                    wtmpcode_message = to_be_written_messages.pop(0)
                
                    heretime=self.clock.getTime()

                    # simplified logfile for data analysis:
                    simplestr = '%.6f\t%.6f\t%.6f\t%d\n' % (senttime, heretime, heretime-senttime, wtmpcode)
                    expLogger.write(simplestr)
                    
                    # a more in-depth log of what was going on:
                    # logging.data(mystr)  # and write it to the psychopy main logifles, too.
      
                    if self.printToTerminal:
                        if wtmpcode in self.printToTerminalAllowed:
                            mystr = 'code: %d, message was: %s\ttime sent: %.6f time logged: %.6f, diff = %.6f' % (wtmpcode, wtmpcode_message, senttime, heretime, heretime-senttime)
                            print(mystr)
                    


                    
        #            # this is onlyt true if port needs to be reset, otherwise leave as-is.
        #            if self.sendParallel and self._port_doreset:
        #                # check the time - 10msec passed?
        #                if (self.clock.getTime() - lasttime) > self._port_waitttime:
        #                    self._port.setData(0)
        #                    self._port_doreset=False

        # at the end of the while loop, we have set the shutdown event - so do it.                    
        if self.sendLogFile:
            # give our system a little bit of time to actually write the file:
            time.sleep(5)
            expLogger.close()
            print('Closed: %s\n' % expLogger)

            
            

    def shutdown(self):
        ''' 
        get rid of this process -- call join later on from the main process
        '''
        # also - send triggers via our network connection towards
        if self._shutdown.is_set():
            self._shutdown.set()
        else:
            print('already shut down!')
            





# initualize it + make it findable by all subfucntions
eh=eventHandler(
        MSGDICT,
        mainClock, 
        destip='127.0.0.1', 
        destport=6050, 
        LPTAddress=0x0378,
        LPTTriggerWaiting=LPT_TRIGGER_WAIT,
        filename='log/triggerlog.log',
        sendParallel=True, 
        sendTcpIp=True, 
        sendLogFile=True,
        printToTerminal=True,
        printToTerminalAllowed=range(256)  # only allow the stops, which are < 40.
        )

eh.start()


G['eh']=eh

#                     messagedict,
#                     clock, 
#                     ip='127.0.0.1', 
#                     port=6500, 
#                     LPTAddress=0x0378,
#                     filename='log/triggerlog.log',
#                     sendParallel=True, 
#                     sendTcpIp=True, 
#                     sendLogFile=True



#%% ASYNC I - The GoNogo handler
#
#
# When it comes to logging responses, this is the Soup Nazi-equivalent.
# subjects should not press too soon, not too late, not twice, not the wrong side, etc etc.
#
    
G['S']=dict()
G['S']['STOP']=1
G['S']['GO']=0
G['S']['BUTTONS'] = BUTTONS 
G['S']['BUTTONS'] = GNGSPEED


# this is a list which basically acts as a pointer. From within functions 
# we can change this as needed.
G['S']['continueRoutine']=False # Container=[False]
G['S']['goNogoStim'] = [None] # Container=[None]
# nextfliptasks=[]
G['S']['tooSoonTime'] = tooSoonTime

    
# set up the staircase handler according specifications in Aron & Poldrack, 2009
# ""Cortical and Subcortical Contributions to Stop Signal Response Inhibition: 
# Role of the Subthalamic Nucleus""
# 
conditions = [
    {'label':'staircase1', 'startVal':100, 'stepSizes':50, 'nTrials':10, 'nUp':1, 'nDown':1, 'applyInitialRule':False, 'stepType':'lin'},
    {'label':'staircase2', 'startVal':150, 'stepSizes':50, 'nTrials':10, 'nUp':1, 'nDown':1, 'applyInitialRule':False, 'stepType':'lin'},
    {'label':'staircase3', 'startVal':200, 'stepSizes':50, 'nTrials':10, 'nUp':1, 'nDown':1, 'applyInitialRule':False, 'stepType':'lin'},
    {'label':'staircase4', 'startVal':250, 'stepSizes':50, 'nTrials':10, 'nUp':1, 'nDown':1, 'applyInitialRule':False, 'stepType':'lin'}
]
G['S']['myMultiStairs'] = data.MultiStairHandler(stairType='simple', method='random', conditions=conditions, nTrials=40)


# Obtain the Go Nogo Timing Parameters
# for stop-signal task: read in the critucal timings from one of my 500 
# OPTIMAL GLM Design specifications:
tmp_rand_number = random.randint(1,501)
#with open('efl/param_%d.txt' % (tmp_rand_number )) as f:
#    matrix=[[float(s) for s in re.findall(r'-?\d+\.?\d*', line)] for line in f]
with open('efl/tmpFile.txt','rb') as f:
    matrix=pickle.load(f)


SSnumber, SSstopgo, ISIwaitTime, tmp1, tmp2, LeftOrRight = zip(*matrix)

G['S']['SSnumber']=SSnumber
G['S']['SSstopgo']=SSstopgo
G['S']['ISIwaitTime']=ISIwaitTime
G['S']['LeftOrRight']=LeftOrRight



# a rather convoluted way of dealing with this on late Friday with beer in sight:
correctResponseSides=[]
wrongResponseSides=[]
for side in LeftOrRight:
    if side == 'left':
        correctResponseSides.append(BUTTONS[0])
        wrongResponseSides.append(BUTTONS[1])
    elif side == 'right':
        correctResponseSides.append(BUTTONS[1])
        wrongResponseSides.append(BUTTONS[0])
        
G['S']['correctResponseSides']=correctResponseSides
G['S']['wrongResponseSides']=wrongResponseSides
    
# hmm, maybe this needs further investigation(s)... see above!





G['S']['nextFlipTasks'] = []

# handle the new clock..., so put the function handle into the struct too.
# this is the MAIN clock...
G['S']['clock']=clock.Clock()
def reset_clock(x):
    x['S']['clock'].reset()
    x['S']['continueRoutine'] = True
G['S']['resetClock'] = reset_clock




   



# decorate this function...    
@asyncio.coroutine
def handle_gonogo(G):
    '''
    This contains the experimenal logic of the Stop Task. A lot of work
    went into constructing the stimuli. Stimuli parameters are loaded
    into variables in the code above. Runs 136 trials of Go-Nogo.
    This function is to be run within the asyncio loop.
    '''
 
    
    # we just need it here...
    STOP=1
    GO=0
    
    tooSoonTime = G['S']['tooSoonTime']  
    
    myMultiStairs = G['S']['myMultiStairs']
    
    
    DO_GNG = G['DO_GNG']
    

    # if the time it took tov respond is smaller than this time --> invalid.
    numberOfResponses=0

    
    
    G['S']['nextFLipTasks']=[]  # stuff winflupper needs to do later on..

    vstimname_for_gng={'left':'al', 'right':'ar'}


    # not sure if this is easier for later. But it should make a dict that'll help
    # if ctrl-L is pressed, then Code = KeyL, ctrl-R is KeyR -- irrespective of what the keys were
    # set to (f.e. z=KeyL, and m=KeyR) -- should also work.
    KeyCodes = {G['S']['BUTTONS'][0]:'KeyL', G['S']['BUTTONS'][1]:'KeyR'}

    GNGSPEED = G['S']['BUTTONS']
        
    
    # set the visual contents here...
    # INITIAL SETTING
    G['S']['goNogoStim']=G['vstims']['S']['fix']
    
    
    
    allGoReactionTimes=[]
    allGoReactionTimesLeft=[]
    allGoReactionTimesRight=[]

    
    allStopReactionTimes=[]
    allStopReactionTimesLeft=[]
    allStopReactionTimesRight=[]

  
    if DO_GNG:
        # yeah, do all kinds of init here.
        for trialNumber in range(len(G['S']['SSstopgo'])):
    
    
            # this is wehre we're going wrong -- we don't need this, anymore, right?
            # thisDirection=random.choice(('al','ar')) # obtain this from the file!!
            leftorright=LorR = G['S']['LeftOrRight'][trialNumber]
            LorR = leftorright[0].upper()
            
            thisDirection = vstimname_for_gng[leftorright]
    
    
            thisTrialType_num = G['S']['SSstopgo'][trialNumber] # this is a 0 (GO) or 1 (STOP)
            thisTrialType = [GO, STOP][int(thisTrialType_num)]  # shady practices indeed -- so later on I cany say 'if this TrialType is GO:, etc'
            GorNG = ['Go', 'Stop'][int(thisTrialType)]
    
    
            thisISIWaitTime = G['S']['ISIwaitTime'][trialNumber]
            
            correctResponseSide = G['S']['correctResponseSides'][trialNumber]
            wrongResponseSide = G['S']['wrongResponseSides'][trialNumber]
            
    
            
            allResponses=[] 
            allGoReactionTimes=[]
            allStopReactionTimes=[]
            responded=False # subj responded?
            trialHandled=False
            responseHandled=False
            
            
            
            if thisTrialType is STOP:
                # this should be called only 40 times, since there are 40 stop trials...
                thisSSD, thisCondition = myMultiStairs.next() # I defined the myMultiStairs above.
            
    
    
            # this code tells the loop to only continue when continueTroutine is not False
            # otherwise it'll just keep yielding.
            # let winflipper make new clock
            G['S']['continueRoutine']=False
            G['S']['nextFlipTasks'].append([G['S']['resetClock'], G]) # the makeNewClock automatically makes things continue
            while G['S']['continueRoutine'] is False:
                yield From(asyncio.sleep(0))
            cl=G['S']['clock'] # obtain the clock that was just made.
    

            event.clearEvents() 
            # ok, we can proceed -- the clock has been set.
            G['S']['goNogoStim']=G['vstims']['S']['pre']
            while cl.getTime() < 0.5 * GNGSPEED:
                
                evs=event.getKeys(timeStamped=cl)
                # check if they press too SOON:
                if len(evs)>0 and not responded:
                    buttonsPressed, timesPressed = zip(*evs)
                    # it's highly unlikely that two buttons are pressed in a signle
                    # frame, but control for that anyway. by rule below.
                    allResponses.append((buttonsPressed[0], timesPressed[0]))
                    numberOfResponses += 1
                    responded=True
                    buttonPressed, RTime = allResponses[0]
                    # LOG this event... (i.e. send trigger)

                    # G['eh'].send_message('PressedTooSoon')
                    responseHandled=True
                    trialHandled=True
                    trialOutcome='PressedTooSoon'
                    
                    for button in buttonsPressed:
                        print button
                        if button in KeyCodes.keys():
                            G['eh'].send_message(KeyCodes[button])
                        else:
                            G['eh'].send_message('WrongKey')
                            
                    
                    
                yield From(asyncio.sleep(0))
        
        
    
    
    
        
            # obtain our next clock...
            # this code tells the loop to only continue when continueTroutine is not False
            # otherwise it'll just keep yielding.
            # let winflipper make new clock
            G['S']['continueRoutine']=False
            
            # make sure upon next window flow, we have a new clock set, and also - that marker is sent signalling the start of the new go/stop trial.
            G['S']['nextFlipTasks'].append([G['S']['resetClock'], G]) # the makeNewClock automatically makes things continue
            # send the trigger regarding the arrow, as soon as the windows flips
            G['S']['nextFlipTasks'].append([G['eh'].send_message, 'Begin' + GorNG + LorR])
            while G['S']['continueRoutine'] is False:
                yield From(asyncio.sleep(0))
            cl=G['S']['clock'] # obtain the clock that was just made.
            
    
    
    
            # flush the even buffer here, otherwise we already have a response from before.
            event.clearEvents() 
            allResponses=[]
            TooManyResponses=False
            # ResponseTriggerTSent=False
            # this is where we show the arrow + find out whether a key is pressed:
            G['S']['goNogoStim']=G['vstims']['S'][thisDirection]
            currentTime = 0.0
            reactionTime = None
            event.clearEvents()
            while currentTime < 1.0 * GNGSPEED:
                currentTime = cl.getTime()
                
                # set the stimulus to the proper direction (it's a choice, for now... -- but it's much much better to hard-code it)
                # make the arrow (+ circle)
    
                evs=event.getKeys(timeStamped=cl)
                
                
                
                # put this check also above and below -- then should be relatively done!!
                if len(evs)>0 and responded:   # important to do this FIRST
                    TooManyResponses=True
                
                
                if len(evs)>0 and not responded:
                    buttonsPressed, timesPressed = zip(*evs)
                    # it's highly unlikely that two buttons are pressed in a signle
                    # frame, but control for that anyway. by rule below.
                    allResponses.append((buttonsPressed[0], timesPressed[0]))
                    numberOfResponses += 1
                    responded=True
                    buttonPressed, RTime = allResponses[0]
                    # LOG this event... (i.e. send trigger)
    

                # once a button is pressed -- display fixation point again.
                if responded and not responseHandled:
                    responseHandled=True
                    # 'clear' the visual window --> fixation cross, again:
                    G['S']['goNogoStim']=G['vstims']['S']['fix']

                    
                    if RTime < tooSoonTime:
                        trialHandled=True
                        trialOutcome='PressedTooSoon'
                    else:
                        # ResponseTriggerTSent=True
                        if buttonsPressed[0] == BUTTONS[0]:
                            G['eh'].send_message('RespL')
                        elif buttonsPressed[0] == BUTTONS[1]:
                            G['eh'].send_message('RespR')
                        reactionTime = timesPressed[0]

                # do this anyway.
                if len(evs)>0:
                    for button in buttonsPressed:
                        if button in KeyCodes.keys():
                            G['eh'].send_message(KeyCodes[button])
                        else:
                            G['eh'].send_message('WrongKey')


    
        
        
                # if it's a stop trial, then make arrow red after X time
                if thisTrialType is STOP and not responded:
                    # print(currentTime, thisSSD)
                    if currentTime > thisSSD/1000.:
                        G['S']['goNogoStim']=G['vstims']['S'][thisDirection+'r']
    
            
                # here we let the screen flip, for example...
                yield From(asyncio.sleep(0))
    
            
            # so the loop is done -- let's figure out what kind of trial this was.
            # taking care of the button press itself, as soon as button is pressed:
            if not trialHandled and responded:
                # print correctResponseSide
                # print buttonPressed
    
                trialHandled=True
    
                if TooManyResponses:
                    trialOutcome = 'TooManyResponses'
                    if thisTrialType is STOP:
                        myMultiStairs.addResponse(0)
    
                else:
                    if RTime < tooSoonTime:
                        trialOutcome = 'PressedTooSoon'
                        if thisTrialType is STOP:
                            myMultiStairs.addResponse(0)
                    else:
                        if thisTrialType is STOP:
                            
                            if buttonPressed == correctResponseSide:
                                trialOutcome = 'ErrorCommission'
                                myMultiStairs.addResponse(0)
        
                            elif buttonPressed == wrongResponseSide:
                                trialOutcome = 'WrongSideErrorCommission'
                                myMultiStairs.addResponse(0)
                                
                            
                        elif thisTrialType is GO:
                            if buttonPressed == correctResponseSide:
                                trialOutcome = 'CorrectGo'+LorR
    
                                # not yet...
                            elif buttonPressed == wrongResponseSide:
                                trialOutcome = 'WrongSideGo'
    
    
        
            # handle the 'response' if the button was NOT pressed:
            if not trialHandled and not responded:
                trialHandled = True
    
                if thisTrialType is GO:
                    trialOutcome = 'ErrorOmission'
    
                if thisTrialType is STOP:
                    trialOutcome = 'CorrectStop'+LorR
                    myMultiStairs.addResponse(1)

            
    
            # this code tells the loop to only continue when continueTroutine is not False
            # otherwise it'll just keep yielding.
            # let winflipper make new clock
    
    
            # this code tells the loop to only continue when continueTroutine is not False
            # otherwise it'll just keep yielding.
            # let winflipper make new clock
            G['S']['continueRoutine']=False
            G['S']['nextFlipTasks'].append([G['S']['resetClock'], G]) # the makeNewClock automatically makes things continue
            while G['S']['continueRoutine'] is False:
                yield From(asyncio.sleep(0))
            cl=G['S']['clock'] # obtain the clock that was just made.
    
    
    
            # print('final one')
            # ok, we can proceed -- the clock has been set.
            flushed=False
            G['S']['goNogoStim']=G['vstims']['S']['fix']
            event.clearEvents()
            while cl.getTime() < thisISIWaitTime * GNGSPEED:
                if not flushed:
                    # this is a nice place to save it to logfile: before the 
                    # send a report about the STOP trial, write a nice line:
                    # logging.data('messa')
                    logging.flush()
                    flushed=True
                    
                evs=event.getKeys(timeStamped=cl)
                                # do this anyway.
                if len(evs)>0:
                    
                    for button in buttonsPressed:
                        buttonsPressed, timesPressed = zip(*evs)
                        trialOutcome='PressedTooLate'
                        if button in KeyCodes.keys():
                            G['eh'].send_message(KeyCodes[button])
                        else:
                            G['eh'].send_message('WrongKey')
                                

                yield From(asyncio.sleep(0))

                                    
            # so we send it out the Final Verdict!
            G['eh'].send_message(trialOutcome)
            
            # Store the reaction time, too:
            # get the Stop Time - from staircase:
            if trialOutcome == 'CorrectGoL':
                allGoReactionTimesLeft.append(reactionTime)
                allGoReactionTimes.append(reactionTime)
            elif trialOutcome == 'CorrectGoR':
                allGoReactionTimesRight.append(reactionTime)
                allGoReactionTimes.append(reactionTime)
            elif trialOutcome == 'CorrectStopL':
                allStopReactionTimesLeft.append(thisSSD)
                allStopReactionTimes.append(thisSSD)
            elif trialOutcome == 'CorrectStopR':
                allStopReactionTimesRight.append(thisSSD)
                allStopReactionTimes.append(thisSSD)


        # log all the RT's:
        logging.data('All Go Reaction Times of Correct Trials')
        for item in allGoReactionTimesLeft:
            logging.data('RT %s: %.6f' % ('L', item))
        for item in allGoReactionTimesRight:
            logging.data('RT %s: %.6f' % ('R', item))

            
        logging.data('All Stop SSDs of Correct Trials')
        for item in allStopReactionTimesLeft:
            logging.data('SSD %s: %.6f' % ('L', item))
        for item in allStopReactionTimesRight:
            logging.data('SSD %s: %.6f' % ('R', item))
            

        # all:
        SSD = np.mean(allStopReactionTimes)
        RTGO = np.median(allGoReactionTimes)
        SSRT = RTGO - SSD
        
        # left:
        SSDL = np.mean(allStopReactionTimesLeft)
        RTGOL = np.median(allGoReactionTimesLeft)
        SSRTL = RTGOL - SSDL
        
        
        # right:
        SSDR = np.mean(allStopReactionTimesRight)
        RTGOR = np.median(allGoReactionTimesRight)
        SSRTR = RTGOR - SSDR

        logging.data('Mean SSD: %.6f\tMedian RT: %.6f\tSSRT = %.6f' % (SSD, RTGO, SSRT))
        
        logging.data('Mean SSDL: %.6f\tMedian RTL: %.6f\tSSRTL = %.6f' % (SSDL, RTGOL, SSRTL))
        
        logging.data('Mean SSDR: %.6f\tMedian RTR: %.6f\tSSRTR = %.6f' % (SSDR, RTGOR, SSRTR))
        
        logging.flush()


            # print(trialNumber)    
            
        # yield From(asyncio.sleep(0))
        # the stop task should be finished now!
        # the visual task should also be finished around the same time.
        # so further stuff, we can do with basic instructions, wait times, etc
        # print('finished, escaped from the loop!') 



#%% ASYNC II - The Audio Handler

# the audio stim list:
# audio_stim_list = [[10.,20.,'audio',['left','40']],[112.5,130.,'audio',['left','40']],[242.5,260.,'audio',['left','40']],[50.,60.,'audio',['left','55']],[195.,205.,'audio',['left','55']],[312.5,330.,'audio',['left','55']],[30.,40.,'audio',['right','40']],[147.5,165.,'audio',['right','40']],[277.5,295.,'audio',['right','40']],[77.5,95.,'audio',['right','55']],[175.,185.,'audio',['right','55']],[215.,225.,'audio',['right','55']]]

# make a more usable stim list:
audio_stim_list = [
        [10.0, 20.0, 'aud_l40'],
        [112.5, 130.0, 'aud_l40'],
        [242.5, 260.0, 'aud_l40'],
        [50.0, 60.0, 'aud_l55'],
        [195.0, 205.0, 'aud_l55'],
        [312.5, 330.0, 'aud_l55'],
        [30.0, 40.0, 'aud_r40'],
        [147.5, 165.0, 'aud_r40'],
        [277.5, 295.0, 'aud_r40'],
        [77.5, 95.0, 'aud_r55'],
        [175.0, 185.0, 'aud_r55'],
        [215.0, 225.0, 'aud_r55']
        ]

# load in the audio's timings, defined in seconds, so that later on, one could
# input triggers into the EEG (or optionally -- send out triggers with the event handler)        

# 40 Hz:
timings40Hz=np.loadtxt('stims/audio_40_ts.txt');
# 50 Hz:
timings55Hz=np.loadtxt('stims/audio_55_ts.txt')

# see also the figure_out_audio_timings.m file to further play with the audio's
# waveforms.


snd40hzL = sound.backend_pygame.SoundPygame(value='stims/audio_40Hz_L.wav',loops=0)
snd40hzR = sound.backend_pygame.SoundPygame(value='stims/audio_40Hz_R.wav',loops=0)
snd55hzL = sound.backend_pygame.SoundPygame(value='stims/audio_55Hz_L.wav',loops=0)
snd55hzR = sound.backend_pygame.SoundPygame(value='stims/audio_55Hz_R.wav',loops=0)


astims={
        'aud_l40':snd40hzL,
        'aud_r40':snd40hzR,
        'aud_l55':snd55hzL,
        'aud_r55':snd55hzR
        }


# put these into the variable, too...
G['astims']=astims
G['A']=dict()
G['A']['audio_stim_list']=audio_stim_list
G['A']['timings40Hz']=timings40Hz
G['A']['timings55Hz']=timings55Hz


@asyncio.coroutine
def handle_audio(G):
    '''
    this should handle the audio stimuli, using the async programming style.
    it starts a new clock and depending on timings, will start some audio
    samples, L or R, 40 or 55 Hz.
    '''
    
    
    audio_stim_list =  G['A']['audio_stim_list']
    astims = G['astims']
    eh=G['eh']

    DO_AUDIO = G['DO_AUDIO']
    
    
    audioClock=clock.Clock()
    playing=False
    withinAudioBlock=False
    prevWithinAudioBlock=False
    # RunAudio=True
    
    
    currentTime=audioClock.getTime()
    
    
    logging.data('aud_BEGIN')
    eh.send_message('aud_BEGIN')
    # just before going in here -- LOG it.
    # log the beginning...
    
    while currentTime < 340.: #currentTime < 340.:
        

        if DO_AUDIO:
            # print('hello')
            # print(currentTime)
            
            if not playing:     # I can safely use this since only one audio is playing at a time.
    
                withinAudioBlock=False
                
                for item in audio_stim_list:
                    b, e, stim = item
                    if b < currentTime < e:
                        currentStim = stim
                        withinAudioBlock=True
                        astims[stim].play()
                        playDuration=astims[stim].getDuration()
                        playing=True
                        playClock=clock.Clock()
                        
                        # print(stim)
                        logging.data(stim)
                        eh.send_message(stim)
                        logging.flush()
    
                        
            else:
                if playClock.getTime() > playDuration:  # figure out if something is playing 
                    playing=False
    
                    
            # try dealing with begin and ending markers:                    
            if withinAudioBlock and not prevWithinAudioBlock:
                messg=currentStim.replace('_','_b')
                # print(messg)
                logging.data(messg)
                eh.send_message(messg)
                prevWithinAudioBlock=True
                
            elif prevWithinAudioBlock and not withinAudioBlock:
                messg=currentStim.replace('_','_e')
                # print(messg)
                logging.data(messg)
                eh.send_message(messg)
                prevWithinAudioBlock=False
                
            
        # this will stop this loop, probably:
        currentTime=audioClock.getTime()
        #if currentTime > 340.:
        #    print('Stopping!')
        #    RunAudio=False
            
        yield From(asyncio.sleep(0))  # pass control to someone else, while this guy sleeps a bit.
            
            
    logging.data('aud_END')
    eh.send_message('aud_END')




#%% ASYNC III - The Visual handler
## set up the functions to be used in the end for asyncing through the loops:
# load the vis table somewhere here - big mem space (.csv?)
    

# so, instead of loading in a separate frame-by-frame list; define a function that as output has this list.


    
    
    

    
# load in the table that tells me all the stop signal stuff (.csv?)
#% Frame-by-frame checkerboard List
# load in the frame-list of the visual stimuli: i.e. saying when things should
# be used:
G['V']=dict()
G['V']['ASYNC_SLEEPTIME'] = 1./FPS*0.75        


#with open('efl/fd.pkl','rb') as f:
#    fd=pickle.load(f)
#    
#
#with open('efl/complete_fd_list.pkl','rb') as f:
#    complete_fd_list=pickle.load(f)
#
##    with open('efl/fd_with_markers.pkl','rb') as f:
##        fd_with_markers=pickle.load(f)
#    
#with open('efl/fd_with_markers_III.pkl','rb') as f:
#    fd_with_markers=pickle.load(f)

fd_with_markers = visualHelper.convert_to_fd_vis(FPS)

G['V']['fd_with_markers']=fd_with_markers
G['V']['EXTRA_FLIPS']=EXTRA_FLIPS
 



@asyncio.coroutine
def handle_visual(G):
    '''
    This flips the window, draws the stuff to be drawn, and calls
    functions to be called from the stop task. It is supposed to be
    run in the asyncio loop.
    '''
    
    # logging.console.setLevel(logging.DEBUG)
    # mainClock=G['mainClock']
    eh=G['eh']
    fd_with_markers=G['V']['fd_with_markers']
    
    
    # some extra flips, to be able to finish off the GNG:
    for i in range(EXTRA_FLIPS):
        fd_with_markers.append(fd_with_markers[-1])
    
    ASYNC_SLEEPTIME=G['V']['ASYNC_SLEEPTIME']
    
    DO_VISUAL = G['DO_VISUAL']
    
    print ASYNC_SLEEPTIME
    
    frameCounter=0
    vstims=G['vstims']['V']

    totFrames=len(fd_with_markers)

    # visualClock=clock.Clock()
    # this will run the entire length of the visual...
    # within this time, the stop signal task will (hopefully) finish.
    # OR... we can also just use a counter.
    
    
    
    while frameCounter < totFrames:
    
    
        # the workflow
        # 1) Prepare everything + draw
        # 2) Prepare markers
        # 3) win.flip() + the callOnFlip routines to be done.
    
        
        # all the visual stuff:
        frameIndex, visContents, markers = fd_with_markers[frameCounter]
        
        
        
        if frameIndex == 0:
            eh.send_message('vis_BEGIN')
        
        
        frameCounter += 1
        # deal with the visuals -- using vstims which should be accessible
        # we get the list...
        # create the shapes to be drawn using list comprehension
        
        shapes=[]
        
        if DO_VISUAL:
            if len(visContents) > 0:
                for item in visContents:
                    for stim in vstims[item]:
                        shapes.append(stim)


        # print shapes
        
        # print G['S']['goNogoStim']
        
        # add the gonogo stimuli to them:
        if len(G['S']['goNogoStim'])>0:
            for stim in G['S']['goNogoStim']:
                if stim is not None:
                    shapes.append(stim)
            
        
        # print shapes
        
        # draw them on our little canvas.
        if len(shapes)>0:
            for shape in shapes:
                #if shape is not None:
                shape.draw()
        else:
            G['vstims']['S']['fix'][0].draw()
            


        # prepare the calls for the next iteration, including marlers;
        # deal with visual markers
        if DO_VISUAL:
            if len(markers) > 0:
                for marker in markers:
                    win.callOnFlip(eh.send_message,marker)
                    # win.callOnFlip(print,marker)
        
        
        # this is to ensure that the GNG still is operational.
        tasks=G['S']['nextFlipTasks']
        while len(tasks) > 0:
            task=tasks.pop(0)
            function, arg = task
            win.callOnFlip(function, arg)


        # we flip the screen here - this will take ~ 16.66667 msec.
        win.flip()
        yield From(asyncio.sleep(0))
        

        
    eh.send_message('vis_END')
        
        # sleep for a little while - hope this actually works
        
                
        # do for loop for TIME (I suppose)
        
        # check vis table + draw stimuli
        # if there's an event - send to sync
        
        # check stimulus for stop + draw stimuli
        
        # pass on current time for audio presentation (this is another process)
        
        # AWAIT (!) -- to flip the window
    






#%% ASYNC IV - The Main Event Loop


# a test coroutine in order to check our debugging...            
@asyncio.coroutine
def test_it(G):
    cl=clock.Clock()
    # while cl.getTime() < 1: #i in range(1000):e
    runit=True
    while runit:
        print cl.getTime()
        yield From(asyncio.sleep(0))
    
        if cl.getTime() > 1:
            runit=False
        if cl.getTime() > 0.5:
            #pass
            print(1/0)
    
# a special exception handler coroutine that'll kill our main loop if something
# happens
@asyncio.coroutine
def handle_exception(f, G, loop):
    print f
    print loop
    try:
        yield From(f(G))
    except Exception:
        # print debug information
        print('---------------')
        print('---------------')
        print('ERROR OCCURRED:')
        print(sys.exc_info()[1])
        traceback.print_tb(sys.exc_info()[2])

        pending = asyncio.Task.all_tasks()
        for task in pending:
            task.cancel()
            # Now we should await task to execute it's cancellation.
            # Cancelled task raises asyncio.CancelledError that we can suppress:
            #with suppress(asyncio.CancelledError):
            #    loop.run_until_complete(task)        
        loop.stop()  # stops the loop, gives an error for that, too.
        G['eh'].shutdown()
        G['eh'].join()



def run_main_loop(G):
    '''
    This runs the stopingibition/visual/audio part of the paradigm using
    asyncio-replacement trollius. Before and after, we can still present
    other stimuli.
    '''
    
    
    # something like this:
    # mainClock=clock.Clock()
    # mainClockContainer[0]=mainClock # put it into my list, that double-serves
                                    # as a pointer
    
    
    
    loop=asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    #tasks = [
    #    asyncio.async(handleVisual()),
    #    asyncio.async(handleGonogo()),
    #    asyncio.async(handleEscape()),
    #    ]
    tasks_dbg = [
            # asyncio.async(handle_exception(test_it,G,loop)),
            asyncio.async(handle_exception(handle_audio,G,loop)),
            asyncio.async(handle_exception(handle_visual,G,loop)),
            asyncio.async(handle_exception(handle_gonogo,G,loop)),
            #asyncio.async(handle_exception(handle_visual,loop)),
            
            ]
    
    
    tasks = [
            # asyncio.async(test_it(G)),
            # asyncio.async(handle_audio(G))
            ]
    
    # so to debug, just run tasks_dbg instead of tasks.
    loop.run_until_complete(asyncio.wait(tasks_dbg))   
    loop.close()






#%% MAIN -- hope things work
if __name__=="__main__":
    # do the stuff.
    time.sleep(5)
    run_main_loop(G)


        
    #  close down our little Process, or it'll become a Zombie.
    G['eh'].shutdown()        
    G['eh'].join()
        
        





#%% The Rest
#    @asyncio.coroutine
#    def handle_exception_test_it():
#        try:
#            yield From(test_it())
#        except Exception:
#            
#            #print(sys.last_type)
#            #traceback.print_tb(sys.last_traceback)
#            #print("exception consumed")
#            # print('hallo!')
#            # print(traceback)
#            print(sys.exc_info()[1])
#            traceback.print_tb(sys.exc_info()[2])
#            # etype, evalue, etraceback = sys.exec_info()
#            # traceback.format_exc()
#            # print(traceback.fortmat_exec(etraceback))
#            
#    @asyncio.coroutine
#    def handle_exception_handle_audio():
#        try:
#            yield From(handle_audio())
#        except Exception:
#            
#            #print(sys.last_type)
#            #traceback.print_tb(sys.last_traceback)
#            #print("exception consumed")
#            # print('hallo!')
#            # print(traceback)
#            print(sys.exc_info()[1])
#            traceback.print_tb(sys.exc_info()[2])
#            
#            # etype, evalue, etraceback = sys.exec_info()
#            # traceback.format_exc()
#            # print(traceback.fortmat_exec(etraceback))
#            
#            
#    # we debug by CHAINING coroutines. Very very clear, yes. But it's necessity for now.
#    # would be nice to enable this feature in a nicer way for someone like me.
        
        
        

#%% Getting Input

# see: http://easygui.sourceforge.net/tutorial.html#enterbox
# variable = easygui.enterbox('hello','title','text')



# OR -- use psychopy's functions:
# expName = 'loc_v1'  # from the Builder filename that created this script
# expInfo = {'participant':'', 'session':'001'}
# dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
#
# access via expInfo['participant'], etc.


#%% Gonogo Thoughts
# vis contents is a list that's accessible by the function
# if the function changes its contents, then other functions will be able to
# read in those contents, too.
# I let the functions talk to each other using ... what?

# visContents is a list from handleGoNogo that contains the stuff to be drawn 
# GoNogo's end
# nexFlipTasks is a list/.. or a dict of stuff with function names and arguments
# that handleVisual should call using win.
    
#
#class GoNogo(object):
#    def __init__(self, SSnumber, SSstopgo, myMultiStairs, myVisualContents,nextFlipTasks, newClock, continueRoutine):
#        self.SSnumber=SSnumber
#        self.SSstopgo=SSstopgo
#        self.myMultiStairs=myMultiStairs
#        self.myVisualContents=myVisualContents
#        self.nextFlipTasks=nextFlipTasks
#        self.newClock=newClock
#        self.continueRoutine=continueRoutine
#        
# after some sleep, my brain might be able to conceive of how I could make this with a Object Oriented programming
# in the event loop in any case I should definitely use some kind of function that yields.
# or can I also make coroutine objects?
# and.. how to implement this, then?    
        
        
#%% Starcase usage -- use the starcase to loop over the stop trials:
# myMultiStair.next()
# myMultiStair.addResponse(1)
#
# getting intensities (for later to average over):
#
# myMultiStair.staircases[3].intensities
#    for thisIntensity, thisCondition in myMultiStairs:
#        print(thisIntensity)
#        print(thisCondition)
#        myMultiStairs.addResponse(random.choice([0,1]))
        
        
#%% More Random Stuff

#    visual_evt_codes={'left':{'8':87,'13':137},'right':{'8':88,'13':138}}
#    
#    # these are markers for the frequency analysis
#    visual_evt_codes_begin={'left':{'8':83,'13':133},'right':{'8':84,'13':134}}
#    visual_evt_codes_end={'left':{'8':85,'13':135},'right':{'8':86,'13':136}}
#    
#    # these are the thread starts - which conveniently also denotify what your visual segments
#    # should BE - in case you wish to reconstruct the visual ERP
#    global visual_evt_codes_beginvisthread
#    visual_evt_codes_beginvisthread={'left':{'8':81,'13':131},'right':{'8':82,'13':132}}
#    
#    
#    
#    
#    
#    
#    audio_evt_codes={'left':{'40':41,'55':51},'right':{'40':42,'55':52}}
#    audio_evt_codes_begin={'left':{'40':43,'55':53},'right':{'40':44,'55':54}}
#    audio_evt_codes_end={'left':{'40':45,'55':55},'right':{'40':46,'55':56}}
#    
#    
#    txt_evt_codes = {'normal':100, 'oddball':101}
        
        
#