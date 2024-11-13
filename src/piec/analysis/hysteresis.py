import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.integrate import cumulative_trapezoid
from analysis.utilities import *

def process_raw_hyst(path:str, show_plots=False):
    metadata, raw_df = standard_csv_to_metadata_and_data(path)
    processed_df = raw_df

    # get relevant values from metadata and math
    timestep = processed_df['time (s)'].values[-1]/len(processed_df)
    amp = metadata['amplitude'].values[0]
    frequency = metadata['frequency'].values[0]
    length = 1/frequency
    area = metadata['area'].values[0]
    N = metadata['n_cycles'].values[0]
    n_length = len(processed_df)
    
    # add on time-dependent processed arrays
    processed_df['current (A)'] = processed_df['voltage (V)']/50/area*100 # 50Ohm conversion, area correction, C/m^2 to uC/cm^2
    processed_df['polarization (uC/cm^2)'] = cumulative_trapezoid(processed_df['current (A)'], processed_df['time (s)'], initial=0)

    # correct time offset
    len_first_wave = n_length//N # cut out first triangle wave response
    first_pol_wave = processed_df['polarization (uC/cm^2)'].values[:len_first_wave]
    max_v_time = processed_df['time (s)'].values[n_length//(N*4)] # first max in applied V should be at the length of the wavaform /(4*n_cycles)
    max_p_time = max_v_time
    for i, pol in enumerate(processed_df['polarization (uC/cm^2)'].values): # find time where polarization reaches its first local max
        if pol == max(first_pol_wave):
            max_p_time = processed_df['time (s)'].values[i]

    time_offset = max_p_time - max_v_time # assume that first max in polarization coincides with first max in voltage in time

    if time_offset < 0:
        print("WARNING: Negative time offset detected, full waveform possibly not captured or data too noisy.")
        time_offset = 0
    
    start_n = int(time_offset//timestep)
    stop_n = int(start_n + (length//timestep))
    try:
        processed_df = processed_df.iloc[start_n:stop_n] # chop off data where voltage is not being applied
    except:
        print('WARNING: Time correction failed, data may be abnormal, or there may not be enough buffer data at the end of the captured waveform')

    # create applied voltage array from nominal assumptions
    l = (len(processed_df['time (s)'])//8)
    interp_v_array = [0,1,0,-1,0]+([1,0,-1,0]*(N-1))

    dense = interpolate_sparse_to_dense(np.linspace(0,len(interp_v_array),len(interp_v_array)), interp_v_array, total_points=len(processed_df))
    processed_df['applied voltage (V)'] = dense

    # optional plotting
    if show_plots:
        processed_df.plot(x='applied voltage (V)', y='polarization (uC/cm^2)')
        raw_df.plot(x='time (s)', y='voltage (V)')

    metadata['processed'] = True
    # update csv with new processed data
    metadata_and_data_to_csv(metadata, processed_df, path)