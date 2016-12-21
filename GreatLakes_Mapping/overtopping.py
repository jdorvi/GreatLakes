#!/usr/bin/env python
"""
####################################################################################################
Calculate overtopping rates based on FEMA Guidelines and Specifications for Flood Hazard Mapping
Partners (Jan 2005).
Python=3
####################################################################################################
DATA INPUTS
H_MO = significant wave height at the toe of the structure
T_p = peak wave period
Beta = angel of wave attack
F_C = freeboard
h_s = the 2% depth of water at the toe of the structure
GEOMETRY
B = Berm height
W = Berm width
ETA = Forshore slope
ALPHA = Structure slope

OUTPUTS
q = Dimensionless rate of overtopping
Q =

####################################################################################################
Author: J. Dorvinen
Email: jdorvinen@dewberry.com
Date: 12/20/2016
####################################################################################################
"""
# Import required modules
import pandas as pd
import numpy as np
from dataIO import dbf2df, df2dbf

# Import transect data
h = 'number'
H_MO = 'number'
F_C = 'number'
L_OM = 'number'
g_B = 'number'
g_P = 'number'
g_r = 'number'
g_beta = 'number'
irribaren = 'number'
g = 32.1740 # ft/(s**2)

S_OP = 'number'
TAN_ALPHA = 'number'

# Define helper functions
def normal_slope():
    """ Table D.4.5-7 'Equations for Wave Overtopping', normally sloping structures. """
    if irribaren <= 1.8:
        # Breaking waves
        f_prm = (F_C/H_MO) * ((S_OP**0.5)/TAN_ALPHA) * 1/(g_r*g_B*g_beta*g_P)
        q_big = 0.06*np.exp**(-4.7*f_prm)
        q_sml = q_big * ((g*(H_MO**3)*TAN_ALPHA)/S_OP)**(0.5)

        f_prm_1 = (F_C/H_MO) * 1/(g_r*g_beta)
        q_big_1 = 0.2*np.exp**(-2.3*f_prm)
        q_sml_1 = q_big * (g*(H_MO**3))**(0.5)

        if q_sml > q_sml_1:
            f_prm = f_prm_1
            q_big = q_big_1
            q_sml = q_sml_1

    elif irribaren > 1.8:
        # Non-Breaking waves
        f_prm = (F_C/H_MO) * 1/(g_r*g_beta)
        q_big = 0.2*np.exp**(-2.3*f_prm)
        q_sml = q_big * (g*(H_MO**3))**(0.5)

    return q_sml, q_big

def steep_slope():
    """ Table D.4.5-7 'Equations for Wave Overtopping', steeply sloping structures. """
    h_star = (h**2)/(H_MO*L_OM)

    if All_approaching_waves_broken == False:
        # Some approaching waves are broken
        if h_star >= 0.3:
            # Non-Breaking waves
            q_big = 0.05*np.exp**(-2.78*(F_C/H_MO))
            q_sml = q_big*(g*(H_MO**3))**(0.5)

        elif h_star < 0.3:
            # Breaking waves
            f_prm = (F_C/H_MO)*h_star
            q_big = 0.000137*f_prm**(-3.24)
            q_sml = q_big * (g*(h**3))**(0.5) * h_star**2

    elif All_approaching_waves_broken == True:
        # All approaching waves are broken
        if structure_toe <= dwl2wl:
            # Structure toe below the DWL2% Water Level
            if ((F_C/H_MO)*h_star) <= 0.03:
                q_big = 0.000027*np.exp**(-3.24*((F_C/H_MO)*h_star))

        elif structure_toe > dwl2wl:
            # Structure toe above the DWL2% Water Level
            q_big = 0.06*np.exp**(-4.7*F_C*(S_OP**(-0.17)))

        q_sml = q_big * (g*(h**3))**(0.5) * h_star**2

    return q_sml, q_big

def shallow_slope():
    """ Table D.4.5-7 'Equations for Wave Overtopping', shallow sloping foreshore. """
    h_star = (h**2)/(H_MO*L_OM)

    if foreshore_slope < (1/2.5) and irribaren > 7:
        f_prm = F_C/(g_r*g_beta*H_MO*(0.33+0.022*irribaren))
        q_big = 0.21 * ((g*(H_MO**3))**(0.5)) * np.exp**(-f_prm)
        q_sml = q_big * (g*(h**3))**(0.5) * h_star**2

    return q_sml, q_big

# Define main function
def main():
    """ Main function to calculate overtopping. """
    if TAN_ALPHA > (1/15) and TAN_ALPHA < (1/1.5):
        # Normally sloping structure
        q_sml, q_big = normal_slope()

    elif TAN_ALPHA >= (1/1.5):
        # Steeply sloping or Vertical structures
        q_sml, q_big = steep_slope()

    elif TAN_ALPHA <= (1/15):
        # Shallow foreshore slopes
        q_sml, q_big = shallow_slope()

    return q_sml, q_big

# Call main function
if __name__ == '__main__':
    main()
