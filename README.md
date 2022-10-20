# Does diversity trump ability? Replication of two ABM studies

This repo contains code that replicates the model proposed by Hong & Page (2004), who suggested that diversity trumps ability, i.e. that a randomly selected group of problem solvers outperforms a group of the best problem solvers, who will be less diverse.

It also contains replication code for Grim et al. (2019), who extended the model and proposed that the original results only apply to domains where there is no/little expertise.

It is based on the [mesa](https://github.com/projectmesa/mesa) framework.

## Background: The [mesa](https://github.com/projectmesa/mesa) framework

Mesa is a Python-based framework for agent-based modeling. It provides support for agent activation, parameter sweeps, reporting and visualisation. Here, just two key functionalities are used: the `BaseScheduler` class takes care of the activation of agents and the `BatchRunnerMP` class conducts parameter sweeps with multi-core processing. To enable this, agents are derived from the mesa `Agent` class and the problems from the mesa `Model` class.

# Structure of the repo

Each of the two replications is contained in its own folder - `Hong and Page` and `Grim et al.`. In these folders, **the model code is contained in `HPmodel.py` and `Gmodel.py` respectively.** In addition, each of the folders contains `run_simulation.py` files (or similar) that actually create the simulation runs presented in the articles, and a Jupyter notebook (`analysis.ipynb`) that reads in simulation results to summarise and visualize them. The `run_simulation.py` file in the root folder is only present to specify which simulation should be run on Google Cloud Engine - see below.

# Requirements

To install the requirements, you can run

```
    $ pip install -r requirements.txt
```

Note that there has been an issue with installing mesa from conda - so we recommend using pip.

# Running the simulations on Google Cloud Engine (GCE)

The simulations to replicate Hong & Page can feasibly be run on a laptop in a matter of hours. However, by the time it comes to the parameter sweep needed for the strategy comparisons in the Grim et al. paper, 56,700 runs are needed, which each involve the evaluation of up to 24,360 possible heuristics for 2000 starting locations. On a 32-core Virtual Machine, this took just 22.5 hours. However, it probably took me as long to figure out how to conveniently deploy such scripts to GCE.

When I failed to find a simple solution, I created the [pyscript2gce](https://github.com/LukasWallrich/pyscript2gce-production) helper, which creates a Docker container that executes a script when launched and saves the results. Once set up, all it takes to run a script is to push an update to a specified file (here: `run_simulation.py`) and start up a VM with a single line terminal command. For that, [a GitHub action](https://github.com/LukasWallrich/diversity_abm_replication/blob/main/.github/workflows/push_gist.yml) pushes changes to that file automatically to a Gist, which is then accessed by the VM, based on [this version](https://github.com/LukasWallrich/pyscript2gce-production/releases/tag/Diversity-ABM-replication) of pyscript2gce. The README of pyscript2gce details how this can be set up. Note that you do not need to change anything in the Python code in `pyscript2gce` except for the link to the Gist in `run_simulation.py` if you use the release linked to above given that it relies on importing the actual simulation code from the Gist.



# Citations

1. Hong, L., & Page, S. E. (2004). Groups of diverse problem solvers can outperform groups of high-ability problem solvers. Proceedings of the National Academy of Sciences, 101(46), 16385-16389.

2. Grim, P., Singer, D. J., Bramson, A., Holman, B., McGeehan, S., & Berger, W. J. (2019). Diversity, ability, and expertise in epistemic communities. Philosophy of Science, 86(1), 98-123.
