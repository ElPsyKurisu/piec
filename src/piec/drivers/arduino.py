"""
Set's up the arduino instrument class that all arduino instruments will inherit basic functionlity from.

"""

from .instrument import Instrument
import time
import re
import pyvisa
from pyvisa import ResourceManager
class Arduino_Stepper(Instrument):
    """
    Custom Class for using an arduino as a stepper motor driver. See https://github.com/ElPsyKurisu/STFMR/tree/main/Arduino for more information
    """
    def __init__(self, address):
        rm = ResourceManager()
        self.instrument = rm.open_resource(address)
        self.instrument.timeout = 20000 #20s

    def idn(self):
        return "Custom Arduino_Stepper Object at {}".format(self.instrument.resource_name)
    
    def step(self, num_steps, direction):
        """
        Steps the stepper motor 
        args:
            self (pyvisa.resources.asrl.not sure): Arduino
            num_steps (str/int): Desired step size, must be an integer value
            direction (str/int): [0,1] are the ONLY allowed values, 0 for CW 1 for CCW (not could be backwards)
        returns:
            current_position (int) The current position as read from the arduino
        """
        self.instrument.write("{},{}".format(num_steps, direction)) #specially formatted string for arduino code to work. See https://github.com/ElPsyKurisu/STFMR/tree/main/Arduino for more information
        try:
            while True:
                # Read a line from the Arduino
                line = self.instrument.read().strip()
                #print(f"Received: {line}")
                number = int(re.search(r'-?\d+', line).group())
                
                # Check if the line contains the "complete" message
                if "Complete" in line:
                    #print("Arduino has completed the task.")
                    return number
                
        except pyvisa.errors.VisaIOError as e: 
            if e.error_code == pyvisa.constants.VI_ERROR_TMO:
                print("Timeout error occurred while waiting for the Arduino.")


    def set_zero(self):
        """
        Hardcoded command that sets the arduinos position tracker to zero
        """
        self.step(0,9)

    def read_position(self):
        """
        Reads the current position without stepping the stepper
        """
        position = self.step(0,99)
        if position is not None:
            return position
        else:
            print("position unknown")

