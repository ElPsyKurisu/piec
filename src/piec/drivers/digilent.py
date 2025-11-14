"""
This is the parent class for MCC (formerly Digilent) DAQ devices
that use the Measurement Computing Universal Library (UL).

It inherits from Instrument and provides a common connection,
identification, and utility framework for all UL-based devices.

This driver requires the 'mcculw' library to be installed.
"""

from .instrument import Instrument

# --- Import the actual MCC Universal Library ---
# We try to import the library. If it fails, we set the
# library objects to None and the driver will raise an
# error on initialization.
try:
    from mcculw import ul
    from mcculw.enums import BoardInfo, ErrorCode
    from mcculw.ul import ULError
    mcc_ul_imported = True
except ImportError:
    print("Warning: 'mcculw' library not found.")
    print("The Digilent/MCC driver cannot be used without this library.")
    ul = None
    BoardInfo = None
    ErrorCode = None
    ULError = None
    mcc_ul_imported = False


class Digilent(Instrument):
    """
    Parent class for Digilent/MCC instruments using the Universal Library.
    
    This class handles the connection and board identification,
    replacing the VISA/PiecManager logic from the Scpi class.
    
    The 'address' for this class is the MCC Board Number (e.g., "0").
    """
    
    def __init__(self, address, **kwargs):
        """
        Connects to the MCC DAQ device using its Board Number.
        
        Args:
            address (str or int): The MCC Board Number (e.g., "0" or 0)
                                or "VIRTUAL".
            **kwargs: Additional arguments for the base Instrument class.
        """
        # --- Check if the required library was imported ---
        if not mcc_ul_imported or ul is None:
            raise ImportError(
                "The 'mcculw' library is not installed. "
                "This driver cannot function without it. "
                "Please install it (e.g., 'pip install mcculw')."
            )

        # --- FIX: Store the user's intended mode ---
        # We check the 'address' passed by the user, not the 'self.virtual'
        # flag from the parent, which is always True.
        self.is_virtual_mode = (str(address).upper() == 'VIRTUAL')

        try:
            # The 'address' is the board number, not a VISA string
            self.board_num = int(address)
        except (ValueError, TypeError):
            if self.is_virtual_mode:
                # This is a VIRTUAL connection
                self.board_num = 0 
            else:
                # This is an invalid address
                raise ValueError(f"Invalid address '{address}'. "
                                 "Must be a MCC Board Number (e.g., '0') or 'VIRTUAL'.")
        
        # We call super().__init__ with "VIRTUAL" to bypass PiecManager
        # but still get the auto-check framework. This is internal.
        super().__init__(address="VIRTUAL", **kwargs)
        
        # Store the (real) UL object and enums
        self.board = ul
        self.ul_error = ULError
        self.error_codes = ErrorCode
        
        # --- FIX: Check our stored 'is_virtual_mode' flag ---
        if self.is_virtual_mode:
            print(f"Digilent: VIRTUAL mode for board {self.board_num}.")
            self.dev_name = "VIRTUAL_DEVICE"
        else:
            # This is a real connection attempt
            print(f"Digilent: Connecting to board {self.board_num}...")
            try:
                # Check if board exists and get its name
                self.dev_name = self.board.get_board_name(self.board_num)
                print(f"Digilent: Connected to {self.dev_name} on board {self.board_num}.")
            except ULError as e:
                raise ConnectionError(f"Failed to connect to MCC board {self.board_num}. Error: {e}")

    def idn(self):
        """
        Returns an identification string from the Universal Library.
        This is the UL-equivalent of the SCPI *IDN? command.
        """
        if self.is_virtual_mode:
            return f"Measurement_Computing,VIRTUAL_DEVICE,s/n_virtual,ver_UL"
        
        try:
            # Re-fetch the name in case it changed (unlikely, but good practice)
            dev_name = self.board.get_board_name(self.board_num)
            # Serial number retrieval is not a standard UL call, so
            # we provide a placeholder.
            serial = "s/n_unknown"
            return f"Measurement_Computing,{dev_name},{serial},ver_UL"
        except self.ul_error as e:
            print(f"Digilent: Could not get IDN. Error: {e}")
            return "Measurement_Computing,Unknown_Device,s/n_unknown,ver_UL_error"

    # --- Base Universal Library Commands ---

    def flash_led(self):
        """
        Flashes the LED on the device to physically identify it.
        (Note: Not supported by all boards, e.g., USB-231)
        """
        if self.is_virtual_mode:
            print(f"Digilent: (Virtual) Flashing LED on board {self.board_num}...")
            return
            
        try:
            print(f"Digilent: Flashing LED on board {self.board_num}...")
            self.board.flash_led(self.board_num)
        except self.ul_error as e:
            # We will just print the error, as this is a non-critical function
            print(f"Digilent: Could not flash LED. Error: {e}")

    def get_last_error(self):
        """
        Gets the error message string for a given error code.
        The default (NOERRORS) returns "No errors."
        
        Returns:
            str: The error message.
        """
        if self.is_virtual_mode:
            return "No errors."
            
        try:
            # --- FIX: Corrected function name from get_error_message to get_err_msg ---
            message = self.board.get_err_msg(self.error_codes.NOERRORS)
            return message
        except self.ul_error as e:
            return f"Failed to get error message. Error: {e}"
        except AttributeError:
            # This handles the case where the ul object itself is missing the function
            return "Error: ul.get_err_msg function not found. Is 'mcculw' installed correctly?"
    
    def close(self):
        """
        Releases the DAQ device from the Universal Library.
        """
        if self.is_virtual_mode:
            print(f"Digilent: (Virtual) Releasing board {self.board_num}...")
            return

        try:
            print(f"Digilent: Releasing board {self.board_num}...")
            self.board.release_daq_device(self.board_num)
        except self.ul_error as e:
            print(f"Digilent: Error releasing device. Error: {e}")