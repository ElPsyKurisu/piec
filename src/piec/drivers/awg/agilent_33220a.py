# This driver has not been tested yet
from ..scpi import Scpi
from .awg import Awg

class Agilent33220A(Scpi, Awg):
    """
    Driver for the Agilent 33220A Arbitrary Waveform Generator.
    """
    
    # Class attributes for parameter restrictions
    AUTODETECT_ID = "33220A"
    
    channel = [1]
    waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    
    # Frequency ranges depend on the function
    # Sine/Square: 1uHz to 20MHz
    # Ramp: 1uHz to 200kHz
    # Pulse: 500uHz to 5MHz
    # Noise: None (fixed bandwidth)
    # DC: None
    # User (Arb): 1uHz to 6MHz
    frequency = {
        'waveform': {
            'SIN': (1e-6, 20e6),
            'SQU': (1e-6, 20e6),
            'RAMP': (1e-6, 200e3),
            'PULS': (500e-6, 5e6),
            'NOIS': None,
            'DC': None,
            'USER': (1e-6, 6e6)
        }
    }
    
    # Amplitude: 10 mVpp to 10 Vpp into 50 ohms
    amplitude = (0.01, 10.0)
    
    # Offset: +/- 5V into 50 ohms
    offset = (-5.0, 5.0)
    
    # Phase: -360 to +360 degrees
    phase = (-360.0, 360.0)
    
    # Duty Cycle (Square): 20% to 80% (varies by freq, simplifying to widely valid range)
    # Manual says: 20% to 80% (to 10 MHz), 40% to 60% (to 20 MHz)
    duty_cycle = (20.0, 80.0)
    
    # Symmetry (Ramp): 0% to 100%
    symmetry = (0.0, 100.0)
    
    # Pulse Width: 20ns to 2000s
    pulse_width = (20e-9, 2000.0)
    
    # Pulse Period: 200ns to 2000s
    pulse_period = (200e-9, 2000.0)
    
    # Edge Time (Rise/Fall): 5ns to 100ns
    edge_time = (5e-9, 100e-9)
    


    def __init__(self, resource_name, **kwargs):
        super().__init__(resource_name, **kwargs)

    def output(self, channel=1, on=True):
        """
        Turn the output on or off.
        """
        state = "ON" if on else "OFF"
        self.instrument.write(f"OUTP {state}")

    def set_waveform(self, channel=1, waveform="SIN"):
        """
        Set the waveform shape.
        """
        self.instrument.write(f"FUNC {waveform}")

    def set_frequency(self, channel=1, frequency=1000):
        """
        Set the frequency in Hz.
        """
        self.instrument.write(f"FREQ {frequency}")

    def set_amplitude(self, channel=1, amplitude=1.0):
        """
        Set the amplitude in Vpp.
        """
        self.instrument.write(f"VOLT {amplitude}")

    def set_offset(self, channel=1, offset=0.0):
        """
        Set the DC offset in Volts.
        """
        self.instrument.write(f"VOLT:OFFS {offset}")

    def set_phase(self, channel=1, phase=0.0):
        """
        Set the phase in degrees.
        """
        self.instrument.write(f"PHAS {phase}")

    def set_square_duty_cycle(self, channel=1, duty_cycle=50.0):
        """
        Set the duty cycle for square waves in percent.
        """
        self.instrument.write(f"FUNC:SQU:DCYC {duty_cycle}")

    def set_ramp_symmetry(self, channel=1, symmetry=100.0):
        """
        Set the symmetry for ramp waves in percent.
        """
        self.instrument.write(f"FUNC:RAMP:SYMM {symmetry}")

    def set_pulse_width(self, channel=1, width=1e-3):
        """
        Set the pulse width in seconds.
        """
        self.instrument.write(f"FUNC:PULS:WIDT {width}")

    def set_pulse_edge_time(self, channel=1, edge_time=5e-9):
        """
        Set the edge time (both rise and fall) in seconds.
        The 33220A has a single command for edge transition time.
        """
        self.instrument.write(f"FUNC:PULS:TRAN {edge_time}")
    
    # Mapping base AWG methods to specific implementation
    def set_pulse_rise_time(self, channel=1, rise_time=5e-9):
        self.set_pulse_edge_time(channel, rise_time)

    def set_pulse_fall_time(self, channel=1, fall_time=5e-9):
        self.set_pulse_edge_time(channel, fall_time)
        
    def set_pulse_duty_cycle(self, channel=1, duty_cycle=50.0):
        """
        Set pulse duty cycle. The 33220A uses pulse width primarily, 
        but we can calculate width if needed or use DCYC if supported.
        33220A Manual: FUNC:PULS:DCYC
        """
        self.instrument.write(f"FUNC:PULS:DCYC {duty_cycle}")
