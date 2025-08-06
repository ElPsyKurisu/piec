# VirtualInstrument and VirtualSample base classes
from piec.simulations.fe_material import Ferroelectric
from piec.drivers.instrument import Instrument

class VirtualInstrument(Instrument):
    _shared_sample = None

    def __init__(self, *args, **kwargs):
        if VirtualInstrument._shared_sample is None:
            #from .virtual_sample import VirtualSample  # or wherever your sample class is
            default_material = {
                'ferroelectric': {
                    'a0': 824800,  # J m / (C^2 K)
                    'b': -838800000, # J m^5 / C^4 (Negative for first-order transition)
                    'c': 7764000000,  # J m^9 / C^6
                    'T0': 388,    # Curie-Weiss Temp (K)
                    'Q12': -0.034, # m^4 / C^2 (Electrostrictive coefficient)
                    's11': 12.7e-12, # m^2 / N (Elastic compliance)
                    's12': -4.2e-12, # m^2 / N (Elastic compliance)
                    'lattice_a': 0.402e-9, # meters, 
                    "film_thickness": 10e-9, # meters
                    'epsilon_r': 400, # no unit
                    'leakage_resistance' : 5e3, # Ohms
                },
                'substrate': { #STO
                    
                    'lattice_a': 0.3905e-9 # meters
                    
                },
                'electrode': { #pt
                    'screening_lambda': 0.05e-9, # meters
                    'permittivity_e': 8.0, # dimensionless
                    'area': (20e-6)**2 # meters^2
                }
            } 
            VirtualInstrument._shared_sample = Ferroelectric(material_dict=default_material)
            VirtualInstrument._shared_sample.name = "virtual_sample"
        self.sample = VirtualInstrument._shared_sample

    @classmethod
    def set_virtual_sample(cls, sample):
        cls._shared_sample = sample

    @property
    def virtual_sample(self):
        return self._shared_sample

    @virtual_sample.setter
    def virtual_sample(self, sample):
        self.__class__._shared_sample = sample
