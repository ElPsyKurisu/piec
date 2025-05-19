"""
This is an outline for how the arduino_stepper.py file should be like
"""
import time
import re
from pyvisa import ResourceManager
from ...stepper_motor import Stepper

class Geos_Stepper(Stepper):
    """
    This is the base level - instrument specific of the Arduino_Stepper used in our lab
    """
    def __init__(self, address):
        rm = ResourceManager()
        self.instrument = rm.open_resource(address, baud_rate=115200)
        self.instrument.timeout = 20000 #20s
        self.steps_per_revolution = 200 #default value, only change IFF change in hardware is also managed

    def idn(self):
        line = self.instrument.query('0,0') #calls in builtin method to check if serial communication works
        if "Complete" in line:
            return "Custom Arduino_Stepper Object at {}".format(self.instrument.resource_name)
                
        else:
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
        answer = self.instrument.query("{},{}".format(num_steps, direction)) #specially formatted string for arduino code to work. See arduino code under src\piec\drivers\arduino\motor_control_serial_piec\motor_control_serial_piec.ino for more information
        number = int(re.search(r'-?\d+', answer).group())
                
        if "Complete" in answer:
            return number
                
        else: 
            print("Did not complete task")


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