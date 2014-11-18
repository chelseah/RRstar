#!/usr/bin/env python
import numpy as np
class cat_format(object):
    def __init__(self):
        self.catformat=dict(id=dict(col=0, type='string', width=17),
                       ra=dict(col=1, type='float', width=10),
                       dec=dict(col=2, type='float', width=10),
                       plx =dict(col=3, type='float', width=10),
                       eplx =dict(col=4, type='float', width=10),
                       BV=dict(col=5, type='float', width=6),
                       BT=dict(col=6, type='float', width=6),
                       eBT=dict(col=7, type='float', width=6),
                       VT=dict(col=8, type='float', width=6),
                       eVT=dict(col=9, type='float', width=6),
                       vsini=dict(col=10, type='float', width=6),
                       evsini=dict(col=11, type='float', width=6),
                       hatid=dict(col=12, type='string', width=17),
                       massra=dict(col=13, type='float', width=10),
                       massdec=dict(col=14, type='float', width=10),
                       xi=dict(col=15, type='float', width=10),
                       eta=dict(col=16, type='float', width=10),
                       center_dist=dict(col=17, type='float', width=13),
                       J=dict(col=18, type='float', width=6),
                       eJ=dict(col=19, type='float', width=6),
                       H=dict(col=20, type='float', width=6),
                       eH=dict(col=21, type='float', width=6),
                       K=dict(col=22, type='float', width=6),
                       eK=dict(col=23, type='float', width=6),
                       qlt=dict(col=24, type='string', width=5),
                       B=dict(col=25, type='float', width=6),
                       V=dict(col=26, type='float', width=6),
                       R=dict(col=27, type='float', width=6),
                       I=dict(col=28, type='float', width=6),
                       u=dict(col=29, type='float', width=6),
                       g=dict(col=30, type='float', width=6),
                       r=dict(col=31, type='float', width=6),
                       i=dict(col=32, type='float', width=6),
                       z=dict(col=33, type='float', width=6),
                       fld=dict(col=34, type='string', width=5),
                       hatnum=dict(col=35, type='string', width=8))
        #return catformat
    def load_line(self,data,keys):
        values = []
        for key in keys:
            values.append(self.read_data(data.split(),key))
        return values

    def read_data(self,data,key):
        try: 
            #print key,self.catformat[key],data[self.catformat[key]['col']]
            return eval(data[self.catformat[key]['col']])
        except NameError:
            if data[self.catformat[key]['col']] =='nan':
                return np.nan
            else:
                raise

class request_table(object):
    def __init__(self):
        self.catformat=dict(id=dict(col=0, type='string', width=17),
                       plx =dict(col=1, type='float', width=10),
                       eplx =dict(col=2, type='float', width=10),
                       BT=dict(col=3, type='float', width=6),
                       eBT=dict(col=4, type='float', width=6),
                       VT=dict(col=5, type='float', width=6),
                       eVT=dict(col=6, type='float', width=6),
                       vsini=dict(col=7, type='float', width=6),
                       evsini=dict(col=8, type='float', width=6),
                       J=dict(col=9, type='float', width=6),
                       eJ=dict(col=10, type='float', width=6),
                       H=dict(col=11, type='float', width=6),
                       eH=dict(col=12, type='float', width=6),
                       K=dict(col=13, type='float', width=6),
                       eK=dict(col=14, type='float', width=6),
                       )
        #return catformat
    def load_line(self,data,keys):
        values = []
        for key in keys:
            values.append(self.read_data(data.split(),key))
        return values

    def read_data(self,data,key):
        try: 
            #print key,self.catformat[key],data[self.catformat[key]['col']]
            return eval(data[self.catformat[key]['col']])
        except NameError:
            if data[self.catformat[key]['col']] =='nan':
                return np.nan
            else:
                raise
        except IndexError:
            return 
