import sys
import os
import Helpers.check_env_var as env
env.check_dependencies()
import logging
import argparse
import PlopRotTemp.main as plop
import Helpers.helpers as hp
import Helpers.prepare_ligand as pl
import Helpers.pele_env as pele
import Adaptive.adaptive as ad
import Adaptive.clusterAdaptiveRun as cl
import Helpers.center_of_mass as cm
import Helpers.constraints as ct
import SystemBuilder.system_prep as sp
import Box.box as bx
import ppp.mut_prep4pele as ppp
import msm.analysis as msm



COMPLEX = "complex.pdb"
RESULTS = "results"
LIG_RES = "LIG"
LIG_CHAIN = "Z"
FORCEFIELD = "OPLS2005"
PELE_CONFILE = "pele.conf"
CPUS = 5
RESTART = True
CLUSTERS = 40

ADAPTIVE_KEYWORDS = ["RESTART", "OUTPUT", "INPUT", "CPUS", "PELE_CFILE", "LIG_RES"]

EX_PELE_KEYWORDS = ["NATIVE", "FORCEFIELD", "CHAIN", "CONSTRAINTS"]

PELE_KEYWORDS = ["BOX_CENTER", "BOX_RADIUS"]

NATIVE = '''
                        {{

                           "type": "rmsd",

                           "Native": {{\n\
                            "path":\n\
                            "{}" }},\n\

                           "selection": {{ "chains": {{ "names": [ "$CHAIN" ] }} }},\n\

                           "includeHydrogens": false,\n\

                           "doSuperposition": false,\n\

                           "tag" : "ligandRMSD"\n\

                        }},\n\


'''

ADAPTIVE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "Adaptive/clusterAdaptiveRun.py"))

# Output Constants
RANKING_FILE = "Pele_ranking.txt"
OUTPUT_HEADER = "#Residue Epoch DG StdDG Db StdDb Conv\n#==================================\n"

# Folders and files
FOLDERS = ["",
           "DataLocal/Templates/OPLS2005/HeteroAtoms/",
           "DataLocal/Templates/AMBER99sb/HeteroAtoms/",
           "DataLocal/Templates/AMBER99sbBSC0/HeteroAtoms/",
           "DataLocal/LigandRotamerLibs",
           ]


# Log Constants
LOG_FILENAME = "output.out"
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(message)s"

# directory
DIR = os.path.dirname(__file__)

