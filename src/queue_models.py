"""SimPy discrete-event simulator for M/M/1, M/M/c and M/M/c/K queues."""

import simpy
import pandas as pd

from .traffic_generator import TrafficGenerator


class Packet:
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
    def __init__(self, lam, mu, c=1, K=None, sim_time=2000, seed=None):
        self.lam = lam
        self.mu = mu
        self.c = c
        self.K = K
        self.sim_time = sim_time
        self.gen = TrafficGenerator(lam, mu, seed=seed)
        self.env = simpy.Environment()
        self.server = simpy.Resource(self.env, capacity=c)
        self.packets = []
        self.in_system = 0
        self.busy_time = 0.0

    def _serve(self, packet):
        # queue -> service -> depart
        with self.server.request() as req:
            yield req
            packet.start_service = self.env.now
            service = self.gen.next_service_time()
            self.busy_time += service
            yield self.env.timeout(service)
            packet.departure = self.env.now
        self.in_system -= 1

    def _arrivals(self):
        # Poisson arrivals; drop when the system is full (finite K)
        pid = 0
        while True:
            yield self.env.timeout(self.gen.next_interarrival())
            pid += 1
            packet = Packet(pid, self.env.now)
            self.packets.append(packet)
            if self.K is not None and self.in_system >= self.K:
                packet.dropped = True
                continue
            self.in_system += 1
            self.env.process(self._serve(packet))

    def run(self):
        self.env.process(self._arrivals())
        self.env.run(until=self.sim_time)

        df = pd.DataFrame([{
            "pid": p.pid,
            "arrival": p.arrival,
            "start_service": p.start_service,
            "departure": p.departure,
            "waiting_time": p.waiting_time,
            "sojourn_time": p.sojourn_time,
            "dropped": p.dropped,
            "served": (not p.dropped) and (p.departure is not None),
        } for p in self.packets])
        df.attrs.update(sim_time=self.sim_time, busy_time=self.busy_time,
                        c=self.c, lam=self.lam, mu=self.mu, K=self.K)
        return df


def simulate(lam, mu, c=1, K=None, sim_time=2000, seed=42):
    return QueueSimulator(lam, mu, c, K, sim_time, seed).run()


if __name__ == "__main__":
    df = simulate(lam=8, mu=10, c=1, sim_time=2000, seed=1)
    print(df.head())
    print("Total packets:", len(df), "| served:", int(df["served"].sum()))
