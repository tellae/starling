from starling_sim.basemodel.algorithms.dispatcher import Dispatcher
from starling_sim.basemodel.algorithms.pal_zhang_GCH import PalZhangGCH


class PalZhangGreedyDispatcher(Dispatcher):

    SCHEMA = PalZhangGCH.SCHEMA

    def __init__(self, simulation_model, operator, verb=False):

        super().__init__(simulation_model, operator, verb)

    def init_algorithm(self):

        self.algorithm = PalZhangGCH(
            simulation_model=self.sim, operator=self.operator, verb=self.verb
        )

    def setup_dispatch(self):

        self.algorithm.setup_new_run()

    def run_algorithm(self):

        self.algorithm.run()

    def update_from_solution(self):

        self.log_message("Final planning is {}".format(self.algorithm.planning))
        self.algorithm.vehicle.set_planning(self.algorithm.planning)

    def dispatching_loop_(self):

        for time in self.algorithm.start_times:
            wait_time = time - self.sim.scheduler.now()
            yield self.sim.scheduler.timeout(wait_time)
            self.dispatch()
