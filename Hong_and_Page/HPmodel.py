# ABM as proposed by Hong & Page (2004)

#%%
from statistics import mean
from collections import Counter
from itertools import permutations
from mesa import Agent, Model
from mesa.time import BaseScheduler, RandomActivation
import copy
import time

#%%
class PSAgent(Agent):
    
    def __init__(self, problem, id, team, k = None, l = None, heuristic = None):
        super().__init__(id, problem)

        if heuristic == None:
            self.draw_heuristic(k, l)
        else:
            self.heuristic = heuristic    

        self.best_solution = 0
        self.focus = 0 #Start search at beginning
        self.problem = problem
        self.team = team

    def draw_heuristic(self, problem, k, l):
        self.heuristic = problem.random.sample(range(1,l+1) , k)

    def step(self):
#        print("Agent starting from " + str(self.problem.current_position))
        self.focus, self.best_solution = self.problem.max_search(agent = self)

class HPProblem(Model):

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
        self.current_position = {"random": 0, "best": 0}
        self.draw_agents(k, l, N_agents)
        self.running = True

    def draw_agents(self, k, l, N_agents):
        heuristics = self.evaluate_heuristics(self.generate_heuristics(k, l))

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

            descriptives["team_average"] = mean(heuristics_selected.values())
            pairs = permutations(heuristics_selected, 2)
            descriptives["NPdiversity"] = mean([self.assess_hp_diversity(x[0], x[1]) for x in pairs])

            agents = [PSAgent(self, id = team_type + str(idx), team = team_type, heuristic=val) for idx, val in enumerate(heuristics_selected)]

            for agent in agents:
                self.schedule.add(agent)
    
            self.agent_descriptives[team_type] = copy.copy(descriptives)

    def draw_solution(self, n):
        self.solution = [self.random.uniform(0, 100) for i in range(n)]

    #Agent tries to take steps of heuristic length, only moving forward if successful
    #Explained most clearly by Singer
    def max_search(self, agent = None, heuristic = None, update = True):

        N = self.n #To speed things up
        SOLUTION = self.solution

        if heuristic == None: #When agents search
            start = [self.current_position[agent.team]]
            heuristic = agent.heuristic
        else: #When heuristics are evaluated
            start = range(N)

        optima = []

        for current in start:
            last_value = SOLUTION[current % N]

            while True:
                old_value = last_value
                for step in heuristic:
                    new_value = SOLUTION[(current+step) % N]
                    if  new_value > last_value:
                        last_value = new_value
                        current += step
                if old_value == last_value: #No change on k checks
                    optima.append(last_value)
                    break 

        if update: #Should only be used when agents search
            self.best_solution[agent.team] = optima.pop()
            self.current_position[agent.team] = start    

        return current, mean(optima) 

    def generate_heuristics(self, k,l):
        return permutations(range(1, l + 1), k)

    def evaluate_heuristics(self, heuristics):
        expectations = {}
        for heuristic in heuristics:
            expectations[heuristic] = self.max_search(heuristic = heuristic, update=False)[1]
        return expectations     

    def __sample_from_dict(self, d, sample): #From https://stackoverflow.com/a/66018057/10581449
        keys = self.random.sample(list(d), sample)
        values = [d[k] for k in keys]
        return dict(zip(keys, values))

    def assess_hp_diversity(self, heuristic1, heuristic2):
        res = (len(heuristic1)-sum(x == y for x, y in zip(heuristic1, heuristic2)))/len(heuristic1)
        return res

    def dict_mean(self, dict_list):
        #Thanks to https://stackoverflow.com/a/55220333/10581449
        mean_dict = {}
        for key in dict_list[0].keys():
            mean_dict[key] = sum(d[key] for d in dict_list) / len(dict_list)
        return mean_dict

    def step(self):
        solutions = list()
        for i in range(self.n):
            self.current_position = dict.fromkeys(self.current_position, i)
#            print("Assessing start from" + str(i))
            old_solution = self.best_solution
            while True:
               self.schedule.step()
               if old_solution == self.best_solution:
                solutions.append(copy.copy(self.best_solution))
                break
        self.best_solution = self.dict_mean(solutions)
        self.running = False    

