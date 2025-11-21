"""
This is the parent class for MCC (formerly Digilent) DAQ devices
that use the Measurement Computing Universal Library (UL).

It inherits from Instrument and provides a common connection,
identification, and utility framework for all UL-based devices.

This driver requires the 'mcculw' library to be installed.
"""

from .instrument import Instrument
import sys

# --- Import the actual MCC Universal Library ---
try:
    from mcculw import ul
    from mcculw.enums import BoardInfo, ErrorCode, InterfaceType
    from mcculw.ul import ULError
    from mcculw.device_info import DaqDeviceInfo
    mcc_ul_imported = True
except ImportError:
    print("Warning: 'mcculw' library not found.")
    print("The Digilent/MCC driver cannot be used without this library.")
    ul = None
    BoardInfo = None
    ErrorCode = None
    InterfaceType = None
    ULError = None
    DaqDeviceInfo = None
    mcc_ul_imported = False


class Digilent(Instrument):
    """
    Parent class for Digilent/MCC instruments using the Universal Library.
    
    This class handles the connection and board identification,
    replacing the VISA/PiecManager logic from the Scpi class.
    
    The 'address' for this class is the device's Product ID (e.g., "10141")
    or Unique ID (e.g., "001A9B3B").
    The 'board_num' is the logical handle (e.g., 0) to assign to this device.
    """
    
    def __init__(self, address, board_num=0, check_params=False, **kwargs):
        """
        Connects to the MCC DAQ device.
        
        Args:
            address (str): The Product ID (e.g., "10141"), Unique ID 
                           (e.g., "001A9B3B"), or "VIRTUAL".
                           If None, will connect to the first device found.
            board_num (int): The logical board number to assign to this
                             device (e.g., 0, 1, 2...).
            check_params (bool): Toggle for auto-check framework.
            **kwargs: Additional arguments (not used by Digilent).
        """
        # --- 1. Check if the required library was imported ---
        if not mcc_ul_imported or ul is None:
            raise ImportError(
                "The 'mcculw' library is not installed. "
                "This driver cannot function without it. "
                "Please install it (e.g., 'pip install mcculw')."
            )

        # --- 2. Call super().__init__ with the "VIRTUAL" hack ---
        # This bypasses PiecManager but enables the auto-check framework.
        # We pass "VIRTUAL" regardless of our *actual* mode, because
        # the base class __init__ is hard-coded for VISA.
        #This alloaws us to still use check_params functionality
        super().__init__(address="VIRTUAL", check_params=check_params)
        
        # --- 3. Store our *actual* state ---
        self.is_virtual_mode = (str(address).upper() == 'VIRTUAL')
        self.board = ul
        self.ul_error = ULError
        self.error_codes = ErrorCode
        self.board_num = int(board_num) # The logical handle
        
        # --- 4. Connect or set up VIRTUAL mode ---
        if self.is_virtual_mode:
            print(f"Digilent: VIRTUAL mode for board {self.board_num}.")
            self.dev_name = "VIRTUAL_DEVICE"
            self.ao_info = None # Can be expanded later
            self.ai_info = None # Can be expanded later
        else:
            # This is a real connection attempt
            print(f"Digilent: Locating device '{address}' to map to board {self.board_num}...")
            try:
                # Find and create the device handle
                device = self._config_device(self.board_num, address)
                
                # Get and store device info
                daq_dev_info = DaqDeviceInfo(self.board_num)
                self.dev_name = daq_dev_info.product_name
                
                if daq_dev_info.supports_analog_output:
                    self.ao_info = daq_dev_info.get_ao_info()
                if daq_dev_info.supports_analog_input:
                    self.ai_info = daq_dev_info.get_ai_info()

                print(f"Digilent: Successfully connected to {self.dev_name} ({device.unique_id}) on board {self.board_num}.")

            except Exception as e:
                raise ConnectionError(f"Failed to connect to MCC device '{address}'. Error: {e}")

    def _config_device(self, board_num, dev_address_id=None):
        """
        Finds a device by its ID and creates a board handle for it.
        Adapted from your mccdig.py.
        
        Args:
            board_num (int): The logical board number to assign.
            dev_address_id (str): The Product ID or Unique ID to find.
                                  If None, finds the first device.
        """
        if board_num == 0:
            # Only ignore Instacal on the *first* board created.
            # Subsequent boards (1, 2, ...) must not.
            try:
                ul.ignore_instacal()
            except Exception as e:
                print(f"Warning: Could not ignore Instacal. {e}")

        devices = ul.get_daq_device_inventory(InterfaceType.ANY)
        if not devices:
            raise Exception('Error: No DAQ devices found')

        device_to_map = None
        
        if dev_address_id is None:
            # No ID specified, just grab the first device
            device_to_map = devices[0]
        else:
            # Search for the device by Product or Unique ID
            dev_id_str = str(dev_address_id)
            for dev in devices:
                if str(dev.product_id) == dev_id_str or str(dev.unique_id) == dev_id_str:
                    device_to_map = dev
                    break
        
        if not device_to_map:
            valid_devices = [f"{d.product_name} (PID: {d.product_id}, UID: {d.unique_id})" for d in devices]
            raise Exception(f"Error: No DAQ device found with ID '{dev_address_id}'. \nFound devices: {valid_devices}")

        # Add the found DAQ device to the UL with the specified board number
        ul.create_daq_device(board_num, device_to_map)
        return device_to_map

    def idn(self):
        """
        Returns an identification string from the Universal Library.
        """
        if self.is_virtual_mode:
            return f"Measurement_Computing,VIRTUAL_DEVICE,s/n_virtual,ver_UL"
        
        try:
            # Re-fetch the name
            dev_name = self.board.get_board_name(self.board_num)
            # Serial number retrieval is not a standard UL call
            serial = "s/n_unknown"
            try:
                # Try to get the real unique ID
                serial = DaqDeviceInfo(self.board_num).unique_id
            except:
                pass # Use default if it fails
            return f"Measurement_Computing,{dev_name},{serial},ver_UL"
        except self.ul_error as e:
            print(f"Digilent: Could not get IDN. Error: {e}")
            return "Measurement_Computing,Unknown_Device,s/n_unknown,ver_UL_error"

    def flash_led(self):
        """
        Flashes the LED on the device to physically identify it.
        """
        if self.is_virtual_mode:
            print(f"Digilent: (Virtual) Flashing LED on board {self.board_num}...")
            return
            
        try:
            print(f"Digilent: Flashing LED on {self.dev_name} (board {self.board_num})...")
            self.board.flash_led(self.board_num)
        except self.ul_error as e:
            print(f"Digilent: Could not flash LED. Error: {e}")

    def get_last_error(self):
        """
        Gets the error message string for a given error code.
        """
        if self.is_virtual_mode:
            return "No errors."
        try:
            message = self.board.get_err_msg(self.error_codes.NOERRORS)
            return message
        except Exception as e:
            return f"Failed to get error message: {e}"
    
    def close(self):
        """
        Releases the DAQ device from the Universal Library.
        """
        if self.is_virtual_mode:
            print(f"Digilent: (Virtual) Releasing board {self.board_num}...")
            return

        try:
            print(f"Digilent: Releasing {self.dev_name} (board {self.board_num})...")
            self.board.release_daq_device(self.board_num)
        except self.ul_error as e:
            print(f"Digilent: Error releasing device. Error: {e}")