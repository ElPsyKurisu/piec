import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

plot_layout_params = {
            "font.size": 15,
            "axes.labelsize": 15,
            "axes.titlesize": 15,
            "xtick.labelsize": 15,
            "ytick.labelsize": 15,
            "axes.linewidth": 1.5,
            "lines.linewidth": 2.0,
            "xtick.major.width": 1.5,
            "ytick.major.width": 1.5,
            "xtick.minor.width": 1.5,
            "ytick.minor.width": 1.5,
            "xtick.major.size": 5,
            "ytick.major.size": 5,
            "xtick.minor.size": 3,
            "ytick.minor.size": 3,
            "figure.autolayout": True, # Decrease white margins
            "figure.figsize": (6, 4) # Slightly taller default
        }

class ConsoleRedirector:
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, string):
        try:
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, string, (self.tag,))
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
            self.text_widget.update_idletasks() # Force redraw immediately
        except Exception:
            pass # Handle case where widget is destroyed

    def flush(self):
        pass

class MeasurementApp:
    def __init__(self, root, title="Measurement GUI", geometry="1200x700", icon_path=None):
        self.root = root
        self.root.title(title)
        self.root.geometry(geometry)
        
        # icon import
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_icon = os.path.join(current_dir, 'GUI_icon.png')
            if os.path.exists(default_icon):
                icon_path = default_icon
        except Exception:
            pass

        if icon_path:
             if os.path.exists(icon_path):
                 try:
                     icon = tk.PhotoImage(file=icon_path)
                     self.root.iconphoto(False, icon)
                 except Exception:
                     try:
                         self.root.iconbitmap(icon_path)
                     except Exception as e:
                         print(f"WARNING: Failed to load icon: {e}")
             else:
                 print(f"WARNING: Icon file not found at {icon_path}")
        
        self.setup_styles()
        self.root.configure(background="#1E1E1E")
        
        # Keyboard Shortcuts
        self.keyboard_shortcuts = {
            "<Control-Return>": lambda event: self.run_measurement()
        }
        self.setup_shortcuts()
        
        # Main frame - Shared by all GUIs
        self.main_frame = ttk.Frame(root, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_layout()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Console Redirection
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        self.console = ConsoleRedirector(self.log_text, "stdout")
        sys.stdout = self.console
        sys.stderr = self.console # Optional: redirect stderr too, maybe with different tag if extended


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
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(0, weight=3) # Plot expands
        self.right_panel.rowconfigure(1, weight=0) # Button fixed
        self.right_panel.rowconfigure(2, weight=1) # Log console expands less than plot

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
        self.run_button = ttk.Button(self.right_panel, text="RUN MEASUREMENT", command=self.run_measurement, style="TButton")
        self.run_button.grid(row=1, column=0, pady=10)

        # 3. Log Console
        self.setup_log_console(self.right_panel)



    def setup_shortcuts(self):
        """Binds keys in self.keyboard_shortcuts to the root window"""
        for key, callback in self.keyboard_shortcuts.items():
            self.root.bind(key, callback)

    def run_measurement(self):
        print("WARNING: run_measurement not implemented in subclass")

    def setup_log_console(self, parent):
        self.log_frame = ttk.Frame(parent, style="Card.TFrame")
        self.log_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 0))
        
        # Text widget for logs
        self.log_text = tk.Text(self.log_frame, height=8, width=50, state='disabled', wrap='word',
                                background="#2B2B2B", foreground="#E0E0E0", 
                                insertbackground="#E0E0E0", borderwidth=0, relief="flat",
                                font=("Consolas", 10))
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

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

        # Override style for GUI visibility (Scale up for screen)
        plt.rcParams.update(plot_layout_params)

        # Plotting section - Using Card style
        self.plot_frame = ttk.LabelFrame(parent, text="ACQUIRED DATA", padding=5, style="Card.TLabelframe")
        self.plot_frame.grid(row=0, column=0, sticky="nsew") 
        
        self.fig, self.ax = plt.subplots() 
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
        
        self.style.configure("Card.TFrame", 
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
                             relief="flat",
                             lightcolor=bg_field,
                             darkcolor=bg_field,
                             bordercolor=bg_field)
                             
        # TCombobox
        self.style.configure("TCombobox", 
                             fieldbackground=bg_field,
                             background=bg_field,
                             foreground=fg_text,
                             arrowcolor=fg_text,
                             borderwidth=0,
                             relief="flat",
                             lightcolor=bg_field,
                             darkcolor=bg_field,
                             bordercolor=bg_field)
        
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

        # TScrollbar
        self.style.configure("Vertical.TScrollbar",
                             gripcount=0,
                             background=bg_field,
                             darkcolor=bg_field,
                             lightcolor=bg_field,
                             troughcolor=bg_card,
                             bordercolor=bg_card,
                             arrowcolor=fg_text,
                             relief="flat")
                             
        self.style.map("Vertical.TScrollbar",
                       background=[('active', '#4A4A4A'), ('pressed', '#555555')])

    def on_closing(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
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
