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
        """
        Connects to the instrument by opening a ResourceManager and talking to it (use PiecManager)
        Sets the instrument timeout and the steps_per_revolution to ensure (hardcode this value based on hardware specs)
        """

    def idn(self):
        """
        Overwrites idn functionality to work with arduino
        """
    
    def step(self, num_steps, direction):
        """
        Steps the stepper motor by sending a write string (via query) where the format is "{steps},{direction}"
        where direction = 0 is for CW and 1 is for CCW
        returns the current position after the stepper stops moving
        args:
            self (pyvisa.resources.asrl.not sure): Arduino
            num_steps (str/int): Desired step size, must be an integer value
            direction (str/int): [0,1] are the ONLY allowed values, 0 for CW 1 for CCW (not could be backwards)
        returns:
            current_position (int) The current position as read from the arduino
        """

    def set_zero(self):
        """
        Hardcoded command that sets the arduinos position tracker to zero. Sends a direction = 9 to set the zero
        """

    def read_position(self):
        """
        Reads the current position without stepping the stepper by sending in zero steps
        since the arduino already returns position with each step
        """