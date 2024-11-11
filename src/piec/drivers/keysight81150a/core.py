'''
This is for the KEYSIGHT 81150A Arbitrary Waveform Generator and requires the KEYSIGHT I/O Libraries to function. check if true
'''
import numpy as np
import time
from ..scpi_instrument import Awg
#yes

class Keysight81150a(Awg):
    """
    Specific Class for this exact model of awg: Keysight 81150A
    """
    #add class attributes here, like max y range etc
    #correct syntax is tuple for ranges, list for limited amount, and dictionaries for nested things...
    channel = ['1', '2'] #allowable channels ['1', '2']
    voltage = (0, 5) #V_pp add functionality that swithches voltage depending on mode
    frequency = {'func': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
    func = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    #might be useless since all awgs should have sin, squ, pulse etc maybe not include arb? idk
    #note that depends if we are in high voltage or high bandwidth mode, if in high bandwidth mode all are 50e6 max freq
    slew_rate = 1.0e9 # V/s
    arb_wf_points_range = (2, 524288)

    def configure_output_amplifier(self, channel: str='1', type: str='HIV'):
        """
        This program configures the output amplifier for either maximum bandwith or amplitude. Taken from EKPY.
        NOTE: If in HIV mode max frequnecy is 50MHz, otherwise you get the full 120MHz
        NOTE: if sending a sin wave above 120MHz max voltage is 3V_pp
        args:
            wavegen (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            type (str): Amplifier Type args = [HIV (MAximum Amplitude), HIB (Maximum Bandwith)]
        """
        if type == 'HIV':
            self.voltage = (0, 10)
            self.frequency = {'func': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
        if type == 'HIB':
            self.voltage = (0, 5)
            self.frequency = {'func': {'SIN': (1e-6, 5e6), 'SQU': (1e-6, 50e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 50e6), 'pattern': (1e-6, 50e6), 'USER': (1e-6, 50e6)}}
        self.instrument.write("OUTP{}:ROUT {}".format(channel, type))

    def configure_wf(self, channel: str = '1', func: str = 'SIN', voltage: str = '1.0', offset: str = '0.00', frequency: str = '1e3', duty_cycle='50', num_cycles=None, invert: bool = False):
        if abs(float(voltage))>5:
            self.configure_output_amplifier(channel, 'HIV')
            print("WARNING switched to High Voltage Mode (HIV), you are now limited in frequency")
        return super().configure_wf(channel, func, voltage, offset, frequency, duty_cycle, num_cycles, invert)

    def __class_specific(self):
        """
        Place to define instrument specific stuff. Ideally never needed if Parent class is robust enough and instead
        we just define class attributes as above
        """
        return None
