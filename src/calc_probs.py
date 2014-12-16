import pyfits as pyf
import numpy as np
from scipy import special
import sys
import tempfile

def makebins(arr):
    bins = np.zeros(arr.shape[0] + 1)
    bins[1:-1] = 0.5*(arr[1:] + arr[:-1])
    bins[0] = 1.5*arr[0] - 0.5*arr[1]
    bins[-1] = 1.5*arr[-1] - 0.5*arr[-2]
    return bins

def calcprobs(star, FeHval=0, dFeH=0.13, norm=False, rot=True):
    
    #prefix = '/home/tbrandt/Rotating/Rotsrc/output_rot'
    prefix = '/home/tbrandt/data/output_rot'
    #prefix = 'data/'
    outdir = tempfile.mkdtemp(dir="static/data/") + "/"
    #outdir = "static/data/"
    #print outdir
    #filename = 'output_alt2/HIP' + star + '_20140903.dat'
    if rot:
        filename = prefix + '/HIP' + star + '.fits.gz'
    else:
        filename = prefix + '/HIP' + star + '.fits'
    hdulist = pyf.open(filename)
    chi2 = hdulist[0].data
    #print star, chi2
    data = hdulist[1].data.astype(np.float)
    if rot:
        t_ratio = hdulist[2].data
        m_indx = hdulist[3].data
        z_indx = hdulist[4].data
        t_indx = hdulist[5].data
        ooc_indx = hdulist[6].data
        i_indx = hdulist[7].data
    else:
        m_indx = hdulist[2].data
        z_indx = hdulist[3].data
        t_indx = hdulist[4].data
        
    hdulist.close()

    # Read in M, metallicity, age from huge input file
    #hdulist = pyf.open(prefix + '/isochron_tables/nr_isochrones_finemassgrid.fits')
    hdulist = pyf.open(prefix + '/finemassgrid.fits')
    M = hdulist[0].data
    Z = hdulist[1].data
    logT = hdulist[3].data
    hdulist.close()

    # Omega/Omega_crit, inclination
    OOc = np.asarray([ 0., 0.1, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95])
    inc = np.linspace(0, np.pi/2, 21)

    # Mass weights calculated by integrating the Salpeter IMF

    wgt_M = np.zeros(M.shape)
    wgt_M[0] = -((M[1] + M[0])/2)**(-1.35) + (1.5*M[0] - 0.5*M[1])**(-1.35)
    wgt_M[-1] = -(1.5*M[-1] - 0.5*M[-2])**(-1.35) + ((M[-1] + M[-2])/2)**(-1.35)

    for i in range(1, M.shape[0] - 1):
        wgt_M[i] = -((M[i + 1] + M[i])/2)**(-1.35)
        wgt_M[i] += ((M[i - 1] + M[i])/2)**(-1.35)

    # lognormal distribution for metallicity, centered on FeHval

    wgt_Z = np.zeros(Z.shape)
    FeH = np.log10(Z/0.014) - FeHval
    wgt_Z[0] = special.erf((FeH[0] + FeH[1])/2/dFeH/2**0.5)/2 + 0.5
    for i in range(1, Z.shape[0] - 1):
        wgt_Z[i] = special.erf((FeH[i + 1] + FeH[i])/2/dFeH/2**0.5)/2
        wgt_Z[i] -= special.erf((FeH[i - 1] + FeH[i])/2/dFeH/2**0.5)/2
    wgt_Z[-1] = 0.5 - special.erf((FeH[-1] + FeH[-2])/2/dFeH/2**0.5)/2

    # Age prior is uniform in time.

    wgt_T = 10**(logT - logT[0])
    #wgt_T = np.ones(logT.shape)

    # Inclination prior is already included in the grid, apart
    # from having half the weight on the endpoints.

    if rot:
        wgt_inc = np.ones(inc.shape)*0.5
        wgt_inc[1:-1] *= 2 
        for i in range(1, inc.shape[0] - 1):
            wgt_inc[i] = -0.5*(np.cos(inc[i + 1]) - np.cos(inc[i - 1]))
        wgt_inc[-1] = -0.5*(np.cos(inc[-1]) - np.cos(inc[-2]))
        wgt_inc[0] = -0.5*(np.cos(inc[1]) - np.cos(inc[0]))

    # distribution in Omega/Omega_crit is a Maxwellian with mode=0.5.
    # Truncate the distribution at 0.975.
    
        wgt_OOc = np.ones(OOc.shape)
        maxval = special.erf(0.975/0.5) - (2/np.pi)**0.5*0.975/2**0.5*np.exp(-(0.975/0.5)**2)
        x = 0.5*OOc[1]/0.5
        wgt_OOc[0] = special.erf(x) - (2/np.pi)**0.5*x*2**0.5*np.exp(-x**2)
        wgt_OOc[0] /= maxval
        for i in range(1, wgt_OOc.shape[0] - 1):
            x1 = 0.5*(OOc[i] + OOc[i - 1])/0.5
            x2 = 0.5*(OOc[i] + OOc[i + 1])/0.5
            wgt_OOc[i] = special.erf(x2) - (2/np.pi)**0.5*x2*2**0.5*np.exp(-x2**2)
            wgt_OOc[i] -= special.erf(x1) - (2/np.pi)**0.5*x1*2**0.5*np.exp(-x1**2)
            wgt_OOc[i] /= maxval
    
        x = 0.5*(OOc[-1] + OOc[-2])/0.5
        wgt_OOc[-1] = maxval
        wgt_OOc[-1] -= special.erf(x) - (2/np.pi)**0.5*x*2**0.5*np.exp(-x**2)    
        wgt_OOc[-1] /= maxval

        #wgt_OOc *= 0
        #wgt_OOc[0] = 1
        #wgt_OOc[:2] *= 0
        #wgt_OOc[3:6] = 1./3

    # Calculate and apply the full weight array
    weight = wgt_M[m_indx]*wgt_Z[z_indx]*wgt_T[t_indx]
    if rot:
        weight *= wgt_OOc[ooc_indx]*wgt_inc[i_indx]
 
    pdens = np.exp(data)*weight
    if norm:
        pdens /= np.sum(pdens)

    # Calculate the 1-D marginalized posterior probability distributions.
    # These will generally be unnormalized.

    M_bins = makebins(M)
    pM = np.histogram(M[m_indx], bins=M_bins, weights=pdens)[0]

    outarr = np.zeros((pM.shape[0], 2))
    outarr[:, 0] = M
    outarr[:, 1] = pM/(M_bins[1:] - M_bins[:-1])
    outarr[:, 1] /= np.amax(outarr[:, 1])
    mmax=M[pM==max(pM)]
    merr=0
    if rot:
        mfile = outdir+'mass_dist_rot_' + star + '.dat'
    else:
        mfile=outdir+'mass_dist_nr_' + star + '.dat'
    np.savetxt(mfile, outarr, fmt="%.5g")
    
    Z_bins = makebins(Z)
    pZ = np.histogram(Z[z_indx], bins=Z_bins, weights=pdens)[0]

    outarr = np.zeros((pZ.shape[0], 2))
    outarr[:, 0] = Z
    outarr[:, 1] = pZ/(Z_bins[1:] - Z_bins[:-1])
    outarr[:, 1] /= np.amax(outarr[:, 1])
    zmax=Z[pZ==max(pZ)]
    zerr=0
    if rot:
        zfile = outdir+'z_dist_rot_' + star + '.dat'
    else:
        zfile = outdir+'z_dist_nr_' + star + '.dat'
    np.savetxt(zfile, outarr, fmt="%.5g")

    T_bins = makebins(logT)
    if rot:
        logT_corr = logT[t_indx] - np.log10(t_ratio)
    else:
        logT_corr = logT[t_indx]
    pT = np.histogram(logT_corr, bins=T_bins, weights=pdens)[0]
        
    outarr = np.zeros((pT.shape[0], 2))
    #outarr[:, 0] = logT
    #outarr[:, 1] = pT
    outarr[:, 0] = 10**(logT - 6)
    outarr[:, 1] = pT/outarr[:, 0]
    outarr[:, 1] /= np.amax(outarr[:, 1])
    tmax=10.**logT[pT==max(pT)]/1.e6
    terr=0
    if rot:
        tfile = outdir+'t_dist_rot_' + star + '.dat' #'_z%.2f' % (FeHval) + '.dat'
    else:
        tfile = outdir+'t_dist_nr_' + star + '.dat' #'_z%.2f' % (FeHval) + '.dat'
    np.savetxt(tfile, outarr, fmt="%.5g")

    if rot:
        inc_bins = makebins(inc)
        p_inc = np.histogram(inc[i_indx], bins=inc_bins, weights=pdens)[0]
        
        outarr = np.zeros((p_inc.shape[0], 2))
        outarr[:, 0] = np.cos(inc)
        outarr[:, 1] = p_inc
        outarr[:, 1] /= np.amax(p_inc)
        outarr[-1, 1] *= 2
        incmax=inc[p_inc==max(p_inc)]
        incerr=0
        incfile = outdir+'mu_dist_' + star + '.dat'
        np.savetxt(incfile,outarr, fmt="%.5g")
    else:
        incfile = ""
    filelist=[tfile,zfile,mfile,incfile]
    bestfit=[tmax,zmax,mmax,incmax]
    errfit=[terr,zerr,merr,incerr]
    return [filelist, outdir, bestfit, errfit, chi2]   

#if __name__ == "__main__":

#    FeH = 0.15
#    dFeH = 0.05
#    stars = ['208941', '208942']
#    for star in stars:
#        calcprobs(star, FeHval=0.15, dFeH=dFeH, norm=True, rot=True)
