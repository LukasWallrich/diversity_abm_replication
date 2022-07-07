from mesa.batchrunner import BatchRunnerMP

import httpimport

url = "https://gist.githubusercontent.com/LukasWallrich/05f445821fbae694b37a205dc08b2b4f/raw/"

with httpimport.remote_repo(["HPmodel"], url):
    from HPmodel import HPProblem

fixed_params = {"n": 2000, "k": 3}

variable_params = {"l": (12, 20), "N_agents": (10, 20)}

batch_run = BatchRunnerMP(
    HPProblem,
    16,
    variable_parameters = variable_params,
    fixed_parameters = fixed_params,
    iterations=500,
    max_steps=100,
    model_reporters={
        "agent_descriptives": lambda m: m.agent_descriptives,
        "solution": lambda m: m.best_solution,
    }
)

batch_run.run_all()

out = batch_run.get_model_vars_dataframe()

#Save results to pickle - unless the script is run by `pyscript2gce`
#in which case it will be saved to Cloud Storage automatically
import os
import datetime
if not 'AM_I_IN_A_DOCKER_CONTAINER' in os.environ:
    out.to_pickle("HPmodel_results_"+ datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+".pkl")
