import tkinter as tk
from tkinter import filedialog, scrolledtext
import google.generativeai as genai
import os
import pathlib
#Note, need to buy an API key for this to work so backburner
# --- Configuration ---
# IMPORTANT: Replace "YOUR_API_KEY" with your actual Gemini API key.
# You can get a key from Google AI Studio: https://aistudio.google.com/app/apikey
API_KEY = "meowsecret"

# The path to your GitHub repository that will always be included in the prompt.
GITHUB_REPO_URL = "https://github.com/your-username/your-repository"

# The name of the file containing the built-in system prompt template.
SYSTEM_PROMPT_FILE = "system_prompt_template.txt"

class GeminiApp:
    """
    A Tkinter-based GUI for interacting with the Gemini API,
    with support for file uploads and a persistent, dynamic system prompt.
    """
    def __init__(self, root):
        """Initializes the application window and its widgets."""
        self.root = root
        self.root.title("Gemini Pro 2.5 GUI")
        self.root.geometry("800x750") # Increased height slightly for new fields

        self.uploaded_file_path = None
        self.uploaded_filename = None

        # --- Configure API ---
        try:
            genai.configure(api_key=API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
        except Exception as e:
            self.show_error(f"Failed to configure Gemini API. Please check your API key.\nError: {e}")
            return

        # --- Create and Grid Widgets ---
        self.main_frame = tk.Frame(root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid layout
        self.main_frame.grid_rowconfigure(1, weight=1) # prompt area
        self.main_frame.grid_rowconfigure(4, weight=2) # response area
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Dynamic Inputs Section ---
        self.inputs_frame = tk.Frame(self.main_frame)
        self.inputs_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.inputs_frame.grid_columnconfigure(1, weight=1)

        tk.Label(self.inputs_frame, text="Class Name:", font=("Helvetica", 11)).grid(row=0, column=0, sticky="w", padx=(0,5))
        self.class_name_input = tk.Entry(self.inputs_frame, font=("Helvetica", 11))
        self.class_name_input.grid(row=0, column=1, sticky="ew")

        tk.Label(self.inputs_frame, text="Parent Classes:", font=("Helvetica", 11)).grid(row=1, column=0, sticky="w", padx=(0,5), pady=(5,0))
        self.parent_classes_input = tk.Entry(self.inputs_frame, font=("Helvetica", 11))
        self.parent_classes_input.grid(row=1, column=1, sticky="ew", pady=(5,0))


        # --- User Prompt Section ---
        tk.Label(self.main_frame, text="Your Prompt:", font=("Helvetica", 12, "bold")).grid(row=1, column=0, sticky="sw")
        self.prompt_input = scrolledtext.ScrolledText(self.main_frame, height=5, wrap=tk.WORD, font=("Helvetica", 11))
        self.prompt_input.grid(row=2, column=0, sticky="nsew", pady=(5,0))

        # --- File Upload Section ---
        self.file_controls_frame = tk.Frame(self.main_frame)
        self.file_controls_frame.grid(row=3, column=0, sticky="ew", pady=10)

        self.upload_button = tk.Button(self.file_controls_frame, text="Upload File", command=self.select_file)
        self.upload_button.pack(side=tk.LEFT)

        self.selected_file_label = tk.Label(self.file_controls_frame, text="No file selected.", fg="gray", padx=10)
        self.selected_file_label.pack(side=tk.LEFT)

        # --- Submit Button ---
        self.submit_button = tk.Button(self.main_frame, text="Submit to Gemini", command=self.call_gemini_api, font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white")
        self.submit_button.grid(row=4, column=0, sticky="ew", pady=10)

        # --- Response Section ---
        tk.Label(self.main_frame, text="Gemini's Response:", font=("Helvetica", 12, "bold")).grid(row=5, column=0, sticky="w", pady=(5, 5))
        self.response_output = scrolledtext.ScrolledText(self.main_frame, state=tk.DISABLED, wrap=tk.WORD, font=("Helvetica", 11), bg="#f0f0f0")
        self.response_output.grid(row=6, column=0, sticky="nsew")


    def select_file(self):
        """Opens a file dialog, updates the GUI, and stores the filename."""
        filepath = filedialog.askopenfilename()
        if filepath:
            self.uploaded_file_path = filepath
            self.uploaded_filename = os.path.basename(filepath)
            self.selected_file_label.config(text=f"Selected: {self.uploaded_filename}", fg="green")
        else:
            self.uploaded_file_path = None
            self.uploaded_filename = None
            self.selected_file_label.config(text="No file selected.", fg="gray")

    def get_system_prompt_template(self):
        """Reads the content of the system prompt template file."""
        try:
            with open(SYSTEM_PROMPT_FILE, "r") as f:
                return f.read()
        except FileNotFoundError:
            self.show_error(f"SYSTEM PROMPT ERROR: The template file '{SYSTEM_PROMPT_FILE}' was not found.")
            return None
        except Exception as e:
            self.show_error(f"SYSTEM PROMPT ERROR: Could not read template file. Reason: {e}")
            return None


    def show_error(self, message):
        """Displays an error message in the response box."""
        self.response_output.config(state=tk.NORMAL)
        self.response_output.delete("1.0", tk.END)
        self.response_output.insert(tk.END, f"ERROR:\n\n{message}")
        self.response_output.config(state=tk.DISABLED)

    def call_gemini_api(self):
        """
        Constructs the dynamic prompt, calls the Gemini API,
        and displays the response.
        """
        # 1. Get user input
        user_prompt = self.prompt_input.get("1.0", tk.END).strip()
        if not user_prompt:
            self.show_error("Please enter a prompt.")
            return

        # 2. Get dynamic values from GUI
        class_name = self.class_name_input.get().strip() or "Not specified"
        parent_classes = self.parent_classes_input.get().strip() or "Not specified"
        attached_files = self.uploaded_filename or "None"

        # 3. Get and populate the system prompt template
        prompt_template = self.get_system_prompt_template()
        if prompt_template is None:
            return # Stop if template couldn't be loaded

        populated_prompt = prompt_template.replace("________", class_name, 1)
        populated_prompt = populated_prompt.replace("______", parent_classes, 1)
        populated_prompt = populated_prompt.replace("______", attached_files, 1)


        # 4. Update GUI to show loading state
        self.response_output.config(state=tk.NORMAL)
        self.response_output.delete("1.0", tk.END)
        self.response_output.insert(tk.END, "Communicating with Gemini... Please wait.")
        self.root.update_idletasks()

        try:
            # 5. Construct the full prompt parts for the API
            full_prompt_parts = [
                "--- SYSTEM INSTRUCTIONS (Always Follow) ---\n",
                populated_prompt,
                "\n\n--- GITHUB REPOSITORY CONTEXT ---\n",
                f"Reference this GitHub repository: {GITHUB_REPO_URL}",
                "\n\n--- USER'S REQUEST ---\n"
            ]

            # 6. Handle file upload
            uploaded_file = None
            if self.uploaded_file_path:
                print(f"Uploading file: {self.uploaded_file_path}")
                uploaded_file = genai.upload_file(path=self.uploaded_file_path)
                full_prompt_parts.append("\n\n--- UPLOADED FILE CONTEXT ---\n")
                full_prompt_parts.append(uploaded_file)

            # 7. Add the final user prompt
            full_prompt_parts.append(f"\n\n{user_prompt}")

            # 8. Generate content
            print("Generating content from Gemini...")
            response = self.model.generate_content(full_prompt_parts, request_options={"timeout": 600})


            # 9. Display the response
            self.response_output.delete("1.0", tk.END)
            self.response_output.insert(tk.END, response.text)

            # Clean up uploaded file from Gemini's storage
            if uploaded_file:
                print(f"Deleting uploaded file: {uploaded_file.name}")
                genai.delete_file(uploaded_file.name)

        except Exception as e:
            self.show_error(f"An error occurred while calling the API: {e}")
        finally:
             self.response_output.config(state=tk.DISABLED)


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! PLEASE REPLACE 'YOUR_API_KEY' IN THE SCRIPT !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        # Create the system prompt file if it doesn't exist
        if not os.path.exists(SYSTEM_PROMPT_FILE):
            with open(SYSTEM_PROMPT_FILE, "w") as f:
                f.write("You are a helpful and expert Python developer. When reviewing code, be critical and provide clear, actionable feedback. Always consider edge cases.")
        
        root = tk.Tk()
        app = GeminiApp(root)
        root.mainloop()

