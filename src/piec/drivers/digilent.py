"""
Digilent/MCC Universal Library (UL) Instrument Driver.
"""
from .instrument import Instrument

# --- Import the actual MCC Universal Library ---
try:
    from mcculw import ul
    from mcculw.enums import BoardInfo, ErrorCode, InterfaceType
    from mcculw.ul import ULError
    from mcculw.device_info import DaqDeviceInfo
    MCC_UL_IMPORTED = True
except ImportError:
    print("Warning: 'mcculw' library not found. Digilent drivers will be forced to VIRTUAL mode.")
    ul = None
    MCC_UL_IMPORTED = False

class Digilent(Instrument):
    """
    Parent class for Digilent/MCC instruments using the Universal Library (UL).
    
    This class acts as the interface layer. It bypasses the standard VISA connection
    logic of the parent 'Instrument' class because MCC devices use a C-library wrapper 
    (mcculw) instead of SCPI commands.
    """
    
    def __init__(self, address, board_num=0, check_params=False, **kwargs):
        """
        Args:
            address (str): The unique identifier for the device.
                           - If "VIRTUAL", runs in simulation mode.
                           - Otherwise, treated as a Product ID (e.g. "10141") 
                             or Unique ID to find the board.
            board_num (int): The logical board number (0-99) to assign in the UL software.
                             Default is 0.
            check_params (bool): Enable/Disable the AutoCheck parameter validation.
        """
        
        # 1. THE BYPASS: 
        # We pass "VIRTUAL" to the parent class regardless of the real mode.
        # This prevents PiecManager from trying (and failing) to open 'address' 
        # as a VISA resource, while still setting up the parameter checking framework.
        super().__init__("VIRTUAL", check_params=check_params, **kwargs)

        # 2. Determine Actual State
        # Now we check if the user *actually* wanted virtual mode.
        user_requested_virtual = (str(address).upper() == 'VIRTUAL')
        
        # If the library is missing, we must force virtual
        if not MCC_UL_IMPORTED:
            self.virtual = True
            if not user_requested_virtual:
                print("Digilent: Defaulting to VIRTUAL mode (mcculw library missing).")
        else:
            # Restore the user's intended state
            self.virtual = user_requested_virtual

        # 3. Connect to Real Hardware
        self.board_num = int(board_num)
        self.ul = ul  # Expose library to child classes
        
        if not self.virtual:
            self._connect_device(address, self.board_num)
        else:
            print(f"Digilent: Initialized VIRTUAL device (Address: {address})")

    def _connect_device(self, identifier, board_num):
        """
        Locates the specific device by ID and assigns it to the board number.
        """
        try:
            # Ignore Instacal to allow manual configuration (prevents conflicts)
            # Only necessary for the first board we configure
            if board_num == 0:
                try: self.ul.ignore_instacal()
                except: pass

            print(f"Digilent: Searching for device '{identifier}'...")
            devices = self.ul.get_daq_device_inventory(InterfaceType.ANY)
            
            target_device = None
            id_str = str(identifier).strip()

            # Try to match Product ID or Unique ID
            for device in devices:
                if id_str == str(device.product_id) or id_str == str(device.unique_id):
                    target_device = device
                    break
            
            # Fallback: If user passed "0" or "1" (like an index), just grab the first found
            if target_device is None and id_str.isdigit() and len(devices) > 0:
                 print(f"Digilent: ID '{id_str}' not found by name, using first discovered device.")
                 target_device = devices[0]

            if not target_device:
                found_list = [f"{d.product_name} (ID: {d.unique_id})" for d in devices]
                raise ConnectionError(f"Device '{identifier}' not found. Found: {found_list}")

            # Create the connection
            self.ul.create_daq_device(board_num, target_device)
            print(f"Digilent: Connected to {target_device.product_name} ({target_device.unique_id}) as Board {board_num}")

        except Exception as e:
            # If connection fails, we raise an error (or you could fallback to virtual here)
            raise ConnectionError(f"Failed to configure Digilent device: {e}")

    def idn(self):
        """
        Overrides the standard SCPI *IDN? query.
        """
        if self.virtual:
            return "Measurement_Computing,VIRTUAL_DEVICE,0000,1.0"
        try:
            # MCC UL doesn't have a standard "Get Serial" command for all boards easily accessible
            # via a single call, but getting the board name verifies communication.
            name = self.ul.get_board_name(self.board_num)
            return f"Measurement_Computing,{name},Unknown_SN,UL_Wrapper"
        except Exception as e:
            return f"Error retrieving ID: {e}"

    def flash_led(self):
        """
        Flashes the onboard LED to identify the physical unit.
        """
        if self.virtual:
            print(f"Digilent [Virt]: Flashing LED on Board {self.board_num}")
            return
        try:
            self.ul.flash_led(self.board_num)
        except Exception as e:
            print(f"Digilent: Flash LED failed (Board might not support it). Error: {e}")

    def close(self):
        """
        Releases the board handle.
        """
        if self.virtual: return
        try:
            self.ul.release_daq_device(self.board_num)
            print(f"Digilent: Released Board {self.board_num}")
        except:
            pass