# Used this import of HPModel to avoid duplicating files
import httpimport
url = "https://gist.githubusercontent.com/LukasWallrich/05f445821fbae694b37a205dc08b2b4f/raw/"

with httpimport.remote_repo(["HPmodel"], url):
     from HPmodel import HPProblem, PSAgent

# Alternative: download file into same folder, then run
# from HPmodel import HPProblem, PSAgent

import pandas as pd
import numpy as np
from copy import copy

class GrimAgent(PSAgent):
    """Agent for Hong-Page problem-solving model as extended by Grim et al.

    This agent forms part of a team that searches for the optimal solution in the landscape presented. The
    only extention from the PSAgent class is that the agent can now search in a tournament strategy, not just in a relay.

    Attributes:
        heuristic: List of step lengths this agent can consider.
        team: Team this agent belongs to. Either "random" or "best" in standard HPProblem.
        best_solution: Best solution found by this agent so far.
    """

    def step(self):
        """Search for highest peak accessible with own heuristic, in tournament or relay mode (called by mesa)"""        
        if self.problem.strategy == "relay":
           self.focus, self.best_solution = self.problem.max_search(agent = self)
        if self.problem.strategy == "tournament":
           self.focus, self.best_solution = self.problem.max_search(agent = self, update = False)


class GProblem(HPProblem):

    """Hong & Page problem-solving model, extended by Grim et al, to assess performance of different teams.

    This mesa-based agent-based model implements the model described by Grim et al. (2019),
    which extends the original model by Hong & Page (2004) to account for landscapes of varying smoothness 
    and to contrast the original 'relay' model with a 'tournament' model. 

    Attributes:
        agent_descriptives: Dict with descriptive statistics for agents in each team (i.e. random and best).
        best_solution: Dict with best solution found by each team so far.

    Methods:
        max_search: Evaluate a heuristic across all starting points, or have an agent search from their current location.
        step: Advance model by one step.    
    """

    def __init__(self, n: int, k: int, l: int, N_agents: int, smoothness: int, seed:int = None, strategy: str = "relay", agent_class: PSAgent = GrimAgent):
        """Initializes problem, assesses heuristics and creates agent teams
        
        Initializes Hong & Page model as extended by Grim et al by drawing a smoothed solution landscape, 
        assessing the performance of all heuristics, and creating best and random agent teams.

        Args:
            n: Length of solution landscape
            k: Number of steps to include in each heuristic
            l: Maximum step size to be considered when drawing heuristics
            N_agents: Number of agents in each team
            smoothness: Smoothness of solution landscape, i.e. the average distance between randomly selected points between which the solution is interpolated.
            seed: Random seed for reproducibility
            strategy: 
              Problem solving strategy for teams. Can be 'relay', 'tournament' or 'both. In 'relay' mode, agents sequentially search for improvements,
              if they find one, their entire team moves to their improved solution and the next agent continues from there. In 'tournament' mode, each
              agent independently searches for improvements, and then the teams move to the best solution found in that round.
    
        """        
        self.draw_G_solution(n, smoothness)
        super().__init__(n, k, l, N_agents, seed, agent_class = agent_class)
        self.strategy = strategy

    def draw_solution(self, n):
        """Overridden in favor of draw_G_solution"""        
        pass

    def draw_G_solution(self, n: int, smoothness: int) -> None:
        """Generate solution landscape of length n, consisting of random values approximately smoothness apart and interpolated"""        
        if (smoothness == 0):
            super().draw_solution(n)
        else:    
            i = 0
            solution = pd.Series(np.nan for x in range(n))
            while(i < n): # Create random heights on average every `smoothness` steps apart
                solution[i] = self.random.uniform(0, 100)
                i += 1+self.random.randrange(2*smoothness)
                
            # Unless last value is already specified, close the circle    
            if (pd.isna(solution[n-1])):
                solution[n] = solution[0]
            # Interpolate between specified points        
            solution = solution.interpolate().tolist()    
            if (len(solution) > n):
                solution.pop()
                
            self.solution = solution              

    def tournament_step(self) -> None:
        """
        Searches the landscape in tournament mode, starting from each position. Each agent searches individually for the best location they can reach, 
        then teams move to the best location identified by team members. In the end, the best_solution attribute is updated with the average of the solutions 
        found by each team across the starting positions.
        """        
        solutions = list()
        for i in range(self.n):
            self.current_position = dict.fromkeys(self.current_position, i)
            self.best_solution = dict.fromkeys(self.best_solution, self.solution[i])
            while True: #Until the solution no longer improves on a full pass through the agents
                old_solution = self.best_solution
                self.schedule.step() # Have each agent move to max position they can reach
                # Update current position of each team based on maximum of agent positions
                pos = [{"team": a.__getattribute__("team"), "solution": a.__getattribute__("best_solution"), "focus": a.__getattribute__("focus")} for a in self.schedule.agents]
                teams = set(d["team"] for d in pos)
                self.current_position = {t:max(list(filter(lambda d: d['team'] == t, pos)), key = lambda x:x["solution"])["focus"] for t in teams} 
                self.best_solution = {t:max(list(filter(lambda d: d['team'] == t, pos)), key = lambda x:x["solution"])["solution"] for t in teams}
                if old_solution == self.best_solution:
                    solutions.append(copy(self.best_solution))
                    break
        self.running = False  
        self.best_solution = self.dict_mean(solutions)

    def step(self) -> None:
        """Have agent teams search for solution, following specified strategy/strategies 
        
        This runs the simulation, going through each starting point in the landscape and getting agent teams to search for the best solution they can achieve, using either the relay or tournament strategy - or both sequentially. At the end, the best_solution attribute is updated with the average performance of each team (under each strategy, if both are simulated).

        """        
        if(self.strategy == "both"):
            self.strategy = "relay"
            super().step()
            sol = {"relay_" + str(key): val for key, val in self.best_solution.items()}
            self.strategy = "tournament"
            self.tournament_step()
            self.best_solution = dict(sol, **{"tournament_" + str(key): val for key, val in self.best_solution.items()})
            self.strategy = "both"
            return None

        if self.strategy == "relay":
            super().step()
        if self.strategy == "tournament":
            self.tournament_step()
            self.running = False  

