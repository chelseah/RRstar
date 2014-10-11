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
from catformat import cat_format 
import numpy as np
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

def send_search_info(search_parameter):
    #do nothing now
    return

def get_search_result(search_paramter):
    msg = "< a href=\"rrstar/data/%s.tar\"\ntarget=\"_blank\">HIP%s</a>"  % (hipid,hipid)
    #return search_parameter
    return msg


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


class RRstarHandler(tornado.web.RequestHandler):
    def initialize(self,catlog="data/hip_band.txt",keys=[]):
        self.keys = ["id","plx","eplx","BT","eBT","VT","eVT","J","Junc","K","Kunc","H","Hunc"]
        if(not keys==[]):
            self.keys=keys
        self.hip_table,self.IDarr=load_hiptable(catlog,self.keys)
        self.IDarr = np.array(self.IDarr)
        return
    def get(self):
        #self.write("in get\n")
        self.render("index.html",outcome="no result")
                #    #self.write("\n")
        #else:
        #    self.write("no parameters given\n")
        #    self.render("rrstar/readme.html")
    def send_search_info(self,msg):
        print msg
        #self.render("searchresult.html",outcome=msg) 
        self.render("index.html",outcome=msg) 
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
            msg = ''
            for i in xrange(len(self.keys)):
                msg+="%s: %s " % (self.keys[i],stellar_param[i])
            return msg
        except IndexError:
            return "Error: Couldn't find the given HIP ID "
    def post(self):
        self.prior = self.get_argument('prior')
        print self.prior
        self.quicksearch_params = self.get_argument('find',None)
        if self.quicksearch_params:
            self.quicksearch_params = xhtml_escape(
                    url_unescape(self.quicksearch_params,plus=False)
                    )
            #msg = "search ID is %s, prior is %s" % (self.quicksearch_params,self.prior)
            msg = self.do_search()
            msg+="prior is %s" % (self.prior)
            self.send_search_info(msg)


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


