
import sys
import os

# Ensure we can import the piec module
sys.path.append(os.path.join(os.getcwd(), 'src'))

from piec.drivers.digilent import Digilent
from piec.drivers.autodetect import autodetect
from piec.drivers.scpi import Scpi

print("--- Testing Digilent Direct Instantiation (Verbose=False) ---")
try:
    d = Digilent(address="VIRTUAL", verbose=False)
    # Success message comes from Digilent.__init__
    d.close()
except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing Autodetect Digilent (Verbose=False) ---")
# Success message comes from Digilent.__init__ being called by autodetect
inst = autodetect(address="VIRTUAL", verbose=False, required_type=Digilent)
if inst:
    inst.close()

print("\n--- Testing Autodetect SCPI Direct (Verbose=False) ---")
# This should print "Autodetect: connected to generic SCPI..."
# Note: VIRTUAL address falls back to VIRTUAL mode in Instrument, but autodetect treats checks "::" for SCPI logic.
# We need a fake VISA address to trigger SCPI logic in autodetect.
try:
    # This might fail actual connection but trigger the SCPI block
    # Scpi init will fallback to Virtual if real connection fails.
    # But autodetect probe "temp_inst.instrument.query" might fail and catch exception.
    # To test the SUCCESS path, we need a working mock or rely on code inspection.
    # However, we can try to force it.
    pass
except Exception:
    pass

# We can manually invoke the functionality by using a VIRTUAL address that LOOKS like VISA?
# But autodetect checks "::". 
# "GPIB::1::INSTR"
print("Attempting to trigger SCPI logic with fake address 'GPIB::1::INSTR' (Will likely fail connection)")
inst = autodetect(address="GPIB::1::INSTR", verbose=False)
# This will likely fail probe and return None, printing nothing (verbose=False).

print("\nTests Complete")
