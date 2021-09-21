from mesa.batchrunner import BatchRunner
from model import Problem

fixed_params = {
    "n": 2000,
    "k": 3,
}

variable_params = {"l": (12, 20),
"N_agents": (10, 20),
"selection_method": ("best", "random")
}

batch_run = BatchRunner(
    Problem,
    variable_params,
    fixed_params,
    iterations=2,
    max_steps=100,
    model_reporters={"agent_descriptives": lambda m: m.agent_descriptives,
    "solution": lambda m: m.best_solution
    }
)

batch_run.run_all()

# == Main == #
n = 2000        # Length of problem
k = 3           # No of positions to consider
l = 12         # Max lookahead

N_agents = 10    

runs = 50

current_problem = 0

problems = list()
problems.append(Problem(n))

descriptives_agents = list()
descriptives_solution = list()

