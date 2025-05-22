Using the Piec GUIs
===================


``piec`` provides Graphical User Interfaces (GUIs) for easier interaction with some of its functionalities, allowing for quick testing and experiment control without extensive coding.

Installation/Running GUIs
-------------------------
To open a GUI, you typically run the desired Python file from the ``piec/guis`` folder within the repository.

**Example:**
To run the ``gui.py`` file located in the ``piec/guis`` folder (assuming ``piec`` is installed and your current directory is the root of the piec repository or the ``piec`` package is in your PYTHONPATH):

.. code-block:: console

   # Ensure piec is installed, e.g., from your local editable install
   # pip install -e .  (from the root of the piec repository)
   # or ensure the piec/guis path is correct relative to your execution
   
   python path/to/piec/guis/gui.py 
   # Or, if piec is installed and GUIs are packaged as entry points (check setup.py):
   # some_piec_gui_command

Please refer to the specific README or documentation within the ``piec/guis`` directory for details on individual GUIs and their dependencies.