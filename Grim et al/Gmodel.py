# Used this to avoid duplicating files
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
    def step(self):
        """Search for highest peak accessible with own heuristic, in tournament or relay mode (called by mesa)"""        
        if self.problem.strategy == "relay":
           self.focus, self.best_solution = self.problem.max_search(agent = self)
        if self.problem.strategy == "tournament":
           self.focus, self.best_solution = self.problem.max_search(agent = self, update = False)

class GProblem(HPProblem):
    def __init__(self, n, k, l, N_agents, smoothness, seed = None, strategy = "relay", agent_class = GrimAgent):
        """Initialize problem, assess heuristics and create agent teams, considering smoothness and strategy given"""        
        self.draw_G_solution(n, smoothness)
        super().__init__(n, k, l, N_agents, seed, agent_class = agent_class)
        self.strategy = strategy

    def draw_solution(self, n):
        """Overridden in favor of draw_G_solution"""        
        pass

    def draw_G_solution(self, n, smoothness):
        """Generate solution landscape: n numbers, random values ~smoothness apart and interpolated"""        
        if (smoothness == 0):
            super().draw_solution(n)
        else:    
            i = 0
            solution = pd.Series(np.nan for x in range(n))
            while(i < n):
                solution[i] = self.random.uniform(0, 100)
                i += 1+self.random.randrange(2*smoothness)
                
            #Unless last value is specified, close the circle    
            if (pd.isna(solution[n-1])):
                solution[n] = solution[0]     
            solution = solution.interpolate().tolist()    
            if (len(solution) > n):
                solution.pop()
                
            self.solution = solution              

    def tournament_step(self):
        """Take next step in tournament mode - have each agent search individually, 
        then teams move to best location identified by team members
        """        
        solutions = list()
        for i in range(self.n):
            self.current_position = dict.fromkeys(self.current_position, i)
            while True:
                old_solution = self.best_solution
                self.schedule.step()
                pos = [{"team": a.__getattribute__("team"), "solution": a.__getattribute__("best_solution"), "focus": a.__getattribute__("focus")} for a in self.schedule.agents]
                teams = set(d["team"] for d in pos)
                self.current_position = {t:max(list(filter(lambda d: d['team'] == t, pos)), key = lambda x:x["solution"])["focus"] for t in teams}
                self.best_solution = {t:max(list(filter(lambda d: d['team'] == t, pos)), key = lambda x:x["solution"])["solution"] for t in teams}
                if old_solution == self.best_solution:
                    solutions.append(copy(self.best_solution))
                    break
        self.running = False  
        self.best_solution = self.dict_mean(solutions)

    def step(self):
        """Have agent teams search for solution, following specified strategy/strategies 
        (called by mesa, should only take one step)
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

