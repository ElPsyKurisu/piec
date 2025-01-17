import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import matplotlib
matplotlib.use('TkAgg')  # Set the backend to TkAgg for interractivity
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from piec.measurement_waveforms.discrete_waveform import HysteresisLoop, ThreePulsePund
from piec.analysis.utilities import standard_csv_to_metadata_and_data
from piec.drivers.keysight81150a import Keysight81150a
from piec.drivers.keysightdsox3024a import Dsox3024a

DEFAULTS = {"awg_address":"VIRTUAL",
            "osc_address":"VIRTUAL",
            "save_dir":r"\\files22.brown.edu\Research\ENG_Caretta_Shared\Group\probe_station\test",
            "vdiv":0.01,
            "time_offset":140,
            "frequency": 1.0e6,
            "amplitude": 1.0,
            "offset": 0.0,
            "n_cycles": 2,
            "reset_amp": 1.0,
            "reset_width": 1.0e-7,
            "reset_delay": 1.0e-7,
            "p_u_amp": 1.0,
            "p_u_width": 1.0e-7,
            "p_u_delay": 1.0e-7,
            }

try:
    from pyvisa import ResourceManager
    rm = ResourceManager()
    visa_resources = rm.list_resources()
except:
    print('WARNING: pyvisa setup failed, check driver dependencies')

class MeasurementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Waveform Measurement GUI")
        self.root.geometry("1200x700")

        # Style configuration
        self.style = ttk.Style()

        self.style.configure("TFrame", font=("Arial", 11), borderwidth=1, relief="solid", bordercolor="#7E7E7E")
        self.style.configure("TLabel", font=("Arial", 11))
        self.style.configure("TLabel", font=("Arial", 11))
        self.style.configure("TCombobox", font=("Arial", 11))
        self.style.configure("TButton", font=("Arial", 11),borderwidth=2, relief="solid", bordercolor="#7E7E7E", padding=5,)

        self.style.map("TButton",
               background=[("active", "#0078D7")],)

        # Main frame
        self.main_frame = ttk.Frame(root, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Static inputs section
        self.static_frame = ttk.LabelFrame(self.main_frame, text="Static Inputs", padding=10, style="TFrame")
        self.static_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(self.static_frame, text="Save Directory:").grid(row=0, column=0, sticky="w")
        self.save_dir_entry = ttk.Entry(self.static_frame, width=40)
        self.save_dir_entry.grid(row=0, column=1, padx=5, pady=5)
        self.save_dir_entry.insert(0, DEFAULTS["save_dir"])
        ttk.Button(self.static_frame, text="Browse", command=self.browse_directory, style="TButton").grid(row=0, column=2, padx=5)

        ttk.Label(self.static_frame, text="AWG Address:").grid(row=1, column=0, sticky="w")
        self.awg_address_entry = ttk.Combobox(self.static_frame, values=["VIRTUAL"]+list(visa_resources), state="readonly")
        self.awg_address_entry.grid(row=1, column=1, padx=5, pady=5)
        self.awg_address_entry.set(DEFAULTS["awg_address"])
        ttk.Button(self.static_frame, text="Refresh", command=self.refresh_instruments, style="TButton").grid(row=1, column=2, rowspan=2, padx=5)

        ttk.Label(self.static_frame, text="Oscilloscope Address:").grid(row=2, column=0, sticky="w")
        self.osc_address_entry = ttk.Combobox(self.static_frame, values=["VIRTUAL"]+list(visa_resources), state="readonly")
        self.osc_address_entry.grid(row=2, column=1, padx=5, pady=5)
        self.osc_address_entry.set(DEFAULTS["osc_address"])

        ttk.Label(self.static_frame, text="Oscilloscope V/div:").grid(row=3, column=0, sticky="w")
        self.vdiv_entry = ttk.Entry(self.static_frame, width=24)
        self.vdiv_entry.grid(row=3, column=1, padx=5, pady=5)
        self.vdiv_entry.insert(0, DEFAULTS["vdiv"])

        ttk.Label(self.static_frame, text="Time Offset (ns):").grid(row=4, column=0, sticky="w")
        self.timeshift_entry = ttk.Entry(self.static_frame, width=24)
        self.timeshift_entry.grid(row=4, column=1, padx=5, pady=5)
        self.timeshift_entry.insert(0, DEFAULTS["time_offset"])

        # Add a checkbox for auto_timeshift
        self.auto_timeshift_entry = tk.BooleanVar(value=True)  # Default state is checked
        self.auto_timeshift_checkbox = ttk.Checkbutton(
            self.static_frame,
            text="Automatic?",
            variable=self.auto_timeshift_entry,
            onvalue=True,
            offvalue=False
        )
        self.auto_timeshift_checkbox.grid(row=4, column=2, columnspan=1, pady=5, sticky="w")

        # Measurement type selection
        ttk.Label(self.static_frame, text="Measurement Type:").grid(row=5, column=0, sticky="w")
        self.measurement_type = ttk.Combobox(self.static_frame, values=["HysteresisLoop", "ThreePulsePund"], state="readonly")
        self.measurement_type.grid(row=5, column=1, padx=5, pady=5)
        self.measurement_type.bind("<<ComboboxSelected>>", self.update_dynamic_inputs)

        # Dynamic inputs section
        self.dynamic_frame = ttk.LabelFrame(self.main_frame, text=f"{str(self.measurement_type.get())} Inputs", padding=10, style="TFrame")
        self.dynamic_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Placeholder for dynamic inputs
        self.dynamic_inputs = {}

        # Plotting section
        self.plot_frame = ttk.LabelFrame(self.main_frame, text="Acquired Data", padding=10, style="TFrame")
        self.plot_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.fig, self.ax = plt.subplots(figsize=(6, 4), tight_layout=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Plot configuration section
        self.plot_config_frame = ttk.LabelFrame(self.main_frame, text="Plot Configuration", padding=10, style="TFrame")
        self.plot_config_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Label(self.plot_config_frame, text="X-axis:").grid(row=0, column=0, sticky="w")
        self.x_axis = ttk.Combobox(self.plot_config_frame, values=["time (s)", "applied voltage (V)", "current (A)", "polarization (uC/cm^2)"], state="readonly")
        self.x_axis.grid(row=0, column=1, padx=5, pady=5)
        self.x_axis.set("applied voltage (V)")
        self.x_axis.bind("<<ComboboxSelected>>", self.plot_data)

        ttk.Label(self.plot_config_frame, text="Y-axis:").grid(row=1, column=0, sticky="w")
        self.y_axis = ttk.Combobox(self.plot_config_frame, values=["time (s)", "applied voltage (V)", "current (A)", "polarization (uC/cm^2)"], state="readonly")
        self.y_axis.grid(row=1, column=1, padx=5, pady=5)
        self.y_axis.set("current (A)")
        self.y_axis.bind("<<ComboboxSelected>>", self.plot_data)

        # Add a checkbox for plot saving
        self.saveplots_entry = tk.BooleanVar(value=False)  # Default state is unchecked
        self.enable_feature_checkbox = ttk.Checkbutton(
            self.plot_config_frame,
            text="Save Plots?",
            variable=self.saveplots_entry,
            onvalue=True,
            offvalue=False
        )
        self.enable_feature_checkbox.grid(row=2, column=0, columnspan=2, pady=5, sticky="w")

        # Run button
        ttk.Button(self.main_frame, text="Run Measurement", command=self.run_measurement, style="TButton").grid(row=3, column=0, columnspan=3, pady=10)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_dir_entry.delete(0, tk.END)
            self.save_dir_entry.insert(0, directory)

    def update_dynamic_inputs(self, event):
        # Clear previous dynamic inputs
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        self.dynamic_inputs = {}
        self.dynamic_frame.config(text=f"{str(self.measurement_type.get())} Inputs")
        measurement_type = self.measurement_type.get()
        if measurement_type == "HysteresisLoop":
            self.setup_hysteresis_inputs()
        elif measurement_type == "ThreePulsePund":
            self.setup_pund_inputs()

    def update_dynamic_defaults(self):
        # Update defaults to currently selected values
        for key in self.dynamic_inputs:
            DEFAULTS[key] = self.dynamic_inputs[key].get()

    def refresh_instruments(self):
        try:
            print('Refreshing VISA instruments...')
            rm = ResourceManager()
            visa_resources = rm.list_resources()
            
            self.awg_address_entry["values"] = ["VIRTUAL"] + list(visa_resources)
            self.osc_address_entry["values"] = ["VIRTUAL"] + list(visa_resources)
            
            self.awg_address_entry.set("")
            self.awg_address_entry.set("VIRTUAL")
            self.osc_address_entry.set("")
            self.osc_address_entry.set("VIRTUAL")
        except Exception as e:
            print(f"Error refreshing VISA resources: {e}")

    def setup_hysteresis_inputs(self):
        ttk.Label(self.dynamic_frame, text="Frequency (Hz):").grid(row=0, column=0, sticky="w")
        self.dynamic_inputs["frequency"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["frequency"].grid(row=0, column=1, padx=5, pady=5)
        self.dynamic_inputs["frequency"].insert(0, DEFAULTS["frequency"])

        ttk.Label(self.dynamic_frame, text="Amplitude (V):").grid(row=1, column=0, sticky="w")
        self.dynamic_inputs["amplitude"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["amplitude"].grid(row=1, column=1, padx=5, pady=5)
        self.dynamic_inputs["amplitude"].insert(0, DEFAULTS["amplitude"])

        ttk.Label(self.dynamic_frame, text="Offset (V):").grid(row=2, column=0, sticky="w")
        self.dynamic_inputs["offset"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["offset"].grid(row=2, column=1, padx=5, pady=5)
        self.dynamic_inputs["offset"].insert(0, DEFAULTS["offset"])

        ttk.Label(self.dynamic_frame, text="Number of Cycles:").grid(row=3, column=0, sticky="w")
        self.dynamic_inputs["n_cycles"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["n_cycles"].grid(row=3, column=1, padx=5, pady=5)
        self.dynamic_inputs["n_cycles"].insert(0, DEFAULTS["n_cycles"])

    def setup_pund_inputs(self):
        ttk.Label(self.dynamic_frame, text="Reset Amplitude (V):").grid(row=0, column=0, sticky="w")
        self.dynamic_inputs["reset_amp"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["reset_amp"].grid(row=0, column=1, padx=5, pady=5)
        self.dynamic_inputs["reset_amp"].insert(0, DEFAULTS["reset_amp"])

        ttk.Label(self.dynamic_frame, text="Reset Width (s):").grid(row=1, column=0, sticky="w")
        self.dynamic_inputs["reset_width"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["reset_width"].grid(row=1, column=1, padx=5, pady=5)
        self.dynamic_inputs["reset_width"].insert(0, DEFAULTS["reset_width"])

        ttk.Label(self.dynamic_frame, text="Reset Delay (s):").grid(row=2, column=0, sticky="w")
        self.dynamic_inputs["reset_delay"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["reset_delay"].grid(row=2, column=1, padx=5, pady=5)
        self.dynamic_inputs["reset_delay"].insert(0, DEFAULTS["reset_delay"])

        ttk.Label(self.dynamic_frame, text="P/U Amplitude (V):").grid(row=3, column=0, sticky="w")
        self.dynamic_inputs["p_u_amp"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["p_u_amp"].grid(row=3, column=1, padx=5, pady=5)
        self.dynamic_inputs["p_u_amp"].insert(0, DEFAULTS["p_u_amp"])

        ttk.Label(self.dynamic_frame, text="P/U Width (s):").grid(row=4, column=0, sticky="w")
        self.dynamic_inputs["p_u_width"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["p_u_width"].grid(row=4, column=1, padx=5, pady=5)
        self.dynamic_inputs["p_u_width"].insert(0, DEFAULTS["p_u_width"])

        ttk.Label(self.dynamic_frame, text="P/U Delay (s):").grid(row=5, column=0, sticky="w")
        self.dynamic_inputs["p_u_delay"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["p_u_delay"].grid(row=5, column=1, padx=5, pady=5)
        self.dynamic_inputs["p_u_delay"].insert(0, DEFAULTS["p_u_delay"])

        ttk.Label(self.dynamic_frame, text="Offset (V):").grid(row=6, column=0, sticky="w")
        self.dynamic_inputs["offset"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["offset"].grid(row=6, column=1, padx=5, pady=5)
        self.dynamic_inputs["offset"].insert(0, DEFAULTS["offset"])

    def run_measurement(self):
        awg_address = self.awg_address_entry.get()
        osc_address = self.osc_address_entry.get()
        save_dir = self.save_dir_entry.get()
        measurement_type = self.measurement_type.get()
        awg = Keysight81150a(awg_address)
        osc = Dsox3024a(osc_address)
        v_div = float(self.vdiv_entry.get())
        time_offset = float(self.timeshift_entry.get())*1.0e-9
        save_plots = bool(self.saveplots_entry.get())
        show_plots = save_plots
        auto_timeshift = bool(self.auto_timeshift_entry.get())

        if measurement_type == "HysteresisLoop":
            frequency = float(self.dynamic_inputs["frequency"].get())
            amplitude = float(self.dynamic_inputs["amplitude"].get())
            offset = float(self.dynamic_inputs["offset"].get())
            n_cycles = int(self.dynamic_inputs["n_cycles"].get())

            self.experiment = HysteresisLoop(awg=awg, osc=osc,
                                             frequency=frequency, amplitude=amplitude,
                                             offset=offset, n_cycles=n_cycles,
                                             save_dir=save_dir, v_div=v_div, time_offset=time_offset,
                                             save_plots=save_plots, show_plots=show_plots, auto_timeshift=auto_timeshift)
            
        elif measurement_type == "ThreePulsePund":
            reset_amp = float(self.dynamic_inputs["reset_amp"].get())
            reset_width = float(self.dynamic_inputs["reset_width"].get())
            reset_delay = float(self.dynamic_inputs["reset_delay"].get())
            p_u_amp = float(self.dynamic_inputs["p_u_amp"].get())
            p_u_width = float(self.dynamic_inputs["p_u_width"].get())
            p_u_delay = float(self.dynamic_inputs["p_u_delay"].get())
            offset = float(self.dynamic_inputs["offset"].get())

            self.experiment = ThreePulsePund(awg=awg, osc=osc,
                                             reset_amp=reset_amp, reset_width=reset_width, reset_delay=reset_delay,
                                             p_u_amp=p_u_amp, p_u_width=p_u_width, p_u_delay=p_u_delay,
                                             save_dir=save_dir, v_div=v_div, time_offset=time_offset, offset=offset,
                                             save_plots=save_plots, show_plots=show_plots, auto_timeshift=auto_timeshift)
        print(self.experiment.save_plots)
        self.experiment.run_experiment()
        self.update_dynamic_defaults()
        self.plot_data(self.experiment.filename)

    def plot_data(self, event=None):
        self.ax.clear()
        metadata, data = standard_csv_to_metadata_and_data(self.experiment.filename)
        x_data = data[self.x_axis.get()]
        y_data = data[self.y_axis.get()]
        self.timeshift_entry.delete(0, tk.END)
        self.timeshift_entry.insert(0, metadata["time_offset"].values[0]*1e9) # update time offset input in case auto is used

        self.ax.plot(x_data, y_data, marker='.',color='k', label=f"{self.y_axis.get()} vs {self.x_axis.get()}")
        self.ax.set_xlabel(self.x_axis.get())
        self.ax.set_ylabel(self.y_axis.get())
        # self.ax.legend()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = MeasurementApp(root)
    root.mainloop()