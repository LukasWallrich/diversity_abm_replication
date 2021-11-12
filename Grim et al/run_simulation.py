#Start with pip install -r requirements.txt
from G_model import GProblem
from mesa.batchrunner import BatchRunnerMP
import pandas as pd
import numpy as np
from functools import partial

pd.set_option("precision", 3)

fixed_params = {"n": 2000,
               "k": 3,
               "N_agents": 10,
               "l": 12
               }
variable_params = {
                   "smoothness": list(range(21))
                   }

batch_run = BatchRunnerMP(GProblem,
                        16,
                        variable_parameters = variable_params,
                        fixed_parameters = fixed_params,
                        iterations=500,
                        max_steps=100,
                        model_reporters={"agent_descriptives": lambda m: m.agent_descriptives,
                        "best_solution": lambda m: m.best_solution})
batch_run.run_all()

res = batch_run.get_model_vars_dataframe()

# Turn dictionaries into columns
res = pd.concat([res.drop(["best_solution"], axis = 1), res.best_solution.apply(pd.Series).add_suffix("_solution")], axis = 1)

def renamer(col, prefix):
    if col.endswith("agent"):
        return col
    else:
        return prefix + col

res_random = res.agent_descriptives.apply(pd.Series).random.apply(pd.Series).rename(mapper = partial(renamer, prefix = "random_"), axis = "columns")

res_best = res.agent_descriptives.apply(pd.Series).best.apply(pd.Series).rename(mapper = partial(renamer, prefix = "best_"), axis = "columns")

res = pd.concat([res.drop(["agent_descriptives"], axis=1), res_best, res_random[res_random.columns[pd.Series(res_random.columns).str.startswith('random_')]]], axis=1)

res["run_id"] = res.reset_index().index
res = res.rename(columns={"best_agent": "top_agent"})

#Pivot so that random and best groups can be easily compared
col_names = res.columns.values.tolist()

def check_var(col_name):
    return not(col_name.find("random_") != -1 or col_name.find("best_") != -1)


id_cols = list(filter(check_var, col_names))

out = pd.melt(res, id_cols)

out = out.join(out.variable.str.split("_", expand = True)).rename(columns={0:"team_type"}).pivot_table(index=id_cols + ["team_type"], columns=[1], values="value").reset_index()

out.to_csv("model_results.csv")