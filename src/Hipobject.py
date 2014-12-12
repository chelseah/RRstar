#!/usr/bin/env python
import numpy as np
import scipy as sp
import os
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import tempfile
import random
import string
from catformat import cat_format,request_table 
from calc_probs import calcprobs


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
        self.__plot=True
        self.params = dict(zip(keys,values))
        self.tempfigurelink=''
        self.filelist=["","","",""]
        self.fittedparams=np.zeros(4)
        self.fittederrs=np.zeros(4)
        return

    def __nonzero__(self):
        print "check here",self.check_keywords()
        return self.check_keywords()
    
    def check_keywords(self):
        #require at least a guess of plx and fill in the vsini part ourself, 
        #fill in error as big value if not given
        #request at least 3 colors with resonable value
        #print "Enter checking"
        if not "plx" in self.params:
            #print "no parallax"
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
                #print self.params['e'+colorkey]
                if(abs(self.params['e'+colorkey])<0.1):
                    count+=1
            except IndexError:
                pass
        #print "count=%d" % count
        if count>=2:
            return 0
        else:
            return 1

    def __str__(self):
        msg = "<p> Stellar parameters for HIP%s are: " % (self.params["id"])
        for key in self.params.keys():
             if (not key=="id" and not key.startswith("e")):
                 msg+="<p> %s: %s &plusmn %s;" % (key,self.params[key],self.params["e"+key])
                 #msg+="%s: %s;" % ("e"+key,self.params["e"+key])
    
        msg+="<p>"
        msg+="Fitted parameters are: "
        msg+="<p> t = %f &plusmn%f" % (self.fittedparams[0],self.fittederrs[0])
        msg+="<p> z = %f &plusmn%f" % (self.fittedparams[1],self.fittederrs[1])
        msg+="<p> m = %f &plusmn%f" % (self.fittedparams[2],self.fittederrs[2])
        msg+="<p> inc = %f &plusmn%f" % (self.fittedparams[3],self.fittederrs[3])
        #append the fitting information
        msg+="<p>"
        return msg

    def fit(self,mean,sigma,priortype):
        #1) fit for the stelalr age and other properties using the given prior
        #2) update the fitted result saved in the HIPobjs class
        #return
        self.filelist,self.fittedparams,self.fittederrs=calcprobs(str(self.params['id']), FeHval=float(mean), 
                  dFeH=float(sigma), norm=True, rot=True)

    def plot_posterior(self):
        if self.__plot:
            #create a temprary link for the figure and send back the figure path
            tfile=self.filelist[0]
            zfile=self.filelist[1]
            mfile=self.filelist[2]
            incfile=self.filelist[3]
            #print os.path.exists(tfile)    
            #print os.path.exists(zfile)    
            if(os.path.exists(tfile) and os.path.exists(zfile)):
                #print "plotting"
                    
                fig = plt.figure()
                ax1=fig.add_subplot(211)
                ax2=fig.add_subplot(212)
                tdata = np.loadtxt(tfile)
                #get age range of the age
                tmax=max(tdata[:,1])
                index1 = tdata[:,0]>tdata[:,0][tdata[:,1]==tmax]
                index2 = tdata[:,1]<1.e-4
                #print tmax,len(tdata[:,1][index2])
                #print len(tdata[:,0][index1*index2])
                #print len(tdata[:,0][(-index1)*index2])
                xmax = tdata[:,0][index1*index2][0]
                xmin = tdata[:,0][(-index1)*index2][0]
                #print xmin, xmax
                #ax1.plot(10**tdata[:,0]/1.e6,tdata[:,1])
                #ax1.set_xlim([10.**xmin/1.e6,10.**xmax/1.e6])
                ax1.plot(tdata[:,0],tdata[:,1])
                ax1.set_xlim([xmin,xmax])
                #print 10.**xmin, 10.**xmax
                ax1.set_ylabel("dp/dT(x constant)")
                ax1.set_xlabel("Myr")
                ax2.set_ylabel("dp/dz(x constant)")
                ax2.set_xlabel("Z")
                zdata = np.loadtxt(zfile)
                zmax=max(zdata[:,1])
                ax2.plot(zdata[:,0],zdata[:,1])
                #filename=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                #tmpfile="static/img/tmp%s" % (filename)                 
                tmpfile = tempfile.NamedTemporaryFile(dir="static/img/").name
                plt.savefig(tmpfile)
                self.tempfigurelink=tmpfile
                return "<img src=\"/rrstar/static/img/%s.png\" height = 500>" % (tmpfile.split('/')[-1]) 
                #return "<img src=\"/rrstar/tmpBG2P5J\" height = 500>" #% (tmpfile) 
            else:
                return ""
        else:
            return ""

    def __del__(self):
        if not self.tempfigurelink=='' and os.path.exists(self.tempfigurelink):
            os.unlink(tempfigurelink)


