import sys

##############################################

# PUBLIC CONSTANTS (to change by the user)
# Preparation inputs to grow
ITERATIONS = 10
SELECTION_CRITERIA = "Binding Energy"
# PELE parameters
CONTROL_TEMPLATE = "control_template.conf"
RESULTS_FOLDER = "growing_output"
PATH_TO_PELE = "/home/dsoler/cleanPELE_rev/build_gnu/Pele_mpi"
PATH_TO_LICENSE = "/sNow/easybuild/centos/7.4.1708/Skylake/software/PELE/licenses/"
REPORT_NAME = "report"
TRAJECTORY_NAME = "trajectory"
CPUS = 48
PELE_EQ_STEPS = 20
# Clustering parameters
DISTANCE_COUNTER = 4
CONTACT_THRESHOLD = 0.3
EPSILON = 0.5
# PlopRotTemp parameters
SCHRODINGER_PY_PATH = "/sNow/easybuild/centos/7.4.1708/Skylake/software/schrodinger2017-4/utilities/python"

##############################################

# PRIVATE CONSTANTS (not to change)
TEMPLATES_PATH = "DataLocal/Templates/OPLS2005/HeteroAtoms/"
ROTAMERS_PATH = "DataLocal/LigandRotamerLibs/"
PDBS_OUTPUT_FOLDER = "PDBs_growing"
OUTPUT_FOLDER = "growing_results/"
TEMPLATES_FOLDER = "growing_templates"
CONFIG_PATH = "log_configure.ini"
PLOP_PATH = "PlopRotTemp_S_2017/ligand_prep.py"
ROTRES = 30
# Clustering constants
CONDITION = "min"   #   min or max
METRICS_WEIGHTS = "linear"
NUM_CLUSTERS = 5
# Messages constants
TEMPLATE_MESSAGE = "We are going to transform the template _{}_ into _{}_ in _{}_ steps! Starting..."
LINES_MESSAGE = "\n•*´¨`*•.¸¸.•*´¨`*•.¸¸.•*´¨`*•.¸¸.•*´¨`*•.¸¸.••*´¨`*•.¸¸.•*´¨`*•.¸¸.•*´¨`*•.¸¸.•*´¨`*•.¸¸.•\n"
SELECTED_MESSAGE = "\n============ Files selected ============\nControl file: {}\nPDB file: {}\nResults folder name: {}\nStep: {}\n"
FINISH_SIM_MESSAGE = "SIMULATION {} COMPLETED!!! "

##############################################