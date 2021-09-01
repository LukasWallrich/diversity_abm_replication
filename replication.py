import random
import pandas as pd
from statistics import mean

from collections import Counter

from itertools import permutations
import pdb



class Agent:
    
    def __init__(self, problem, k = None, l = None, heuristic = None):
        if heuristic == None:
            self.draw_heuristic(k, l)
        else:
            self.heuristic = heuristic    
        self.best_solution = 0
        self.initialise_focus(problem)

    def draw_heuristic(self, problem, k, l):
        self.heuristic = random.sample(range(1,l+1) , k)

    def initialise_focus(self, problem):
        self.focus =  random.randint(0, problem.n - 1)

    def search(self, problem, start):
        self.focus, self.best_solution = problem.max_search(start, self.heuristic)

class Problem:

    def __init__(self, n):
        self.n = n
        self.draw_solution(n)
        self.optimal_solution = max(self.solution)
        self.best_solution = 0
        self.iterations = 0

    def draw_solution(self, n):
        self.solution = [random.uniform(0, 100) for i in range(n)]

    def max_search(self, start, heuristic):
        last_value = self.solution[start % self.n]
        optimum = start
        current = start
        continue_search = True

        while continue_search:
            old_value = last_value
            for current in self.__indices(heuristic, current):
                new_value = self.solution[current % self.n]
                if  new_value > last_value:
                    last_value = new_value
                    optimum = current
            if old_value == last_value: #No change on k checks
                break
        return optimum, last_value 

    def __indices(self, heuristic, current): 
        res = list()
        res.append(current)
        
        for i in range(len(heuristic)):
            res.append(heuristic[i] + res[i])
        return res[1:]   

def generate_heuristics(k,l):
    return permutations(range(1, l + 1), k)

def evaluate_heuristics(heuristics, problem):
    expectations = {}
    for heuristic in heuristics:
        results = list()
        for i in range(problem.n):
            results.append(problem.max_search(i, heuristic)[1])
        expectations[heuristic] = mean(results)
    return expectations     

def draw_teams(problem, k, l, N_agents, method):
    heuristics = evaluate_heuristics(generate_heuristics(k, l), problem)
    descriptives = {
        "worst_agent": min(heuristics.values()),
        "average_agent": mean(heuristics.values()),
        "best_agent": max(heuristics.values())
    }
    if method == "random" or method == "both":
        heuristics_random = sample_from_dict(heuristics, N_agents)
        descriptives["random_average"] = mean(heuristics_random.values())
        pairs = permutations(heuristics_random, 2)
        descriptives["random_diversity"] = mean([assess_diversity(x[0], x[1]) for x in pairs])
        agents_random = [Agent(problem, heuristic=x) for x in heuristics_random]
    if method == "best" or method == "both":
        heuristics_best = dict(Counter(heuristics).most_common(N_agents))
        descriptives["best_average"] = mean(heuristics_best.values())
        pairs = permutations(heuristics_best, 2)
        descriptives["best_diversity"] = mean([assess_diversity(x[0], x[1]) for x in pairs])
        agents_best = [Agent(problem, heuristic=x) for x in heuristics_best]
    if method == "both":
        return descriptives, agents_random, agents_best
    if method == "random":
        return descriptives, agents_random
    if method == "best":
        return descriptives, agents_best               

def sample_from_dict(d, sample): #From https://stackoverflow.com/a/66018057/10581449
    keys = random.sample(list(d), sample)
    values = [d[k] for k in keys]
    return dict(zip(keys, values))

def assess_diversity(heuristic1, heuristic2):
    res = (len(heuristic1)-sum(x == y for x, y in zip(heuristic1, heuristic2)))/len(heuristic1)
    return res

### Range of heuristic performance scores much narrower than in paper

# == Main == #
n = 2000    # Length of problem
k = 3        # No of positions to consider
l = 12         # Max lookahead

N_agents = 10    

runs = 10

current_problem = 0

problems = list()
problems.append(Problem(n))

descriptives = list()

for i in range(runs):
    print("Starting iteration ", i)
    #Create teams of best and random agents
    x, agents_random, agents_best = draw_teams(problems[i], k, l, N_agents, method = "both")
    descriptives.append(x)

    # Search with both teams
    for agents, agent_type in zip([agents_random, agents_best], ["random", "best"]):

        #Initialise shared knowledge
        current_max = 0
        current_opt_position = -1
        current_iter = 0

        while True:
            prev_max = current_max 
            for agent in agents:
                if current_opt_position >= 0:
                    agent.focus = current_opt_position  
                agent.search(problems[i], agent.focus)
                current_opt_position = agent.focus 
                current_max = agent.best_solution
                current_iter += 1
            if current_max == prev_max:
                problems[i].best_solution = current_max
                problems[i].iterations = current_iter
                break
        descriptives[i]["solution_" + agent_type] = problems[i].best_solution
        descriptives[i]["iterations_" + agent_type] = problems[i].iterations
                    
    problems.append(Problem(n))        
            
print(pd.DataFrame(descriptives))


