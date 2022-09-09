#######
#
# NB: This file was used to run analyses on Google Cloud Engine (GCE).
# Please refer to the files in the subfolders (Hong_and_Page and Grim_et_al)
# for commented code showing the different analyses that were used, and to the
# README regarding the workflow used with GCE.
#
#######

from datetime import datetime
from mesa.batchrunner import BatchRunnerMP
import httpimport

GCE.PREFIX = "GrimSweepTournament" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

URL = "https://gist.githubusercontent.com/LukasWallrich/42dea3211f0bde452781dd9b69c8199a/raw/"

with httpimport.remote_repo(["Gmodel"], URL):
    from Gmodel import GProblem


fixed_params = {"n": 2000, "k": 3, "N_agents": 10, "strategy": "both"}
variable_params = {"smoothness": list(range(21)), "l": range(4, 31)}

batch_run = BatchRunnerMP(
    GProblem,
    nr_processes = 32,
    variable_parameters=variable_params,
    fixed_parameters=fixed_params,
    iterations=40,
    max_steps=100,
    model_reporters={
        "agent_descriptives": lambda m: m.agent_descriptives,
        "best_solution": lambda m: m.best_solution,
    },
)
batch_run.run_all()

out = batch_run.get_model_vars_dataframe()
