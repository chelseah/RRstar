#!/usr/bin/env python

'''rrstarhandlers.py 

This contains the URL handlers for the rrstar web-server.

'''

import os.path
import logging
import base64
import re

LOGGER = logging.getLogger(__name__)

from datetime import datetime, timedelta
from pytz import utc, timezone

import tornado.web
from tornado.escape import xhtml_escape, xhtml_unescape, url_unescape
from catformat import cat_format,request_table 
import numpy as np
import time
#import webdb

#import zmq
#import zmq.eventloop.zmqstream
#
#from zmqutils import to_zmq_msg, from_zmq_msg
#from miscutils import msgdecode, msgencode
#from authentication import BaseHandler


######################
## USEFUL CONSTANTS ##
######################

ARCHIVEDATE_REGEX = re.compile(r'^(\d{4})(\d{2})(\d{2})$')
MONTH_NAMES = {x:datetime(year=2014,month=x,day=12)
               for x in range(1,13)}


######################
## USEFUL FUNCTIONS ##
######################

#def msgencode(message, signer):
#    '''This escapes a message, then base64 encodes it.
#
#    Uses an itsdangerous.Signer instance provided as the signer arg to sign the
#    message to protect against tampering.
#
#    '''
#    try:
#        msg = base64.b64encode(signer.sign(xhtml_escape(message)))
#        msg = msg.replace('=','*')
#        return msg
#    except Exception as e:
#        return ''
#
#
#
#def msgdecode(message, signer):
#    '''This base64 decodes a message, then unescapes it.
#
#    Uses an itsdangerous.Signer instance provided as the signer arg to verify
#    the message to protect against tampering.
#
#    '''
#    try:
#        msg = message.replace('*','=')
#        decoded_message = base64.b64decode(msg)
#        decoded_message = signer.unsign(decoded_message)
#        return xhtml_unescape(decoded_message)
#    except Exception as e:
#        return ''
#

##################
## URL HANDLERS ##
##################
def load_hiptable(infile,keys):
    cat_form = cat_format()
    fin  = open(infile,mode='r')
    data_table=[]
    IDarr = []
    for line in fin.readlines():
        if(line.startswith("#")):
            continue
        #print line
        obj = cat_form.load_line(line.rstrip(),keys)
        data_table.append(obj)
        IDarr.append(int(cat_form.read_data(line.rstrip().split(),"id")))
    return [data_table,IDarr]

class HIPobjs(object):
    def __init__(self,keys,values):
        self.__plot=False
        self.params = dict(zip(keys,values))
        self.tempfigurelink=''
        return

    def __nonzero__(self):
        print "check here",self.check_keywords()
        return self.check_keywords()
    
    def check_keywords(self):
        #require at least a guess of plx and fill in the vsini part ourself, 
        #fill in error as big value if not given
        #request at least 3 colors with resonable value
        print "Enter checking"
        if not "plx" in self.params:
            print "no parallax"
            return 1
        if not "id" in self.params:
            self.params.update(ID="unknown star")
        for key in self.params.keys():
            if key is not "id" and (not key.startswith("e")):
                try:
                    if not "e"+key in self.params.keys():
                        self.params.update({'e'+key:9.e5})
                    self.params[key] = float(self.params[key])
                    self.params['e'+key] = float(self.params['e'+key])
                except ValueError or IndexError:
                    print "Value Error in %s" % key
                    return 1
        if not "vsini" in self.params:
            self.params.update(vsini=0.)
            self.params.update(evsini=9.e5)
        #check the colors again
        count = 0
        for colorkey in ["BT","VT","J","H","K"]: 
            try:
                print self.params['e'+colorkey]
                if(abs(self.params['e'+colorkey])<0.1):
                    count+=1
            except IndexError:
                pass
        print "count=%d" % count
        if count>2:
            return 0
        else:
            return 1

    def __str__(self):
        msg = "<p> Stellar parameters for %s are: " % (self.params["id"])
        for key in self.params.keys():
             if (not key=="id" and not key.startswith("e")):
                 msg+="%s: %s &plusmn %s;" % (key,self.params[key],self.params["e"+key])
                 #msg+="%s: %s;" % ("e"+key,self.params["e"+key])
    
        msg+="<p>"
        msg+="Fitted parameters are: "
        #append the fitting information
        msg+="<p>"
        return msg

    def fit(self,mean,sigma,priortype):
        #1) fit for the stelalr age and other properties using the given prior
        #2) update the fitted result saved in the HIPobjs class
        return

    def plot_posterior(self):
        if self.__plot:
            #create a temprary link for the figure and send back the figure path
            return self.tempfigurelink.name 
        else:
            return ""

    def __del__(self):
        if not self.tempfigurelink=='' and os.path.exists(self.tempfigurelink.name):
            os.unlink(tempfigurelink.name)


