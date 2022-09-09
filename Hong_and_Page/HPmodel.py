# ABM as proposed by Hong & Page (2004)

from statistics import mean
from collections import Counter
from itertools import permutations
from mesa import Agent, Model
from mesa.time import BaseScheduler
from copy import copy


class PSAgent(Agent):

    """Agent for Hong-Page problem-solving model.

    This mesa-agent forms part of a team that searches for the optimal solution in the HPProblem model.

    Attributes:
        heuristic: List of step lengths this agent can consider.
        team: Team this agent belongs to. Either "random" or "best" in standard HPProblem.
        best_solution: Best solution found by this agent so far.

    Methods:
        step: Advance by one step - called by mesa.
    """

    def __init__(
        self,
        problem: "HPProblem",
        agent_id: str,
        team: str,
        k: int = None,
        l: int = None,
        heuristic: list = None,
    ):
        """Initializes agent, assigns heuristic and team

        This initializes an agent to solve a given problem, assigns them a heuristic and a team. The heuristic can
        either be given as a list of step lengths, or by specifying k (number of different step lengths) and l (maximum step length).

        Args:
            problem (HPProblem): Problem to solve
            id (str): Agent ID
            team (str): Name of the team
            k (int): Number of different step lengths to consider (e.g., 3 per agent)
            l (int): Maximum step length to consider (e.g., 10)
            heuristic (list): Alternative to k and l, the specific heuristic can be given
        """
        super().__init__(agent_id, problem)

        if heuristic is None:
            self.__draw_heuristic(k, l)
        else:
            self.heuristic = heuristic

        self.best_solution = 0
        self.problem = problem
        self.team = team

    def __draw_heuristic(self, problem: "HPProblem", k: int, l: int):
        """Draw heuristic as k random integers up to l"""
        self.heuristic = problem.random.sample(range(1, l + 1), k)

    def step(self):
        """Search for highest peak accessible with own heuristic (called by mesa)"""
        self.focus, self.best_solution = self.problem.max_search(agent=self)


