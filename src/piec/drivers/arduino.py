"""
Set's up the arduino instrument class that all arduino instruments will inherit basic functionlity from.

"""

from piec.drivers.instrument import Instrument
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
        self.instrument = rm.open_resource(address, baud_rate=115200)
        self.instrument.timeout = 10000 #10s

    def idn(self):
        self.instrument.write("0,99") #calls in builtin method to check if serial communication works
        start_time = time.time()
        try:
            while True:
                # Check if 5 seconds have passed
                if time.time() - start_time > 5:
                    raise pyvisa.errors.VisaIOError(pyvisa.constants.VI_ERROR_TMO)
                
                # Read a line from the Arduino
                line = self.instrument.read().strip()
                
                # Check if the line contains the "Connected" message
                if "Connected" in line:
                    return "Custom Arduino_Stepper Object at {}".format(self.instrument.resource_name)
                
        except pyvisa.errors.VisaIOError as e: 
            if e.error_code == pyvisa.constants.VI_ERROR_TMO:
                print("Timeout error occurred while waiting for the Arduino.")
                return "Not connected"
    
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
        time.sleep(2) #ensure that arduino has time to recieve the data
        self.step(0,9)

    def read_position(self):
        """
        Reads the current position without stepping the stepper
        """
        time.sleep(2) #ensure that arduino has time to recieve the data
        position = self.step(0,0) #steps 0 steps, so doesnt change position
        if position is not None:
            return position
        else:
            print("Position unknown")

