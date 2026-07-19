"""Poisson traffic: exponential inter-arrival and service times."""

import numpy as np


class TrafficGenerator:
    def __init__(self, lam, mu, seed=None):
        self.lam = lam
        self.mu = mu
        self.rng = np.random.default_rng(seed)

    def next_interarrival(self):
        # Time until next arrival ~ Exp(lambda)
        return self.rng.exponential(1.0 / self.lam)

    def next_service_time(self):
        # Service time ~ Exp(mu)
        return self.rng.exponential(1.0 / self.mu)

    def arrival_times(self, n):
        return np.cumsum(self.rng.exponential(1.0 / self.lam, size=n))


if __name__ == "__main__":
    gen = TrafficGenerator(lam=5, mu=10, seed=42)
    print("Inter-arrivals:", [round(gen.next_interarrival(), 4) for _ in range(5)])
    print("Service times :", [round(gen.next_service_time(), 4) for _ in range(5)])
