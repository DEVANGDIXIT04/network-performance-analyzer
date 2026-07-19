"""
queue_models.py
---------------
Discrete-event simulation of packet queues using SimPy.

A single, general simulator handles all three models:
    * M/M/1     -> c = 1, K = None (infinite buffer)
    * M/M/c     -> c > 1, K = None (infinite buffer)
    * M/M/c/K   -> K given          (finite buffer -> packet loss)

The server pool is a simpy.Resource with capacity c.  Packets arrive as a
Poisson process; each packet is either admitted (and later served) or, if the
system already holds K packets, dropped to model buffer overflow.

Per-packet statistics are recorded so that metrics.py can compute throughput,
delay, packet loss and utilisation, and compare them against theoretical.py.
"""

import simpy
import pandas as pd

from .traffic_generator import TrafficGenerator


class Packet:
    """A single network packet flowing through the system."""
    __slots__ = ("pid", "arrival", "start_service", "departure", "dropped")

    def __init__(self, pid, arrival):
        self.pid = pid
        self.arrival = arrival
        self.start_service = None
        self.departure = None
        self.dropped = False

    @property
    def waiting_time(self):
        if self.dropped or self.start_service is None:
            return None
        return self.start_service - self.arrival

    @property
    def sojourn_time(self):
        if self.dropped or self.departure is None:
            return None
        return self.departure - self.arrival


class QueueSimulator:
    """
    Discrete-event M/M/c/K queue simulator.

    Parameters
    ----------
    lam, mu : arrival and per-server service rates
    c       : number of parallel servers
    K       : system capacity (None = infinite buffer)
    sim_time: total simulated seconds
    seed    : RNG seed for reproducibility
    """

    def __init__(self, lam, mu, c=1, K=None, sim_time=2000, seed=None):
        self.lam = lam
        self.mu = mu
        self.c = c
        self.K = K
        self.sim_time = sim_time
        self.seed = seed

        self.gen = TrafficGenerator(lam, mu, seed=seed)
        self.env = simpy.Environment()
        self.server = simpy.Resource(self.env, capacity=c)

        self.packets = []          # every packet that ARRIVED
        self.in_system = 0         # current number in system (service + queue)
        self.busy_time = 0.0       # integral of (#busy servers) dt -> utilisation

    # ----------------------------------------------------------------- #
    def _serve(self, packet):
        """Process one admitted packet: queue -> service -> depart."""
        with self.server.request() as req:
            yield req
            packet.start_service = self.env.now
            service = self.gen.next_service_time()
            self.busy_time += service          # one server busy for 'service' secs
            yield self.env.timeout(service)
            packet.departure = self.env.now
        self.in_system -= 1

    def _arrivals(self):
        """Poisson arrival process; drops packets when the system is full."""
        pid = 0
        while True:
            yield self.env.timeout(self.gen.next_interarrival())
            pid += 1
            packet = Packet(pid, self.env.now)
            self.packets.append(packet)

            # Finite capacity -> drop if system already holds K packets
            if self.K is not None and self.in_system >= self.K:
                packet.dropped = True
                continue

            self.in_system += 1
            self.env.process(self._serve(packet))

    # ----------------------------------------------------------------- #
    def run(self):
        """Run the simulation and return a per-packet pandas DataFrame."""
        self.env.process(self._arrivals())
        self.env.run(until=self.sim_time)

        rows = []
        for p in self.packets:
            rows.append({
                "pid": p.pid,
                "arrival": p.arrival,
                "start_service": p.start_service,
                "departure": p.departure,
                "waiting_time": p.waiting_time,
                "sojourn_time": p.sojourn_time,
                "dropped": p.dropped,
                "served": (not p.dropped) and (p.departure is not None),
            })
        df = pd.DataFrame(rows)
        df.attrs["sim_time"] = self.sim_time
        df.attrs["busy_time"] = self.busy_time
        df.attrs["c"] = self.c
        df.attrs["lam"] = self.lam
        df.attrs["mu"] = self.mu
        df.attrs["K"] = self.K
        return df


def simulate(lam, mu, c=1, K=None, sim_time=2000, seed=42):
    """Convenience wrapper -> returns the per-packet DataFrame."""
    return QueueSimulator(lam, mu, c, K, sim_time, seed).run()


if __name__ == "__main__":
    df = simulate(lam=8, mu=10, c=1, sim_time=2000, seed=1)
    print(df.head())
    print("Total packets:", len(df), "| served:", int(df["served"].sum()))