# Logging definition block
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMAT)
file_handler = logging.FileHandler(LOG_FILENAME, mode='w')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def run(system, residue, chain, ligands, forcefield, confile, native, cpus, core, mtor, n, mae_charges, clean, only_plop):
    
    # Preparative for Pele
    logger.info("Retrieving Ligands & Complexes")
    receptor, lig_ref = sp.retrieve_receptor(system, residue)
    complexes, ligands, residues = sp.build_complexes(ligands, receptor)
    pele_dirs = [os.path.abspath("{}_Pele".format(residue)) for residue in residues]
    native = NATIVE.format(os.path.abspath(native), chain) if native else native
    center_mass = cm.center_of_mass(lig_ref.getvalue()) 

    for residue, lig, sys, pele_dir in zip(residues, ligands, complexes, pele_dirs):
 
        logger.info("Preparing {} system".format(residue))
        system_fix, missing_residues, gaps, metals = ppp.main(sys)
        protein_constraints = ct.retrieve_constraints(system_fix, gaps, metals)

        # Produce Templates of all missing residues
        logger.info("Running PlopRotTemp")
        for res, resname, chain in missing_residues:
            logger.info("Creating template for residue {}".format(res))
            template, rotamers_file = plop.main(lig, mtor, n, core, mae_charges, clean)
            hp.silentremove([lig])
       
   
        logger.info("Creating Pele env")
        adap_ex_input = os.path.join(pele_dir, system_fix)
        adap_ex_output = os.path.join(pele_dir, "output_adaptive_exit")
        cluster_output = os.path.join(pele_dir, "output_clustering")
        adap_l_input = "{}/initial_*"
        adap_l_output = os.path.join(pele_dir, "output_adaptive_long")
        ad_ex_temp = os.path.join(pele_dir, "adaptive_exit.conf")
        ad_l_temp = os.path.join(pele_dir, "adaptive_long.conf")
        pele_temp = os.path.join(pele_dir, "pele.conf")
        box_temp = os.path.join(pele_dir, "box.pdb")
        clusters = os.path.join(cluster_output, "clusters_40_KMeans_allSnapshots.pdb")
        
        files = [os.path.basename(system_fix), os.path.join(DIR, "PeleTemplates/box.pdb"), os.path.join(DIR, "PeleTemplates/pele.conf"),
                 os.path.join(DIR, "PeleTemplates/adaptive_exit.conf"), os.path.join(DIR, "PeleTemplates/adaptive_long.conf")]
        directories = FOLDERS
        directories.extend(["output_adaptive_long", "output_adaptive_exit", "output_clustering"])
        pele.set_pele_env(system_fix, directories, files, forcefield, template, rotamers_file, pele_dir)

        
        logger.info("Preparing ExitPath Adaptive Env")
        ad.AdaptiveBuilder(pele_temp, EX_PELE_KEYWORDS, native, forcefield, chain, "\n".join(protein_constraints))
        adaptive_exit = ad.AdaptiveBuilder(ad_ex_temp, ADAPTIVE_KEYWORDS, RESTART, adap_ex_output, adap_ex_input, cpus, pele_temp, residue)
        adaptive_exit.run()  
       

        logger.info("MSM Clustering")
        with pele.cd(adap_ex_output):
            cl.main(num_clusters=CLUSTERS, output_folder=cluster_output, ligand_resname=residue, atom_ids="")

        logger.info("Create box")
        center, radius = bx.main(adap_ex_output , clusters , center_mass)
        box = bx.build_box(center, radius, box_temp)

        logger.info("Running standard Pele")
        ad.AdaptiveBuilder(pele_temp, PELE_KEYWORDS, center, radius)
        adaptive_long = ad.AdaptiveBuilder(ad_l_temp, ADAPTIVE_KEYWORDS, RESTART, adap_l_output, adap_l_input, cpus, pele_temp, residue)
        adaptive_long.run()
       
        logger.info("Extracting dG with MSM analysis") 
        msm.analyse_results(adap_l_output, residue)

    # Analyze results
    output = msm.summerize(pele_dirs, residues)
    output.insert(0, OUTPUT_HEADER)
    with open(RANKING_FILE, "w") as fout:
        fout.write("".join(output))

if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='Run Adaptive Pele Platform')
    parser.add_argument('input', type=str, help='complex to run pele on')
    parser.add_argument('residue', type=str, help='residue of the ligand to extract', default=LIG_RES)
    parser.add_argument('chain', type=str, help='forcefield to use', default=LIG_CHAIN)
    parser.add_argument('ligands', type=str, help='ligands to run pele on')
    parser.add_argument('--forc', type=str, help='chain of the ligand to extract', default=FORCEFIELD)
    parser.add_argument('--confile', type=str, help='your own pele configuration file', default=PELE_CONFILE)
    parser.add_argument('--native', type=str, help='native file to compare RMSD to', default="")
    parser.add_argument('--cpus', type=int, help='number of processors', default=CPUS)
    parser.add_argument("--core", type=int, help="Give one atom of the core section", default=-1)
    parser.add_argument("--mtor", type=int, help="Gives the maximum number of torsions allowed in each group.  Will freeze bonds to extend the core if necessary.", default=4)
    parser.add_argument("--n", type=int, help="Maximum Number of Entries in Rotamer File", default=1000)
    parser.add_argument("--mae_charges", help="Use charges in mae", action='store_true')
    parser.add_argument("--clean", help="Whether to clean up all the intermediate files", action='store_true')
    parser.add_argument("--only_plop", help="Whether to run PlopRotTemp or both", action='store_true')
    args = parser.parse_args()

    run(args.input, args.residue, args.chain, args.ligands, args.forc, args.confile, args.native, args.cpus, args.core, args.mtor, args.n, args.mae_charges, args.clean, args.only_plop)