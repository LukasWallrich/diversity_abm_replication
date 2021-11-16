from mesa.batchrunner import BatchRunner

import httpimport

url = "https://gist.githubusercontent.com/LukasWallrich/05f445821fbae694b37a205dc08b2b4f/raw/6163cfc6aaa9eba33738f42c5b1a35cff1053005"

with httpimport.remote_repo(["HPmodel"], url):
    from HPmodel import HPProblem

fixed_params = {"n": 2000, "k": 3}

variable_params = {"l": (12, 20), "N_agents": (10, 20)}

batch_run = BatchRunner(
    HPProblem,
    variable_params,
    fixed_params,
    iterations=500,
    max_steps=100,
    model_reporters={
        "agent_descriptives": lambda m: m.agent_descriptives,
        "solution": lambda m: m.best_solution,
    }
)

batch_run.run_all()

