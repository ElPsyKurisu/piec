"""
Virtual Instrument Base Module

This module provides the base class for virtual instruments used in simulation and testing.
It handles shared sample management and default material properties for ferroelectric simulations.
"""

from piec.simulations.fe_material import Ferroelectric
from piec.drivers.instrument import Instrument

class VirtualInstrument(Instrument):
    """
    Base class for all virtual instruments that share a common sample instance.
    
    This class manages a shared ferroelectric sample across all virtual instruments,
    ensuring consistent material properties and state during simulations.
    
    Attributes:
        _shared_sample (Ferroelectric): Class-level shared sample instance
        sample (Ferroelectric): Instance-level reference to shared sample
    """

    _shared_sample = None

    def __init__(self, *args, **kwargs):
        """
        Initialize virtual instrument with default ferroelectric sample if none exists.
        
        Creates a default Ferroelectric sample with PbTiO3-like properties on first instantiation.
        Subsequent instances will share the same sample object.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if VirtualInstrument._shared_sample is None:
            default_material = {
                'ferroelectric': {
                    # Core Landau coefficients derived from Haun et al. for PZT 53/47
                    'a0': 2*(-5.88e7)/(400-23),      # J m / (C^2 K)
                    'b': 4*(4.764e7),      # J m^5 / C^4 (Negative for first-order transition)
                    'c': 6*(2.336e8),       # J m^9 / C^6
                    'T0': 273+400,         # Curie-Weiss Temp (K), converted from 231.5 C
                    
                    # Electromechanical and elastic constants from literature for PZT
                    'Q12': -4.6e-2,     # m^4 / C^2 (Electrostrictive coefficient)
                    's11': 14.1e-12,   # m^2 / N (Elastic compliance)
                    's12': -4.56e-12,  # m^2 / N (Elastic compliance)
                    
                    # Assumed device parameters
                    'lattice_a': 0.406e-9, # meters, typical for PZT near MPB
                    "film_thickness": 30e-9,  # meters
                    'epsilon_r': 500,     # A reasonable background permittivity for PZT
                    'leakage_resistance': 5e19, # Ohms (Set high to ensure a clear ferroelectric loop)
                },
                'substrate': { #SRO
                    
                    'lattice_a': 0.395e-9 # meters
                    
                },
                'electrode': { #YBCO
                    'screening_lambda': 0.1e-9, # meters
                    'permittivity_e': 7.0e6, # dimensionless
                    'area': (40e-6)**2 # meters^2
                }
            } 
            VirtualInstrument._shared_sample = Ferroelectric(material_dict=default_material)
            VirtualInstrument._shared_sample.name = "virtual_sample"
        self.sample = VirtualInstrument._shared_sample

    @classmethod
    def set_virtual_sample(cls, sample):
        """
        Set a new shared sample for all virtual instruments.

        Args:
            sample (Ferroelectric): New ferroelectric sample instance to share
        """
        cls._shared_sample = sample

    @property
    def virtual_sample(self):
        """
        Get the current shared sample instance.

        Returns:
            Ferroelectric: Current shared sample instance
        """
        return self._shared_sample

    @virtual_sample.setter
    def virtual_sample(self, sample):
        """
        Set a new shared sample for all instances of this class.

        Args:
            sample (Ferroelectric): New ferroelectric sample instance to share
        """
        self.__class__._shared_sample = sample
