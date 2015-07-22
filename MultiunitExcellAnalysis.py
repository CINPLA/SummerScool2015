from __future__ import division
import neo
import numpy as np
import matplotlib.pyplot as plt
import quantities as qt

def plot_waveform(data,
                  label=None,
                  normalize=False,
                  meanchan=False,
                  meanspikes=False,
                  channel=0,
                  spikenum=None,
                  compare=False,
                  fontsize=16,
                  ):
    if not compare:
        f = plt.figure(figsize=(16,9))
        ax = f.add_subplot(1,1,1)
    else:
        ax = compare
    unit = get_unit(data)
    wave = unit.spiketrains[0].waveforms
    t = np.linspace(0,1,50)*qt.ms
    if spikenum is not None and channel is None:
        if spikenum >= wave.shape[0]:
            spikenum = wave.shape[0]-1
            print ('You have asked for a spikenum which is larger than the number\
             of spikes in this spiketrain, reseting spikenum to %i'%spikenum)
        wave = wave[spikenum,:,:]
        label = ['ch0','ch1','ch2','ch3']
    if channel is not None and spikenum is None:
        wave = wave[:,channel,:]
    if spikenum is not None and channel is not None:
        wave = wave[spikenum,channel,:]
    if meanspikes:
        wave = np.mean(wave, axis=0)
    if normalize:
        wave = normalize_signal(wave,'minmax')
    if type(label) is str:
        h = plt.plot(t,wave.T, label=label)
        plt.legend(fontsize=fontsize)
    else:
        h = plt.plot(t,wave.T)
    #if not normalize:
    plt.ylabel(wave.dimensionality, fontsize=fontsize)
    plt.xlabel(t.dimensionality, fontsize=fontsize)
    if type(label) is list:
        plt.legend(h,label, fontsize=fontsize)
    simpleaxis(ax)

def plot_spiketrain(data,
                    raster=True,
                    histogram=False,
                    rectangular=False,
                    gaussian=False,
                    causal=False,
                    sigma=1,
                    t_start=0,
                    t_stop=None,
                    fontsize=16,
                    ):
    unit = get_unit(data)
    spikes = unit.spiketrains[0]
    if t_stop is None:
        t_stop = spikes.max()
    spikes = spikes.time_slice(t_start,t_stop)
    nplt = sum([raster,histogram,rectangular,gaussian,causal])
    if not raster or nplt > 1:
        f = plt.figure(figsize=(16,9))

    #raster
    if raster:
        if nplt == 1:
            f = plt.figure(figsize=(16,3))
        ax = f.add_subplot(nplt,1,1)
        ax.set_title('$N_{tot} = %i$'%len(spikes), fontsize=fontsize)
        for s in spikes.magnitude:
            ax.vlines(s, 0, 1, color = 'b')

        plt.ylim(0,1.1)
        if nplt > 1:
            ax.set_xticks([])
        else:
            ax.set_xlabel(spikes.dimensionality, fontsize=fontsize)
        ax.set_yticks([])
        simpleaxis(ax, left=True)
    #count rate
    if histogram:
        ax = f.add_subplot(nplt,1,1+raster)
        nbins = spikes.magnitude.max() / sigma
        ns, bs = np.histogram(spikes, nbins)
        ax.bar(bs[0:-1], ns/sigma, width = bs[1]-bs[0])
        ax.set_ylabel((qt.Hz).dimensionality, fontsize=fontsize)
        if nplt > 2:
            ax.set_xticks([])
        else:
            ax.set_xlabel(spikes.dimensionality, fontsize=fontsize)
        simpleaxis(ax)
    #instantaneuos rate
    if rectangular | gaussian | causal:
        wins = []
        if rectangular:
            wins.append(rectangularWindow)
        if gaussian:
            wins.append(gaussianWindow)
        if causal:
            wins.append(causalWindow)
        for n, win in enumerate(wins):
            ax = f.add_subplot(nplt,1,n+1+raster+histogram)
            r, t = instantaneous_rate(spikes, sigma, win, fs=1e3)
            ax.plot(t, r)
            ax.set_ylabel(r.dimensionality, fontsize=fontsize)

            if n != len(wins) - 1:
                ax.set_xticks([])
            else:
                ax.set_xlabel(t.dimensionality, fontsize=fontsize)
            simpleaxis(ax)

def simpleaxis(ax, left=False):
    """
    Removes axis lines
    """
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if left:
        ax.spines['left'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

def normalize_signal(inp, normtype='minmax'):
    if normtype == 'minmax':
        return (inp - inp.min())/np.max(inp - inp.min())
    elif normtype == 'meanstd':
        return (inp - np.mean(inp))/np.std(inp)

def instantaneous_rate(spikes, dt, window, fs=1e4):
    '''
    Here 's' is the spikes, the window size of 'window' is
    represented by 'dt', window is a function which takes two inputs
    '''
    t = np.linspace(0, spikes.magnitude.max(), fs)*qt.s
    r = np.zeros(t.shape)*qt.Hz
    for s in spikes:
        r += window(dt*qt.s, t - s)
    return r,t

def causalWindow(sig, tau):
    """
    causal window
    """
    a = 1./sig
    w = 0 / tau
    indices = np.where(tau >= 0)
    w[indices] = a**2 * tau[indices] * np.exp(-a * tau[indices])
    return w


def gaussianWindow(sig, tau):
    """
    gaussian window
    """
    w = 1.0 / (np.sqrt(2. * np.pi) *  sig) \
    * np.exp(-tau**2 / (2. * sig**2))
    return w


def rectangularWindow(dt, t):
    """
    rectangular window
    """
    w = 0 / t
    indices = np.where(np.logical_and(-dt/2. <= t, t < dt/2.))
    w[indices] = 1./dt
    return w

def get_unit(data):
    for tet in data['blk'].recordingchannelgroups:
        if tet.name == data['tetrode']:
            for unit in tet.units:
                if unit.name == data['unit']:
                    return unit

def raster_plot(spikes,ax):
    """
    Raster plot
    """
    for s in spikes.magnitude:
        ax.vlines(s, 0, 1, color = 'b')

    plt.ylim(-.1,1.1)
    ax.set_yticks([])
    ax.set_xticks([])
    return ax
