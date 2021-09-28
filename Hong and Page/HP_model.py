
#%%
from statistics import mean
from collections import Counter
from itertools import permutations
import pdb
from mesa import Agent, Model
from mesa.time import BaseScheduler, RandomActivation
import time
import copy

#%%
class PSAgent(Agent):
    
    def __init__(self, problem, id, team, k = None, l = None, heuristic = None):
        super().__init__(id, problem)

        if heuristic == None:
            self.draw_heuristic(k, l)
        else:
            self.heuristic = heuristic    
        self.best_solution = 0
        self.initialise_focus(problem)
        self.problem = problem
        self.team = team

    def draw_heuristic(self, problem, k, l):
        self.heuristic = problem.random.sample(range(1,l+1) , k)

    def initialise_focus(self, problem):
        self.focus =  problem.random.randint(0, problem.n - 1)

    def step(self):
        self.focus, self.best_solution = self.problem.max_search(agent = self)

class Problem(Model):
    def __init__(self, n, k, l, N_agents, seed = None, schedule = "base"):
        
        if schedule == "base":
            self.schedule = BaseScheduler(self)
        if schedule == "random":
            self.schedule = RandomActivation(self)
        self.agent_descriptives = {}
        self.n = n
        self.draw_solution(n)
        self.optimal_solution = max(self.solution)
        self.best_solution = {"random": 0, "best": 0}
        self.current_position = {"random": self.random.randint(0, self.n - 1), "best": self.random.randint(0, self.n - 1)} #Start search at random position
        self.running = True
        self.draw_agents(k, l, N_agents)


    def draw_agents(self, k, l, N_agents):
        start = time.time()
        heuristics = self.evaluate_heuristics(self.generate_heuristics(k, l))
        #print(time.time() - start, "sec to evaluate heuristics")
        descriptives = {
            "worst_agent": min(heuristics.values()),
            "average_agent": mean(heuristics.values()),
            "top_agent": max(heuristics.values())        
            }
        for team_type in ["random", "best"]:

            if team_type == "random":
                heuristics_selected = self.__sample_from_dict(heuristics, N_agents)
            if team_type == "best":
                heuristics_selected = dict(Counter(heuristics).most_common(N_agents))
            #print(heuristics_selected)
            descriptives["team_average"] = mean(heuristics_selected.values())
            pairs = permutations(heuristics_selected, 2)
            descriptives["NPdiversity"] = mean([self.assess_hp_diversity(x[0], x[1]) for x in pairs])

            descriptives["Cdiversity"] = len(set([item for sublist in heuristics_selected.keys() for item in sublist]))/l
            agents = [PSAgent(self, id = team_type + str(idx), team = team_type, heuristic=val) for idx, val in enumerate(heuristics_selected)]
            for agent in agents:
                self.schedule.add(agent)
            #print(descriptives["NPdiversity"])    
    
            self.agent_descriptives[team_type] = copy.copy(descriptives)

    def draw_solution(self, n):
        self.solution = [self.random.uniform(0, 100) for i in range(n)]

    #Agent tries to take steps of heuristic length, only moving forward if successful
    #Explained most clearly by Singer
    def max_search(self, agent = None, heuristic = None, start = None,  update = True):
        if heuristic == None: #When agents search
            start = self.current_position[agent.team]
            heuristic = agent.heuristic
            last_value = self.solution[self.current_position[agent.team] % self.n]
        else: #When heuristics are evaluated
            last_value = 0
        current = start
        while True:
            old_value = last_value
            for step in heuristic:
                new_value = self.solution[(current+step) % self.n]
                if  new_value > last_value:
                    last_value = new_value
                    current += step
            if old_value == last_value: #No change on k checks
                break    
        if update:
            self.best_solution[agent.team] = last_value
            self.current_position[agent.team] = current    
        return current, last_value 

    def get_focus(self, agent):
        #Get search to start from known maximum, apart from 
        if(self.best_position == -1):
            return(agent.focus)
        else:
            return(self.best_position)

    def generate_heuristics(self, k,l):
        return permutations(range(1, l + 1), k)

    def evaluate_heuristics(self, heuristics):
        expectations = {}
        for heuristic in heuristics:
            results = list()
            for i in range(self.n):
                results.append(self.max_search(heuristic = heuristic, start = i, update=False)[1])
            expectations[heuristic] = mean(results)
        return expectations     

    def __sample_from_dict(self, d, sample): #From https://stackoverflow.com/a/66018057/10581449
        keys = self.random.sample(list(d), sample)
        values = [d[k] for k in keys]
        return dict(zip(keys, values))

    def assess_hp_diversity(self, heuristic1, heuristic2):
        res = (len(heuristic1)-sum(x == y for x, y in zip(heuristic1, heuristic2)))/len(heuristic1)
        return res

    def step(self):
        old_solution = self.best_solution
        self.schedule.step()
        if old_solution == self.best_solution:
            self.running = False    

