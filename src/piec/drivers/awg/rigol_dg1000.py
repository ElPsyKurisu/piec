# This driver has not been tested yet
from ..scpi import Scpi
from .awg import Awg

class RigolDG1000(Scpi, Awg):
    """
    Driver for the Rigol DG1000 Series Arbitrary Waveform Generators.
    and DG1000Z series.
    """
    
    # "RIGOL TECHNOLOGIES,DG1022,..."
    AUTODETECT_ID = "DG1"
    
    channel = [1, 2]
    
    waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    
    # Frequency: 1uHz to 25MHz (DG1022Z) or up to 60MHz (DG1062Z)
    # Using 60MHz to support the top end; instrument will error if out of range for specific model.
    frequency = {
        'waveform': {
            'SIN': (1e-6, 60e6),
            'SQU': (1e-6, 25e6),
            'RAMP': (1e-6, 500e3), # DG1000Z ramp max is usually lower
            'PULS': (1e-6, 25e6), 
            'NOIS': (1e-6, 25e6), # Bandwidth
            'DC': None,
            'USER': (1e-6, 20e6)
        }
    }
    
    # Amplitude: 1mVpp to 10Vpp (50 ohm)
    amplitude = (0.001, 10.0)
    
    # Offset: +/- 5V (50 ohm)
    offset = (-5.0, 5.0)
    
    phase = (0.0, 360.0)
    
    # Duty Cycle (Square): 1% to 99% (limited by freq)
    duty_cycle = (1.0, 99.0)
    
    # Symmetry (Ramp): 0% to 100%
    symmetry = (0.0, 100.0)
    
    # Pulse Width
    pulse_width = (16e-9, 1000.0)
    


    def __init__(self, resource_name, **kwargs):
        super().__init__(resource_name, **kwargs)

    def output(self, channel=1, on=True):
        state = "ON" if on else "OFF"
        self.instrument.write(f"OUTP{channel} {state}")

    def set_waveform(self, channel=1, waveform="SIN"):
        # Rigol uses APPLy or FUNC
        # FUNC is better for just changing shape without changing parameters
        # However, Rigol DG1000Z manual says "SOURce[n]:FUNCtion[:SHAPe]"
        self.instrument.write(f"SOUR{channel}:FUNC {waveform}")

    def set_frequency(self, channel=1, frequency=1000):
        self.instrument.write(f"SOUR{channel}:FREQ {frequency}")

    def set_amplitude(self, channel=1, amplitude=1.0):
        self.instrument.write(f"SOUR{channel}:VOLT {amplitude}")

    def set_offset(self, channel=1, offset=0.0):
        self.instrument.write(f"SOUR{channel}:VOLT:OFFS {offset}")

    def set_phase(self, channel=1, phase=0.0):
        self.instrument.write(f"SOUR{channel}:PHAS {phase}")

    def set_square_duty_cycle(self, channel=1, duty_cycle=50.0):
        self.instrument.write(f"SOUR{channel}:FUNC:SQU:DCYC {duty_cycle}")

    def set_ramp_symmetry(self, channel=1, symmetry=100.0):
        self.instrument.write(f"SOUR{channel}:FUNC:RAMP:SYMM {symmetry}")

    def set_pulse_width(self, channel=1, width=1e-3):
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:WIDT {width}")
        
    def set_pulse_duty_cycle(self, channel=1, duty_cycle=50.0):
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:DCYC {duty_cycle}")
    
    # Rigol DG1000Z might not support variable edge time on all models, usually fixed or limited.
    # DG1000Z manual check: SOURce[n]:FUNCtion:PULSe:TRANsition 
    def set_pulse_edge_time(self, channel=1, edge_time=8e-9):
         self.instrument.write(f"SOUR{channel}:FUNC:PULS:TRAN {edge_time}")

    def set_pulse_rise_time(self, channel=1, rise_time=8e-9):
         self.set_pulse_edge_time(channel, rise_time)

    def set_pulse_fall_time(self, channel=1, fall_time=8e-9):
         self.set_pulse_edge_time(channel, fall_time)
