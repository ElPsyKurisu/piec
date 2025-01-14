import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from piec.measurement_waveforms.discrete_waveform import HysteresisLoop, ThreePulsePund

class MeasurementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Waveform Measurement GUI")
        self.root.geometry("800x600")

        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10), padding=5)
        self.style.configure("TCombobox", font=("Arial", 10))

        # Main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Static inputs section
        self.static_frame = ttk.LabelFrame(self.main_frame, text="Static Inputs", padding=10)
        self.static_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(self.static_frame, text="AWG Address:").grid(row=0, column=0, sticky="w")
        self.awg_address_entry = ttk.Entry(self.static_frame, width=30)
        self.awg_address_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.static_frame, text="Oscilloscope Address:").grid(row=1, column=0, sticky="w")
        self.osc_address_entry = ttk.Entry(self.static_frame, width=30)
        self.osc_address_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.static_frame, text="Save Directory:").grid(row=2, column=0, sticky="w")
        self.save_dir_entry = ttk.Entry(self.static_frame, width=30)
        self.save_dir_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(self.static_frame, text="Browse", command=self.browse_directory).grid(row=2, column=2, padx=5)

        # Measurement type selection
        ttk.Label(self.static_frame, text="Measurement Type:").grid(row=3, column=0, sticky="w")
        self.measurement_type = ttk.Combobox(self.static_frame, values=["HysteresisLoop", "ThreePulsePund"], state="readonly")
        self.measurement_type.grid(row=3, column=1, padx=5, pady=5)
        self.measurement_type.bind("<<ComboboxSelected>>", self.update_dynamic_inputs)

        # Dynamic inputs section
        self.dynamic_frame = ttk.LabelFrame(self.main_frame, text="Dynamic Inputs", padding=10)
        self.dynamic_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Placeholder for dynamic inputs
        self.dynamic_inputs = {}

        # Plotting section
        self.plot_frame = ttk.LabelFrame(self.main_frame, text="Acquired Data", padding=10)
        self.plot_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Run button
        ttk.Button(self.main_frame, text="Run Measurement", command=self.run_measurement).grid(row=2, column=0, columnspan=2, pady=10)

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

        measurement_type = self.measurement_type.get()
        if measurement_type == "HysteresisLoop":
            self.setup_hysteresis_inputs()
        elif measurement_type == "ThreePulsePund":
            self.setup_pund_inputs()

    def setup_hysteresis_inputs(self):
        ttk.Label(self.dynamic_frame, text="Frequency (Hz):").grid(row=0, column=0, sticky="w")
        self.dynamic_inputs["frequency"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["frequency"].grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="Amplitude (V):").grid(row=1, column=0, sticky="w")
        self.dynamic_inputs["amplitude"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["amplitude"].grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="Offset (V):").grid(row=2, column=0, sticky="w")
        self.dynamic_inputs["offset"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["offset"].grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="Number of Cycles:").grid(row=3, column=0, sticky="w")
        self.dynamic_inputs["n_cycles"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["n_cycles"].grid(row=3, column=1, padx=5, pady=5)

    def setup_pund_inputs(self):
        ttk.Label(self.dynamic_frame, text="Reset Amplitude (V):").grid(row=0, column=0, sticky="w")
        self.dynamic_inputs["reset_amp"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["reset_amp"].grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="Reset Width (s):").grid(row=1, column=0, sticky="w")
        self.dynamic_inputs["reset_width"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["reset_width"].grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="Reset Delay (s):").grid(row=2, column=0, sticky="w")
        self.dynamic_inputs["reset_delay"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["reset_delay"].grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="P/U Amplitude (V):").grid(row=3, column=0, sticky="w")
        self.dynamic_inputs["p_u_amp"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["p_u_amp"].grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="P/U Width (s):").grid(row=4, column=0, sticky="w")
        self.dynamic_inputs["p_u_width"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["p_u_width"].grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(self.dynamic_frame, text="P/U Delay (s):").grid(row=5, column=0, sticky="w")
        self.dynamic_inputs["p_u_delay"] = ttk.Entry(self.dynamic_frame, width=20)
        self.dynamic_inputs["p_u_delay"].grid(row=5, column=1, padx=5, pady=5)

    def run_measurement(self):
        awg_address = self.awg_address_entry.get()
        osc_address = self.osc_address_entry.get()
        save_dir = self.save_dir_entry.get()
        measurement_type = self.measurement_type.get()

        if measurement_type == "HysteresisLoop":
            frequency = float(self.dynamic_inputs["frequency"].get())
            amplitude = float(self.dynamic_inputs["amplitude"].get())
            offset = float(self.dynamic_inputs["offset"].get())
            n_cycles = int(self.dynamic_inputs["n_cycles"].get())

            experiment = HysteresisLoop(awg=awg_address, osc=osc_address, frequency=frequency, amplitude=amplitude, offset=offset, n_cycles=n_cycles, save_dir=save_dir)
        elif measurement_type == "ThreePulsePund":
            reset_amp = float(self.dynamic_inputs["reset_amp"].get())
            reset_width = float(self.dynamic_inputs["reset_width"].get())
            reset_delay = float(self.dynamic_inputs["reset_delay"].get())
            p_u_amp = float(self.dynamic_inputs["p_u_amp"].get())
            p_u_width = float(self.dynamic_inputs["p_u_width"].get())
            p_u_delay = float(self.dynamic_inputs["p_u_delay"].get())

            experiment = ThreePulsePund(awg=awg_address, osc=osc_address, reset_amp=reset_amp, reset_width=reset_width, reset_delay=reset_delay, p_u_amp=p_u_amp, p_u_width=p_u_width, p_u_delay=p_u_delay, save_dir=save_dir)

        experiment.run_experiment()
        self.plot_data(experiment.data)

    def plot_data(self, data):
        self.ax.clear()
        self.ax.plot(data["time (s)"], data["voltage (V)"], label="Voltage")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.legend()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = MeasurementApp(root)
    root.mainloop()