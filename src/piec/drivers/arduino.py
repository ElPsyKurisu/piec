"""
Set's up the arduino instrument class that all arduino instruments will inherit basic functionlity from.

"""

from instrument import Instrument

class Arduino_Stepper(Instrument):
    """
    Custom Class for using an arduino as a stepper motor driver. See https://github.com/ElPsyKurisu/STFMR/tree/main/Arduino for more information
    """
    def step(self, num_steps, direction):
        """
        Steps the stepper motor 
        args:
            self (pyvisa.resources.asrl.not sure): Arduino
            num_steps (str/int): Desired step size, must be an integer value
            direction (str/int): [0,1] are the ONLY allowed values, 0 for CW 1 for CCW (not could be backwards)
        """
        self.write("{},{}".format(num_steps, direction)) #specially formatted string for arduino code to work. See https://github.com/ElPsyKurisu/STFMR/tree/main/Arduino for more information
    
    def set_zero(self):
        """
        Hardcoded command that sets the arduinos position tracker to zero
        """
        self.step(0,9)

    def read_position(self):
        """
        Reads the current position without stepping the stepper
        """
        self.step(0,99)
        return self.read()

