from mesa.batchrunner import BatchRunnerMP

import httpimport

url = "https://gist.githubusercontent.com/LukasWallrich/42dea3211f0bde452781dd9b69c8199a/raw/"

with httpimport.remote_repo(["Gmodel"], url):
    from Gmodel import GProblem

fixed_params = {"n": 2000,
               "k": 3,
               "N_agents": 10,
               "l": 12,
               "strategy": "relay"
               }
variable_params = {
                   "smoothness": list(range(21))
                   }

# Run simulations with various parameter combinations
# `nr_processes` represents the number of processes to use - typically the number of cores on your machine
# `iterations` represents the number of landscapes
# `max_steps` is the maximum number of steps the model takes. Given the design 
# of the HPModel.step() function, it should never have to take more than 1.

batch_run = BatchRunnerMP(GProblem,
                        16,
                        variable_parameters = variable_params,
                        fixed_parameters = fixed_params,
                        iterations=500,
                        max_steps=100,
                        model_reporters={"agent_descriptives": lambda m: m.agent_descriptives,
                        "best_solution": lambda m: m.best_solution})
batch_run.run_all()

out = batch_run.get_model_vars_dataframe()

#Save results to pickle - unless the script is run by `pyscript2gce`
#in which case it will be saved to Cloud Storage automatically
import os
import datetime
if not 'AM_I_IN_A_DOCKER_CONTAINER' in os.environ:
    out.to_pickle("HPmodel_results_"+ datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+".pkl")