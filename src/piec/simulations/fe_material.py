import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve # For solving the polynomial equation

"""
The purpose of this script is to create a material that can simulate whatever we want in a FE material. Goal is to be able to have a realistic FE material
that combines resistor, with dielectric with fe

ASSUMES: You pass in a V(t) you wanna apply, lets assume its 2 numpy arrays for now one is v other is t each of the same length

NOTE: Does it make sense to give it an I(t) or a V(t)? on the awg we do V(t) but for resistor than you just get a flat line
"""

class Material:
    """
    This material is the parent class that literally does nothing but passes the trace through it
    """
    def __init__(self):
        self.name = "pass_through"

    def voltage_response(self, v,t):
        """
        Returns the voltage and time arrays back
        NOTE: do we even need the t array? ima say yes since we can use the dielectric equation etc.
        
        args:
            v (ndarray): voltage array of the applied waveform
            t (ndarray): time array of the applied waveform
        """
        return v,t

class Resistor(Material):
    """
    This class simulates a resistor and be default it has 1kohm. units is in SI units
    """
    def __init__(self, resistance=1e3):
        self.resistance = resistance
        self.name = "resistor"
    
    def voltage_response(self, v, t):
        """
        Returns a linear response
        NOTE: do we even need the t array? ima say yes since we can use the dielectric equation etc.
        
        args:
            v (ndarray): voltage array of the applied waveform
            t (ndarray): time array of the applied waveform
        """ 
        return v/self.resistance, t

class Dielectric(Material):
    """
    This class simulates a pure dielectric and by default the permittivity is 1epislon_0
    """
    def __init__(self, permittivity=8.85e-12):
        self.permittivity = permittivity
        self.name = "dielectric"

    def voltage_response(self, v, t):
        """
        Returns a dielectric response
        """

