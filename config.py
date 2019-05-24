import os
# Enter values
depth_of_interest = 4000
total_depth = 12000
hole_size = 6.5
slack_off = 0
thermal_gradient = 1.8
burst_backup = 0.465
min_section = 500
mop = 100000
leak_resistance = False

# Units
depth_unit = 'ft'
diameter_unit = 'in'
weight_unit = 'lbf'
thermal_unit = 'degF'
pressure_grad_unit = 'psi/ft'

# Safety Factors
SF_joint = 1.8
SF_burst = 1.1
SF_collapse = 1.1
SF_tensile = 1.5

# Other variables
root = os.path.dirname(os.path.abspath(__file__))
conn = 0
