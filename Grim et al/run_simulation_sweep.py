from mesa.batchrunner import BatchRunnerMP

import httpimport

url = "https://gist.githubusercontent.com/LukasWallrich/42dea3211f0bde452781dd9b69c8199a/raw/"

with httpimport.remote_repo(["Gmodel"], url):
    from Gmodel import GProblem


fixed_params = {"n": 2000,
               "k": 3,
               "N_agents": 10,
               "strategy": "both"
               }
variable_params = {
                   "smoothness": list(range(21)),
                   "l": range(4, 31)
                   }

batch_run = BatchRunnerMP(GProblem,
                        32,
                        variable_parameters = variable_params,
                        fixed_parameters = fixed_params,
                        iterations=100,
                        max_steps=100,
                        model_reporters={"agent_descriptives": lambda m: m.agent_descriptives,
                        "best_solution": lambda m: m.best_solution})
batch_run.run_all()

out = batch_run.get_model_vars_dataframe()