class HPProblem(Model):

    """Hong-Page problem-solving model to assess performance of different teams.

    This mesa-based agent-based model in an implementation of Hong & Page (2004),
    in which agents are assigned to teams that strive to find the maximum value
    in a random landscape.

    Attributes:
        solution: List of numbers representing 'heights' in the landscape.
        agent_descriptives: Dict with descriptive statistics for agents in each team (i.e. random and best).
        best_solution: Dict with best solution found by each team so far.

    Methods:
        max_search: Evaluate a heuristic across all starting points, or have an agent search from their current location.
        draw_agents: Generate teams of agents (random and best)
        draw_solution: Create solution (random landscape) that agents search
        generate_heuristics: Create heuristics (set of step sizes to be considered)
        evaluate_heuristics: Calculate average score achieved by a given heuristic
        assess_hp_diversity: Calculate diversity between two heuristics as defined by Hong & Page
        step: Advance model by one step.
    """

    def __init__(
        self,
        n: int,
        k: int,
        l: int,
        N_agents: int,
        seed: int = None,
        agent_class: Agent = PSAgent,
    ):
        """Initializes problem, assesses heuristics and creates agent teams

        Initializes Hong & Page model by drawing the solution landscape, assessing the performance of all heuristics,
        and creating best and random agent teams.

        Args:
            n: Length of solution landscape
            k: Number of steps to include in each heuristic
            l: Maximum step size to be considered when drawing heuristics
            N_agents: Number of agents in each team
            seed: Random seed for reproducibility
        """
        # Seed automatically set by mesa if provided
        self.schedule = BaseScheduler(self)
        self.agent_descriptives = {}
        self.n = n
        self.draw_solution(n)
        self.optimal_solution = max(self.solution)
        self.best_solution = {"random": 0, "best": 0}
        self.current_position = {"random": 0, "best": 0}
        self.draw_agents(k, l, N_agents, agent_class)
        self.running = True

    def draw_agents(self, k: int, l: int, N_agents: int, agent_class: Agent) -> None:
        """Generates both random and best agent teams

        To generate the team of 'best' agents, all possible heuristics are evaluated across all starting points.
        Then the N_agents best-performing heuristics are used to create the team.

        To create the random team, N_agents random heuristics are generated and used to initialise the agents.

        Args:
            k: Number of steps to include in each heuristic
            l: Maximum step size to be considered when drawing heuristics
            N_agents: Number of agents in each team
            agent_class: Class of agent to be used
        """

        heuristics = self.evaluate_heuristics(self.generate_heuristics(k, l))

        descriptives = {
            "worst_agent": min(heuristics.values()),
            "average_agent": mean(heuristics.values()),
            "top_agent": max(heuristics.values()),
        }

        # Draw "random" team based on randomly selected heuristics, and best team based on highest-performing heuristics
        for team_type in ["random", "best"]:
            if team_type == "random":
                heuristics_selected = self.__sample_from_dict(heuristics, N_agents)
            if team_type == "best":
                heuristics_selected = dict(Counter(heuristics).most_common(N_agents))
            descriptives["team_average"] = mean(heuristics_selected.values())
            pairs = permutations(heuristics_selected, 2)
            descriptives["NPdiversity"] = mean(
                [self.assess_hp_diversity(x[0], x[1]) for x in pairs]
            )

            # Initialise agents and add them to the scheduler

            agents = [
                agent_class(
                    self, agent_id=team_type + str(idx), team=team_type, heuristic=val
                )
                for idx, val in enumerate(heuristics_selected)
            ]

            for agent in agents:
                self.schedule.add(agent)

            self.agent_descriptives[team_type] = copy(descriptives)

    def draw_solution(self, n: int) -> None:
        """Generate solution landscape: n random numbers up to 100"""
        self.solution = [self.random.uniform(0, 100) for i in range(n)]

    def max_search(
        self, agent: Agent = None, heuristic: list = None, update: bool = True
    ) -> tuple:
        """Either evaluates a heuristic across all starting points, or has an agent search from their current location

        If an agent is provided, the agent will search from their current location, trying out each step size in their heuristic in turn until
        they cannot reach a higher value. If a heuristic is provided, the heuristic will be evaluated across all starting points. `update` determines
        whether the team's current position (and best_solution) should be updated.

        Returns: A tuple (best_solution, current_position) that represents the best solution found and the current position of the agent
          (NB: when a heuristic is evaluated, the latter is meaningless).
        """
        N = self.n  # To speed things up
        SOLUTION = self.solution

        if heuristic is None:  # When agents search, start from their current location
            start = [self.current_position[agent.team]]
            heuristic = agent.heuristic
        else:  # When heuristics are evaluated, search should start from each location in turn
            start = range(N)

        optima = []

        # Search for highest peak accessible with heuristic
        for current in start:
            last_value = SOLUTION[current % N]  # Turn landscape into a ring

            while (True):  
            # Take steps using heuristic unless there are no further improvements
                old_value = last_value
                for step in heuristic:
                    new_value = SOLUTION[(current + step) % N]
                    if new_value > last_value:
                        last_value = new_value
                        current += step
                if old_value == last_value:  # No change on k checks
                    optima.append(last_value)
                    break

        if update:  # Should only be used when agents search
            self.best_solution[agent.team] = optima[0]
            self.current_position[agent.team] = current

        return current, mean(optima)

    def generate_heuristics(self, k: int, l: int) -> list:
        """Generates all possible heuristics"""
        return permutations(range(1, l + 1), k)

    def evaluate_heuristics(self, heuristics: list) -> dict:
        """Calculates 'ability' score for each heuristic - the mean result from each starting point

        Returns: Dict with heuristics as keys and their average score as value
        """
        expectations = {}
        for heuristic in heuristics:
            expectations[heuristic] = self.max_search(
                heuristic=heuristic, update=False
            )[1]
        return expectations

    def __sample_from_dict(self, d: dict, n: int):  
        # From https://stackoverflow.com/a/66018057/10581449
        """Return n random objects from d"""
        keys = self.random.sample(list(d), n)
        values = [d[k] for k in keys]
        return dict(zip(keys, values))

    def assess_hp_diversity(self, heuristic1: list, heuristic2: list) -> float:
        """Calculates diversity between two heuristics as defined by Hong & Page

        Diversity here is defined as the share of positions in which the two heuristics differ.
        For instance (1,2,3) and (1,3,4) would have a diversity of 67% since they overlap in the first position only.
        """
        res = (
            len(heuristic1) - sum(x == y for x, y in zip(heuristic1, heuristic2))
        ) / len(heuristic1)
        return res

    def __dict_mean(self, dict_list: list) -> dict:
        """Calculates the mean of values in a list of dictionaries, grouped by each key"""
        # Thanks to https://stackoverflow.com/a/55220333/10581449
        mean_dict = {}
        for key in dict_list[0].keys():
            mean_dict[key] = sum(d[key] for d in dict_list) / len(dict_list)
        return mean_dict

    def step(self) -> None:
        """Has agent teams search for solution

        This runs the simulation, going through each starting point in the landscape and getting agent teams to search for the best solution they can achieve.
        At the end, the best_solution attribute is updated with the average performance of each team.
        """
        solutions = list()
        for i in range(self.n):
            self.current_position = dict.fromkeys(self.current_position, i)
            while True:
                old_solution = self.best_solution
                self.schedule.step()
                if old_solution == self.best_solution:
                    solutions.append(copy(self.best_solution))
                    break
        self.best_solution = self.__dict_mean(solutions)
        self.running = False
