import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()

cells = [
    new_markdown_cell("# LeCroy SDA 6020 Trigger & Acquisition Test\nThis notebook configures the oscilloscope for a pulsed input on a specific channel, sets up the trigger, scales the X and Y axes, and acquires a waveform."),
    
    new_code_cell("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from piec.drivers.autodetect import autodetect
from piec.drivers.oscilloscope.lecroy_sda6020 import LeCroySDA6020

# Connect to the oscilloscope. You can hardcode the address if needed:
# scope = LeCroySDA6020("GPIB0::7::INSTR")
scope = autodetect("scope", verbose=True)"""),
    
    new_markdown_cell("## 1. Configure the Oscilloscope Display & Scales\nWe select a channel, turn it on, and configure the time and voltage scales."),
    
    new_code_cell("""TARGET_CHANNEL = 1

# Turn the channel on
scope.toggle_channel(TARGET_CHANNEL, on=True)

# Set Vertical Scale: 0.5 Volts/Division, DC 50 Ohm coupling
scope.set_vertical_scale(TARGET_CHANNEL, vdiv=0.5)
scope.set_input_coupling(TARGET_CHANNEL, "DC")
scope.set_channel_impedance(TARGET_CHANNEL, "50")

# Set Horizontal Scale: 1 microsecond/Division, 0 delay
scope.configure_horizontal(tdiv=1e-6, x_position=0.0)"""),
    
    new_markdown_cell("## 2. Configure the Trigger\nHere we set up an EDGE trigger on our target channel with a specific voltage level. We can also specify if we want it to sweep normally (wait for the pulse) or if we want to force it."),
    
    new_code_cell("""# We want to trigger when the pulse passes 1.0V, on a rising edge.
TRIGGER_LEVEL = 1.0  # Volts
TRIGGER_SLOPE = "POS"

# Set up the trigger routing
scope.configure_trigger(
    trigger_source=TARGET_CHANNEL,
    trigger_level=TRIGGER_LEVEL,
    trigger_slope=TRIGGER_SLOPE,
    trigger_mode="EDGE"
)

# Choose your sweep mode:
# "NORM" - Waits strictly for the trigger event (the pulse)
# "AUTO" - Triggers on the pulse if it sees it, otherwise forces a trigger anyway
scope.set_trigger_sweep("NORM")"""),
    
    new_markdown_cell("## 3. Acquire the Waveform\nNow we tell the scope to arm itself, wait for the pulse, and pull down the data once it triggers!"),
    
    new_code_cell("""# Optional: If you want to force the scope to trigger without a pulse, uncomment the line below:
# scope.manual_trigger()

print("Arming scope and waiting for trigger...")
# Arm the scope for a single shot
scope.arm() 

# Set up the acquisition parameters to read out the data
scope.configure_acquisition(channel=TARGET_CHANNEL, acquisition_points=1000)

# get_data() communicates with the scope to pull the waveform into a Pandas DataFrame
df = scope.get_data(channel=TARGET_CHANNEL)

print("Data acquired!")
df.head()"""),
    
    new_markdown_cell("## 4. Plot the Result\nLets plot the DataFrame to visually verify the acquired pulse."),
    
    new_code_cell("""plt.figure(figsize=(10, 6))
plt.plot(df["Time"], df["Voltage"], label=f"Channel {TARGET_CHANNEL}")

# Draw a line showing where our trigger level was
plt.axhline(TRIGGER_LEVEL, color="red", linestyle="--", label="Trigger Level")

plt.title("Acquired Pulse")
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.legend()
plt.grid(True)
plt.show()""")
]

nb.cells.extend(cells)

with open('lecroy_trigger_test.ipynb', 'w') as f:
    nbformat.write(nb, f)
print('Notebook created successfully.')
