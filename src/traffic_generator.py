"""
traffic_generator.py
--------------------
Generates network traffic as a Poisson arrival process.

In a Poisson process with rate lambda, the time BETWEEN consecutive
arrivals (the inter-arrival time) is exponentially distributed with
mean 1/lambda.  This is the standard model for bursty, memoryless
network packet arrivals and is the 'M' (Markovian) in M/M/1, M/M/c ...
"""

import numpy as np


class TrafficGenerator:
    """Produces exponential inter-arrival and service times."""

    def __init__(self, lam, mu, seed=None):
        self.lam = lam                       # arrival rate  (packets/sec)
        self.mu = mu                         # service rate  (packets/sec/server)
        self.rng = np.random.default_rng(seed)

    def next_interarrival(self):
        """Time until the next packet arrives  ~ Exp(lambda)."""
        return self.rng.exponential(1.0 / self.lam)

    def next_service_time(self):
        """Service (processing) time for a packet  ~ Exp(mu)."""
        return self.rng.exponential(1.0 / self.mu)

    def arrival_times(self, n):
        """Return absolute arrival times for the first n packets."""
        gaps = self.rng.exponential(1.0 / self.lam, size=n)
        return np.cumsum(gaps)


if __name__ == "__main__":
    gen = TrafficGenerator(lam=5, mu=10, seed=42)
    print("Sample inter-arrival times:",
          [round(gen.next_interarrival(), 4) for _ in range(5)])
    print("Sample service times     :",
          [round(gen.next_service_time(), 4) for _ in range(5)])
