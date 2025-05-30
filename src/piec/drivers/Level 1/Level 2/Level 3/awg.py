"""
This is an outline for what the awg.py file should be like.

An awg (arbitrary waveform generator) is defined as an instrument that has the typical features on expects an awg to have
"""
from ..generator import Generator
class Awg(Generator):
    # Initializer / Instance attributes
    """
    All awgs must be able to generate an arbitrary waveform and output it to the selected channel
    """

    #core output channel control functions

    def output(self, channel, on=True):
        """
        All awgs must be able to output something, so therefore we need a method to turn the output on for the selected channel.
        args:
            channel (int): The channel to output on
            on (bool): Whether to turn the output on or off
        """
    
    #Standard waveform configuration functions
    def set_waveform(self, channel, waveform):
        """
        Sets the waveform to be generated on the selected channel either built in or user defined
        args:
            channel (int): The channel to set the waveform on
            waveform (str): The waveform to be generated, e.g., 'sine', 'square', 'triangle', 'ramp', 'pulse', 'arb'
        """
    def set_frequency(self, channel, frequency):
        """
        Sets the frequency of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the frequency on
            frequency (float): The frequency of the waveform in Hz
        """
    def set_delay(self, channel, delay):
        """
        Sets the delay of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the delay on
            delay (float): The delay of the waveform in seconds
        """
    def set_amplitude(self, channel, amplitude):
        """
        Sets the amplitude of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the amplitude on
            amplitude (float): The amplitude of the waveform in volts
        """
    def set_offset(self, channel, offset):
        """
        Sets the offset of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the offset on
            offset (float): The offset of the waveform in volts
        """
    def set_load_impedance(self, channel, load_impedance):
        """
        Sets the load impedance of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the load impedance on
            load_impedance (float): The load impedance of the waveform in ohms
        """
    def set_source_impedance(self, channel, source_impedance):
        """
        Sets the source impedance of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the source impedance on
            source_impedance (float): The source impedance of the waveform in ohms
        """
    def set_polarity(self, channel, polarity):
        """
        Sets the polarity of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the polarity on
            polarity (str): The polarity of the waveform, e.g., 'positive', 'negative'
        """
    def configure_waveform(self, channel, waveform, frequency, delay, amplitude, offset, load_impedance, source_impedance, polarity):
        """
        Configures the waveform to be generated on the selected channel. Calls the set_waveform, set_frequency, set_delay, set_amplitude, set_offset, set_load_impedance, set_source_impedance and set_polarity functions to configure the waveform
        args:
            channel (int): The channel to configure the waveform on
            waveform (str): The waveform to be generated
            frequency (float): The frequency of the waveform in Hz
            delay (float): The delay of the waveform in seconds
            amplitude (float): The amplitude of the waveform in volts
            offset (float): The offset of the waveform in volts
            load_impedance (float): The load impedance of the waveform in ohms
            source_impedance (float): The source impedance of the waveform in ohms
            polarity (str): The polarity of the waveform
        """
    #functions that are specific to waveform types

    #First for square waves
    def set_duty_cycle(self, channel, duty_cycle):
        """
        Sets the duty cycle of the waveform to be generated on the selected channel
        Useful for square waves
        args:
            channel (int): The channel to set the duty cycle on
            duty_cycle (float): The duty cycle of the waveform as a percentage (0-100)
        """
    #Now for triangular and ramp waves
    def set_symmetry(self, channel, symmetry):
        """
        Sets the symmetry of the waveform to be generated on the selected channel
        Useful for triangular and ramp waves
        args:
            channel (int): The channel to set the symmetry on
            symmetry (float): The symmetry of the waveform as a percentage (0-100)
        """
    #Now for pulses
    def set_pulse_width(self, channel, pulse_width):
        """
        Sets the pulse width of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the pulse width on
            pulse_width (float): The pulse width of the waveform in seconds
        """
    def set_pulse_rise_time(self, channel, rise_time):
        """
        Sets the rise time of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the rise time on
            rise_time (float): The rise time of the waveform in seconds
        """
    def set_pulse_fall_time(self, channel, fall_time):
        """
        Sets the fall time of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the fall time on
            fall_time (float): The fall time of the waveform in seconds
        """
    def configure_pulse(self, channel, pulse_width, rise_time, fall_time):
        """
        Configures the pulse waveform on the selected channel. Calls the set_pulse_width, set_pulse_rise_time, and set_pulse_fall_time functions to configure the pulse waveform
        args:
            channel (int): The channel to configure the pulse waveform on
            pulse_width (float): The pulse width of the waveform in seconds
            rise_time (float): The rise time of the waveform in seconds
            fall_time (float): The fall time of the waveform in seconds
        """

    #Now we move to the arb functions
    def create_arb_waveform(self, channel, name, data):
        """
        Creates an arbitrary waveform to be generated on the selected channel and saves to instrument memory if applicable. If no name is given, it will be generated with a default name. Typically
        corresponding to the volatile memory of the instrument. In the case where the given name already exists, it will prompt the user to overwrite or not.
        args:
            channel (int): The channel to create the arbitrary waveform on
            name (str): The name of the arbitrary waveform
            data (list or ndarray): The data points of the arbitrary waveform
        """
    def set_arb_waveform(self, channel, name):
        """
        Sets the arbitrary waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the arbitrary waveform on
            name (str): The name of the arbitrary waveform to be set
        """
    
    #modulation functions
    #skip for now, not needed yet

    #burst and sweep functions
    #skip for now, not needed yet

    #trigger and sync functions
    def set_trigger_source(self, channel, source):
        """
        Sets the trigger source for the selected channel
        args:
            channel (int): The channel to set the trigger source on
            source (str): The trigger source, e.g., 'internal', 'external', 'manual'
        """
    def set_trigger_level(self, channel, level):
        """
        Sets the trigger level for the selected channel
        args:
            channel (int): The channel to set the trigger level on
            level (float): The trigger level in volts
        """
    def set_trigger_slope(self, channel, slope):
        """
        Sets the trigger slope for the selected channel
        args:
            channel (int): The channel to set the trigger slope on
            slope (str): The trigger slope, e.g., 'rising', 'falling'
        """
    def set_trigger_mode(self, channel, mode):
        """
        Sets the trigger mode for the selected channel
        args:
            channel (int): The channel to set the trigger mode on
            mode (str): The trigger mode, e.g., 'auto', 'normal', 'single'
        """
    def configure_trigger(self, channel, source, level, slope, mode):
        """
        Configures the trigger for the selected channel. Calls the set_trigger_source, set_trigger_level, set_trigger_slope, and set_trigger_mode functions to configure the trigger
        args:
            channel (int): The channel to configure the trigger on
            source (str): The trigger source
            level (float): The trigger level in volts
            slope (str): The trigger slope
            mode (str): The trigger mode
        """
    #maybe impedance for trigger as well? But maybe some wont have this
    