def file_search(infile):
    fin = open(infile,mode="w")
     
    return str(infile)

class RRstarHandler(tornado.web.RequestHandler):
    def initialize(self,catlog="data/hip_band.txt",keys=[]):
        self.keys = ["id","plx","eplx","vsini","evsini","BT","eBT","VT","eVT","J","eJ","K","eK","H","eH"]
        if(not keys==[]):
            self.keys=keys
        self.hip_table,self.IDarr=load_hiptable(catlog,self.keys)
        self.IDarr = np.array(self.IDarr)
        self.empty_canvas = "<img src=\"/rrstar/static/img/empty_canvas.png\" height = 500>"
        return
    def get(self):
        #self.write("in get\n")
        self.render("index.html",outcome="no result",canvas=self.empty_canvas)
                #    #self.write("\n")
        #else:
        #    self.write("no parameters given\n")
        #    self.render("rrstar/readme.html")
    def send_search_info(self,msg,canvas=""):
        print msg
        #self.render("searchresult.html",outcome=msg)
        if canvas=="":
            self.render("index.html",outcome=msg,canvas=self.empty_canvas)
        else:
            self.render("index.html",outcome=msg,canvas=canvas) 
        #self.render("data.html") 
    def do_search(self):
        if self.quicksearch_params.startswith("HIP"):
            try:
                HIPID = int(self.quicksearch_params.lstrip("HIP"))
            except ValueError:
                return "Error: Please input valid HIP IDs "
        else:
            try:
                HIPID = int(self.quicksearch_params)
            except ValueError:
                return "Error: Please input valid HIP IDs "
        try:
            index = np.where(self.IDarr==HIPID)[0]
            #print index, index==[]
            if len(index)==0:
                return "Error: Couldn't find the given HIP ID "
            stellar_param = self.hip_table[index]
            return HIPobjs(self.keys,stellar_param) 

        except IndexError:
            return "Error: Couldn't find the given HIP ID "
    def post(self):
        self.prior = self.get_argument('prior',None)
        self.prior_mean = self.get_argument('mean',np.nan)
        self.prior_sigma = self.get_argument('sigma',np.nan)
        #print self.prior
        self.quicksearch_params = self.get_argument('find',None)
        if self.quicksearch_params:
            self.quicksearch_params = xhtml_escape(
                    url_unescape(self.quicksearch_params,plus=False)
                    )
            #msg = "search ID is %s, prior is %s" % (self.quicksearch_params,self.prior)
            star = self.do_search()
            if(star):
                print "star true"
            if(not star):
                star.fit(self.prior_mean,self.prior_sigma,self.prior)
                msg = str(star) #this is the star name
                msg+=" Prior is %s, with mean=%f, sigma=%f" % (self.prior,float(self.prior_mean),float(self.prior_sigma))
                self.send_search_info(msg,star.plot_posterior())
            else:
                msg = "<p> Error: Please enter valid stellar parameters."
                if type(star)==str:
                    msg+="Couldn't find the given HIP ID"
                else:
                    msg+="The parameters are not in the right format"
                    msg+=str(star)
                self.send_search_info(msg)
      

class UploadFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("upload.html",outcome="no result")
    
    @tornado.web.asynchronous
    def post(self):
        #upload_path = os.path.join(os.path.dirname(__file__),'files')
        upload_path="files"
        file_metas=self.request.files['file']
        for meta in file_metas:
            filename=meta['filename']
            filepath=os.path.join(upload_path,filename)
            #print filepath
            with open(filepath,'wb') as up:
                up.write(meta['body'])
        if os.path.exists(filepath):
            #self.add_header("this will take a few minutes...")
            #file_search(filepath)
            result = file_search(filepath)
            time.sleep(5) #need to get rid of that when we are actually doing the calculation
            self.render("upload.html",outcome="the result are:")
        else:
            self.render("upload.html",outcome="Error: file upload failed")
             

class AboutHandler(tornado.web.RequestHandler):
    def initialize(self):
        #self.database = database
        return
    def get(self):
        self.render("about.html")

class StellarHandler(tornado.web.RequestHandler):
    def initialize(self):
        #self.database = database
        return
    def get(self):
        self.render("stellar_param.html",outcome="no result")




class DataHandler(tornado.web.RequestHandler):
    def initialize(self):
        #self.database = database
        return
    def get(self):
        self.render("data.html")


