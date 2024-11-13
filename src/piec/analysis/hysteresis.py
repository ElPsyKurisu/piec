import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.integrate import cumulative_trapezoid
from analysis.utilities import *

def process_raw_hyst(path:str, show_plots=False):
    metadata, raw_df = standard_csv_to_metadata_and_data(path)
    processed_df = raw_df

    processed_df = processed_df[processed_df['time (s)']>=0].copy() # cut out times before trigger

    # get relevant values from metadata and math
    amp = metadata['amplitude'].values[0]
    frequency = metadata['frequency'].values[0]
    length = 1/frequency
    active_n = len(processed_df[processed_df['time (s)']<=length])
    timestep = length/active_n
    area = metadata['area'].values[0]
    N = metadata['n_cycles'].values[0]
    n_length = len(processed_df)
    
    # add on time-dependent processed arrays
    processed_df['current (A)'] = processed_df['voltage (V)']/50/area*100 # 50Ohm conversion, area correction, C/m^2 to uC/cm^2
    processed_df['polarization (uC/cm^2)'] = cumulative_trapezoid(processed_df['current (A)'], processed_df['time (s)'], initial=0)

    # correct time offset
    len_first_wave = n_length//N # cut out first triangle wave response
    first_pol_wave = processed_df['polarization (uC/cm^2)'].values[:len_first_wave]
    max_v_time = processed_df['time (s)'].values[int(length//(timestep*4*N))] # first max in applied V should be at the length of the waveform /(4*n_cycles)
    max_p_time = processed_df['time (s)'].values[np.argmax(first_pol_wave)] # find time at first poarization maximum

    time_offset = max_p_time - max_v_time # assume that first max in polarization coincides with first max in voltage in time

    if time_offset < 0:
        print("WARNING: Negative time offset detected, full waveform possibly not captured or data too noisy.")
        time_offset = 0

    try:
        processed_df = processed_df[processed_df['time (s)']>=time_offset].copy()
    except:
        print('WARNING: Time correction failed, data may be abnormal, or there may not be enough buffer data at the end of the captured waveform')

    # create applied voltage array from nominal assumptions
    interp_v_array = np.array([0,1,0,-1,0]+([1,0,-1,0]*(N-1)))*amp

    dense = interpolate_sparse_to_dense(np.linspace(0,len(interp_v_array),len(interp_v_array)), interp_v_array, total_points=length//timestep)
    if len(dense)<len(processed_df):
        dense = np.concatenate([dense, np.zeros(len(processed_df) - len(dense))]) #make sure arrays are the same length

    processed_df['applied voltage (V)'] = dense[:len(processed_df)]

    # optional plotting
    if show_plots:
        processed_df.plot(x='applied voltage (V)', y='polarization (uC/cm^2)')
        processed_df.plot(x='time (s)', y=['polarization (uC/cm^2)', 'applied voltage (V)'], secondary_y=['applied voltage (V)'])

    metadata['processed'] = True
    # update csv with new processed data
    metadata_and_data_to_csv(metadata, processed_df, path)