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
        self.__agelink="t_dist_rot_%d.dat" % (self.params["id"])
        self.__agelinkname="age_pdist_hip%d.dat" % (self.params["id"])
        self.__masslink="mass_dist_rot_%d.dat" % (self.params["id"])
        self.__masslinkname="mass_pdist_hip%d.dat" % (self.params["id"])
        self.__Zlink="z_dist_rot_%d.dat" % (self.params["id"])
        self.__Zlinkname="z_pdist_hip%d.dat" % (self.params["id"])
        self.__mulink="mu_dist_%d.dat" % (self.params["id"])
        self.__mulinkname="mu_pdist_hip%d.dat" % (self.params["id"])
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
        #msg = "<p> Stellar parameters for HIP%s are: " % (self.params["id"])
        msg = "<p> HIP %s Measurements: &nbsp&nbsp" % (self.params["id"])

        msg += "B<sub>T</sub> = %s &plusmn %s &nbsp&nbsp&nbsp&nbsp" % (self.params["BT"],self.params["eBT"])
        msg += "V<sub>T</sub> = %s &plusmn %s &nbsp&nbsp&nbsp&nbsp" % (self.params["VT"],self.params["eVT"])
        msg += "v&thinsp;sin&thinsp;i = %s &plusmn %s km s<sup>-1</sup>&nbsp&nbsp&nbsp&nbsp" % (self.params["vsini"],self.params["evsini"])
        msg += "&piv; = %s &plusmn %s mas&nbsp&nbsp&nbsp&nbsp" % (self.params["plx"],self.params["eplx"])

        msg += "<br>Additional systematic uncertainties added:  "
        msg += "B<sub>T</sub>: &plusmn 0.005 &nbsp&nbsp&nbsp&nbsp"
        msg += "V<sub>T</sub>: &plusmn 0.005 &nbsp&nbsp&nbsp&nbsp"
        msg += "v&thinsp;sin&thinsp;i: &plusmn 30 km s<sup>-1"

        for key in []: #self.params.keys():
            if (not key=="id" and not key.startswith("e")):
                 msg+="%s: %s &plusmn %s" % (key,self.params[key],self.params["e"+key])
                 #msg+="%s: %s;" % ("e"+key,self.params["e"+key])
    
        #msg+="<p>"
        #msg+="Fitted parameters are: "
        #msg+="<p> t = %f &plusmn%f" % (self.fittedparams[0],self.fittederrs[0])
        #msg+="<p> z = %f &plusmn%f" % (self.fittedparams[1],self.fittederrs[1])
        #msg+="<p> m = %f &plusmn%f" % (self.fittedparams[2],self.fittederrs[2])
        #msg+="<p> inc = %f &plusmn%f" % (self.fittedparams[3],self.fittederrs[3])
        #append the fitting information
        msg+="<p>"
        msg += "Minimum &chi;<sup>2</sup> = %.2f&ensp;&ensp;" % (self.minchi2)
        msg += "Posteriors for star HIP %s:" % (self.params["id"])

        msg+="&ensp;<a href=\"%s\" download=\"%s\">Age</a>" % \
            ("rrstar/" + self.datadir + self.__agelink, self.__agelinkname) 
        msg+="&ensp;<a href=\"%s\" download=\"%s\">Mass</a>" % \
            ("rrstar/" + self.datadir + self.__masslink, self.__masslinkname) 
        msg+="&ensp;<a href=\"%s\" download=\"%s\">Metallicity</a>" % \
            ("rrstar/" + self.datadir + self.__Zlink, self.__Zlinkname) 
        msg+="&ensp;<a href=\"%s\" download=\"%s\">&mu;</a>" % \
            ("rrstar/" + self.datadir + self.__mulink, self.__mulinkname) 
        #msg+="<a href=\"%s\" download=\"%s\">Posteriors for star HIP%s </a>" % (self.__link,self.__linkname,self.params["id"]) 
        msg+="<p>"
        return msg

    def fit(self,mean,sigma,priortype):
        #1) fit for the stelalr age and other properties using the given prior
        #2) update the fitted result saved in the HIPobjs class
        #return
        self.filelist,self.datadir,self.fittedparams,self.fittederrs,self.minchi2=calcprobs(str(self.params['id']), FeHval=mean, 
                  dFeH=sigma, norm=True, rot=True)

    def plot_posterior(self):
        if self.__plot:
            
            files_ok = [os.path.exists(ifile) for ifile in self.filelist]
            if not np.all(files_ok):
                return ""

            fig = plt.figure(figsize=(8,6))
            xlab = ["Age (Myr)", "Z", "Mass (Msun)", "$\mu$ = cos i"]
            ylab = ["dp/dT", "dp/dZ", "dp/dM", "dp/d$\mu$"]
            # Draw age, metallicity, mass, mu plots in turn
            for i in range(len(self.filelist)):
                data = np.loadtxt(self.filelist[i])
                ax = fig.add_subplot(221 + i)
                xmin = np.amin(data[:, 0][np.where(data[:, 1] > 1e-5)])
                xmax = np.amax(data[:, 0][np.where(data[:, 1] > 1e-5)])
                # draw with steps --> histogram plotting style
                ax.plot(data[:, 0], data[:, 1], ls="steps")
                ax.set_xlim([xmin, xmax])
                ax.set_ylim([0, 1.1])
                ax.set_ylabel(ylab[i] + " (x constant)")
                ax.set_xlabel(xlab[i])
                # Maximum number of x labels (to prevent overlap)
                plt.locator_params(nbins=6)
                ax.set_yticklabels('', visible=False)

            plt.tight_layout()
            #create a temprary link for the figure and send back the figure path

            tmpfile = tempfile.NamedTemporaryFile(dir="static/img/").name
            plt.savefig(tmpfile)
            self.tempfigurelink=tmpfile
            return "<img src=\"/rrstar/static/img/%s.png\" height = 500>" % (tmpfile.split('/')[-1]) 
               
        else:
            return ""

    def __del__(self):
        if not self.tempfigurelink=='' and os.path.exists(self.tempfigurelink):
            os.unlink(tempfigurelink)


