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
import numpy as np
import time
from Hipobject import *

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
        #self.prior = self.get_argument('prior',None)
        self.prior = "Gaussian"
        try:
            self.prior_mean = float(self.get_argument('mean',np.nan))
            self.prior_sigma = float(self.get_argument('sigma',np.nan))
        except:
            self.prior_mean = 0
            self.prior_sigma = 0.1
        if self.prior_sigma < 0:
            self.prior_sigma = 0.1

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
                msg+="[Fe/H] prior is %s, &mu; = %.3f, &sigma; = %.3f," % (self.prior,self.prior_mean,self.prior_sigma)
                msg += " with Z<sub>&#9737;</sub> = 0.014 corresponding to [Fe/H] = 0."
                
                self.send_search_info(msg,star.plot_posterior())
            else:
                msg = "<p> Error: Please enter valid stellar parameters."
                print "<p> Error: Please enter valid stellar parameters."
                print "arrive here"
                if type(star)==str:
                    msg+="Couldn't find the given HIP ID"
                else:
                    print "arrive here"
                    msg+="The parameters are not in the right format"
                self.send_search_info(msg)
        else:
            msg="No parameters are entered"
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


