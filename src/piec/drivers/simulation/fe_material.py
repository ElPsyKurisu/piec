"""
The purpose of this script is to create a material that can simulate whatever we want in a FE material. Goal is to be able to have a realistic FE material
that combines resistor, with dielectric with fe

ASSUMES: You pass in a V(t) you wanna apply, lets assume its 2 numpy arrays for now one is v other is t each of the same length

NOTE: Does it make sense to give it an I(t) or a V(t)? on the awg we do V(t) but for resistor than you just get a flat line
"""

class Material:
    """
    This material is the parent class that literally does nothing but passes the trace through it
    """
    def __init__(self):
        self.name = "pass_through"

    def voltage_response(self, v,t):
        """
        Returns the voltage and time arrays back
        NOTE: do we even need the t array? ima say yes since we can use the dielectric equation etc.
        
        args:
            v (ndarray): voltage array of the applied waveform
            t (ndarray): time array of the applied waveform
        """
        return v,t

class Resistor(Material):
    """
    This class simulates a resistor and be default it has 1kohm. units is in SI units
    """
    def __init__(self, resistance=1e3):
        self.resistance = resistance
        self.name = "resistor"
    
    def voltage_response(self, v, t):
        """
        Returns a linear response
        NOTE: do we even need the t array? ima say yes since we can use the dielectric equation etc.
        
        args:
            v (ndarray): voltage array of the applied waveform
            t (ndarray): time array of the applied waveform
        """ 
        return v/self.resistance, t
    