class Ferroelectric(Material):
    """
    This class simulates a ferroelectric material and by default the permittivity is 1epsilon_0
    """
    def __init__(self, material_dict, temperature = 300):
        self.name = None
        self.material_dict = material_dict
        self.temperature = temperature

    
    def run_landau_hysteresis_simulation(self, V_applied_path, temperature=300):
        # This function is the same as the previous response that traces the loop.
        # It calculates and returns V_applied_path and P_loop (the ideal ferroelectric loop).
        fe = self.material_dict['ferroelectric']
        sub = self.material_dict['substrate']
        elec = self.material_dict['electrode']
        film_thickness = fe['film_thickness']
        EPSILON_0 = 8.854e-12
        #plt.plot(np.arange(len(V_applied_path)), V_applied_path)
        #V_applied_peak = V_pp / 2.0
        eta_m = (sub['lattice_a'] - fe['lattice_a']) / fe['lattice_a']
        a_strain_term = -4 * fe['Q12'] * eta_m / (fe['s11'] + fe['s12'])
        a_depol_term = elec['screening_lambda'] / (EPSILON_0 * elec['permittivity_e'] * film_thickness)
        a_tilde = fe['a0'] * (temperature - fe['T0']) + a_strain_term + a_depol_term
        b_tilde = fe['b'] + (4 * fe['Q12']**2) / (fe['s11'] + fe['s12'])
        c_tilde = fe['c']
        def landau_voltage_function(P_val):
            return (a_tilde * P_val + b_tilde * P_val**3 + c_tilde * P_val**5) * film_thickness
        def equation_to_solve(P_val, V_target):
            return landau_voltage_function(P_val) - V_target
        coeffs_for_P_squared = [5 * c_tilde, 3 * b_tilde, a_tilde]
        roots_P_squared = np.roots(coeffs_for_P_squared)
        P_switching_points = [np.sqrt(np.real(r_P2)) for r_P2 in roots_P_squared if np.isreal(r_P2) and r_P2 > 0]
        V_switching = sorted([landau_voltage_function(p_sw) for p_sw in P_switching_points])
        V_c_negative, V_c_positive = -V_switching[0], V_switching[0] # Simplified for this example
        #up_ramp = np.linspace(-V_applied_peak, V_applied_peak, num_steps_per_ramp)
        #V_applied_path = np.concatenate([up_ramp, down_ramp])
        P_loop = np.zeros_like(V_applied_path)
        P_current = fsolve(equation_to_solve, x0=-0.5, args=(V_applied_path[0]))[0]
        P_loop[0] = P_current
        on_upper_branch = (P_current > 0)
        for i in range(1, len(V_applied_path)):
            V_target = V_applied_path[i]
            V_previous = V_applied_path[i-1]
            sweeping_up = (V_target > V_previous)
            initial_guess_P = P_current
            if sweeping_up and not on_upper_branch and V_target >= V_c_positive:
                initial_guess_P = 0.5; on_upper_branch = True
            elif not sweeping_up and on_upper_branch and V_target <= V_c_negative:
                initial_guess_P = -0.5; on_upper_branch = False
            P_solution = fsolve(equation_to_solve, x0=initial_guess_P, args=(V_target))
            P_current = P_solution[0]
            P_loop[i] = P_current
        return P_loop

    def add_parasitic_effects(self, V_applied_path, P_ideal_loop):
        """
        Adds both linear dielectric and ohmic leakage effects to an ideal P-V loop.
        """
        EPSILON_0 = 8.854e-12 # F/m, vacuum permittivity 
        epsilon_r = self.material_dict['ferroelectric']['epsilon_r']
        film_thickness = self.material_dict['ferroelectric']['film_thickness']
        area = self.material_dict['electrode']['area']
        R_leak = self.material_dict['ferroelectric']['leakage_resistance']

        frequency = 1e6
        # --- Part 1: Linear Dielectric Contribution (Causes Tilt) ---
        # P_dielectric = epsilon_0 * (epsilon_r - 1) * E = epsilon_0 * (epsilon_r - 1) * V / d
        P_dielectric = EPSILON_0 * (epsilon_r - 1) * V_applied_path / film_thickness
        
        # --- Part 2: Leakage Contribution (Causes Rounding/Fattening) ---
        num_points = len(V_applied_path)
        period = 1.0 / frequency
        delta_t = period / num_points
        leakage_integral_term = np.cumsum(V_applied_path) * delta_t
        P_leak_loop = (1 / (area * R_leak)) * leakage_integral_term

        # --- Part 3: Total Measured Polarization ---
        P_total_loop = P_ideal_loop + P_dielectric + P_leak_loop
        
        return P_total_loop, P_dielectric + P_ideal_loop
   
    def apply_waveform(self, v, t):
        """
        Applies a voltage waveform to the ferroelectric material and returns the response.
        
        args:
            v (ndarray): voltage array of the applied waveform
            t (ndarray): time array of the applied waveform
        """
        # Placeholder for actual ferroelectric response logic
        # For now, just return the voltage and time arrays
        import matplotlib.pyplot as plt
        g = plt.plot(t,v)
        plt.title("Checking input waveform")
        plt.show()
        print("max and min of v", max(v), min(v))
        self.t = t
        
        import matplotlib.pyplot as plt
        
        p_ideal = self.run_landau_hysteresis_simulation(v)
        p_total, p_noise = self.add_parasitic_effects(v, p_ideal)

        print("P_total INDEX 0:", p_total[0])
        p_total[-0] = p_total[-1]
        p_total[0] = 0
        print("P_total INDEX 0:", p_total[0])

        #plt.plot(v, p_total)
        
        #p_total.pop(0)
        #t.pop(0)
        # Sawyer-Tower circuit formula
        su = plt.plot(v, p_total, label='modeld p loop')
        plt.title('modeld p loop')
        plt.show()
        self.output_voltage = (np.gradient(p_total, t))*50*self.material_dict['electrode']['area']
        self.output_voltage[0:10] = self.output_voltage[10]
        #p_total*self.material_dict['electrode']['area']/(10e-6) #multiply current by 50 ohm to get voltage response,
        
        #plt.plot(v, self.output_voltage, label='Voltage Response')

    def get_voltage_response(self):
        return self.output_voltage, self.t #multiply current by 50 ohm to get voltage response,
        



