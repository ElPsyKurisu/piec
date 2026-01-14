Anisotropic Magnetoresistance (AMR) Measurements
================================================

Anisotropic Magnetoresistance (AMR) is a magnetotransport phenomenon observed in ferromagnetic materials where the electrical resistance of the material changes with respect to the angle between the direction of electric current and the orientation of magnetization.

Theoretical Background
----------------------
The AMR effect arises from spin-orbit interaction. When an external magnetic field aligns the magnetization of the material, the scattering of conduction electrons depends on the direction of their spin relative to their motion and the magnetization direction. This typically results in a resistance that varies as cos²(θ), where θ is the angle between the current and magnetization.
AMR measurements involve:
* Applying a constant current through the sample.
* Rotating the sample in a constant applied magnetic field (strong enough to saturate the magnetization).
* Measuring the sample's resistance (or voltage, which is proportional to resistance at constant current) as a function of the angle θ.

Using ``piec`` for AMR Measurements
-----------------------------------
The :class:`~piec.measurement.magneto_transport.AMR` class is designed for performing AMR experiments. This class typically controls a Digital Multimeter (DMM) or lock-in amplifier to measure resistance/voltage, a current source (often part of a calibrator or lock-in), a stepper motor for sample rotation, and a power supply for an electromagnet (via a calibrator providing a control voltage).

**Example:**

.. code-block:: python

   from piec.measurement.magneto_transport import AMR
   # Assuming dmm_obj, calibrator_obj, arduino_obj (for stepper), and lockin_obj
   # are pre-initialized instrument objects.
   # e.g., dmm_obj = Keithley193A('GPIB::DMM_ADDRESS::INSTR')
   #       calibrator_obj = EDC522('GPIB::CALIBRATOR_ADDRESS::INSTR')
   #       arduino_obj = Arduino('COM_PORT_ARDUINO')
   #       lockin_obj = SR830('GPIB::LOCKIN_ADDRESS::INSTR')


   amr_experiment = AMR(
       dmm=dmm_obj,
       calibrator=calibrator_obj,
       arduino=arduino_obj,
       lockin=lockin_obj,
       field=1000.0,         # Desired magnetic field in Oersted
       angle_step=15,        # Step size for angle in degrees
       total_angle=360,      # Total angle to rotate in degrees
       amplitude=1.0,        # Lock-in reference voltage amplitude (V)
       frequency=13.7,       # Lock-in reference frequency (Hz)
       measure_time=60,      # Time to average at each data point (s)
       sensitivity='50uV/nA',# Lock-in sensitivity
       save_dir="path/to/save/data",
       voltage_callibration=10000 # Oe/V for field control
   )

   # To run the full experiment:
   # amr_experiment.run_experiment()

Key Parameters
--------------
Important parameters for the ``AMR`` class initialization include:
* ``dmm``, ``calibrator``, ``arduino``, ``lockin``: Initialized instrument objects.
* ``field`` (float): The magnetic field strength in Oersted to be applied during rotation.
* ``angle_step`` (float): The increment in angle (degrees) for each measurement point.
* ``total_angle`` (float): The total angular range of the measurement (degrees).
* ``amplitude`` (float), ``frequency`` (float): Parameters for the lock-in amplifier's reference signal.
* ``measure_time`` (float): Duration in seconds for averaging data at each angular step.

Workflow
--------
The ``run_experiment()`` method in the ``AMR`` class performs the following sequence:
1.  **Initialize Instruments**: Checks communication and sets up instruments.
2.  **Set Field**: Applies the specified magnetic field.
3.  **Configure Lock-in**: Sets up the lock-in amplifier with specified frequency, amplitude, and sensitivity.
4.  **Capture Data Loop**:
    * Iterates through angles from 0 to `total_angle` with `angle_step`.
    * At each angle, moves the stepper motor.
    * Captures data (e.g., X and Y components from lock-in) averaged over `measure_time`.
    * Saves the data point.
5.  **Shut Off**: Turns off the magnetic field.
6.  **Analyze (Placeholder)**: The base `analyze` method is a placeholder; specific analysis would typically involve fitting the R(θ) data to a cos²(θ) function.

API Reference
-------------
* :class:`~piec.measurement.magneto_transport.MagnetoTransport` (Base class)
* :class:`~piec.measurement.magneto_transport.AMR`