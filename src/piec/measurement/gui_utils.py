import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

class MeasurementApp:
    def __init__(self, root, title="Measurement GUI", geometry="1200x700"):
        self.root = root
        self.root.geometry(geometry)
        
        self.setup_styles()
        self.root.configure(background="#1E1E1E")
        
        # Main frame - Shared by all GUIs
        self.main_frame = ttk.Frame(root, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_layout()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_layout(self):
        # 2-Column Layout
        self.main_frame.columnconfigure(0, weight=0) # Inputs (fixed width-ish, let widgets decide)
        self.main_frame.columnconfigure(1, weight=1) # Plot (expand)
        self.main_frame.rowconfigure(0, weight=1)

        # Left Panel (Inputs) - Using SideBar style
        self.left_panel = ttk.Frame(self.main_frame, style="SideBar.TFrame")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0) # Removing external padding for full sidebar look
        
        # Right Panel (Plot + Run) - Default TFrame (dark background)
        self.right_panel = ttk.Frame(self.main_frame, style="TFrame")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(0, weight=0) # Plot fixed height (controlled by figsize)
        self.right_panel.rowconfigure(1, weight=0) # Button fixed

        # --- Left Panel Contents ---
        
        # 1. Static Inputs Frame - Using Card styles
        self.static_frame = ttk.LabelFrame(self.left_panel, text="STATIC INPUTS", padding=10, style="Card.TLabelframe")
        self.static_frame.pack(fill=tk.X, expand=False, pady=10, padx=10)
        
        # Standard Input: Save Directory
        ttk.Label(self.static_frame, text="Save Directory:").grid(row=0, column=0, sticky="w")
        self.save_dir_entry = ttk.Entry(self.static_frame, width=40)
        self.save_dir_entry.grid(row=0, column=1, padx=5, pady=5)
        # Inheriting classes should set default if needed, or we can check kwarg
        ttk.Button(self.static_frame, text="Browse", command=lambda: self.browse_directory(self.save_dir_entry), style="TButton").grid(row=0, column=2, padx=5)

        # 2. Dynamic Inputs Frame (Placeholder for subclass) - Using Card style
        self.dynamic_frame = ttk.LabelFrame(self.left_panel, text="DYNAMIC INPUTS", padding=10, style="Card.TLabelframe")
        self.dynamic_frame.pack(fill=tk.X, expand=False, pady=(0, 10), padx=10)

        # 3. Plot Configuration Frame - Using Card style
        self.plot_config_frame = ttk.LabelFrame(self.left_panel, text="PLOT CONFIGURATION", padding=10, style="Card.TLabelframe")
        self.plot_config_frame.pack(fill=tk.X, expand=False, padx=10)

        # --- Right Panel Contents ---

        # 1. Plot
        self.setup_plot(self.right_panel)
        
        # 2. Run Button
        # Subclasses must implement run_measurement
        ttk.Button(self.right_panel, text="RUN MEASUREMENT", command=self.run_measurement, style="TButton").grid(row=1, column=0, pady=10)

    def run_measurement(self):
        print("WARNING: run_measurement not implemented in subclass")

    def setup_plot(self, parent):
        # Locate and use natty_style.mplstyle
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            style_path = os.path.join(current_dir, '..', '..', 'natty_style.mplstyle')
            if os.path.exists(style_path):
                plt.style.use(style_path)
            else:
                 style_path = os.path.join(current_dir, '..', 'natty_style.mplstyle')
                 if os.path.exists(style_path):
                     plt.style.use(style_path)
                 else:
                     print(f"WARNING: natty_style.mplstyle not found at {style_path}")
        except Exception as e:
            print(f"WARNING: Failed to load natty_style: {e}")

        # Plotting section - Using Card style
        self.plot_frame = ttk.LabelFrame(parent, text="ACQUIRED DATA", padding=5, style="Card.TLabelframe")
        self.plot_frame.grid(row=0, column=0, sticky="nsew") 
        
        self.fig, self.ax = plt.subplots(figsize=(6, 3.5)) 
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Color Palette - Layered
        bg_root = "#181818"       # Darkest (Background)
        bg_sidebar = "#202020"    # Left Panel
        bg_card = "#2B2B2B"       # Content Cards
        bg_field = "#383838"      # Input Fields
        fg_text = "#E0E0E0"       # Off-white text
        border_grey = "#3E3E42"   # Subtle border
        
        # General defaults
        self.style.configure(".", 
                             background=bg_root, 
                             foreground=fg_text, 
                             font=("Helvetica", 15))

        # TFrame (Default for transparent-ish look on root)
        self.style.configure("TFrame", 
                             background=bg_root,
                             borderwidth=0) # No border for layout frames
                             
        # SideBar Style
        self.style.configure("SideBar.TFrame",
                             background=bg_sidebar,
                             relief="flat")

        # Card Style for LabelFrames
        self.style.configure("Card.TLabelframe", 
                             background=bg_card,
                             borderwidth=0, 
                             relief="flat")
        
        self.style.configure("Card.TLabelframe.Label",
                             background=bg_card,
                             foreground=fg_text,
                             font=("Helvetica", 20, "bold")) # Adjusted font size

        # TLabel - Need to handle different backgrounds...
        # Since we can't easily have transparent labels in ttk clam with different bg colors,
        # We might need specific styles or default to the most common one (Card).
        # Or we rely on the widget picking up the parent style if we don't set background explicitely?
        # 'clam' theme usually paints background.
        self.style.configure("TLabel", 
                             background=bg_card, 
                             foreground=fg_text,
                             font=("Helvetica", 12))
        
        # TButton
        self.style.configure("TButton", 
                             padding=6, 
                             relief="flat", 
                             background=bg_field, 
                             foreground=fg_text,
                             borderwidth=0,
                             font=("Helvetica", 15, "bold"))
        
        self.style.map("TButton", 
                       background=[('active', '#4A4A4A'), ('pressed', '#555555')],
                       foreground=[('active', '#FFFFFF')])

        # TEntry
        self.style.configure("TEntry", 
                             fieldbackground=bg_field,
                             foreground=fg_text,
                             insertcolor=fg_text,
                             borderwidth=0,
                             relief="flat")
                             
        # TCombobox
        self.style.configure("TCombobox", 
                             fieldbackground=bg_field,
                             background=bg_field,
                             foreground=fg_text,
                             arrowcolor=fg_text,
                             borderwidth=0,
                             relief="flat")
        
        self.style.map("TCombobox", 
                       fieldbackground=[('readonly', bg_field)],
                       selectbackground=[('readonly', bg_field)],
                       selectforeground=[('readonly', fg_text)])

        # TCheckbutton
        self.style.configure("TCheckbutton", 
                             background=bg_card, # Assuming inside cards
                             foreground=fg_text,
                             font=("Helvetica", 10),
                             indicatorcolor=bg_field,
                             indicatorrelief="solid",
                             indicatorborderwidth=1)

        self.style.map("TCheckbutton",
                       indicatorcolor=[('selected', fg_text), ('active', '#4A4A4A')],
                       background=[('active', bg_card)])

    def on_closing(self):
        self.root.destroy()
        sys.exit()

    def browse_directory(self, entry_widget):
        directory = filedialog.askdirectory()
        if directory:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory)
            
    def get_visa_resources(self):
        try:
            from pyvisa import ResourceManager
            rm = ResourceManager()
            return list(rm.list_resources())
        except Exception as e:
            print(f"WARNING: pyvisa setup failed or no resources found: {e}")
            return []
