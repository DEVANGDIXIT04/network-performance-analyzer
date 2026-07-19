"""Menu-driven entry point.  Run `python main.py` or `python main.py --demo`."""

import sys

from src.queue_models import simulate
from src.metrics import print_report
from src import visualization as viz
from src.protocol_comparison import compare_protocols, summarise


BANNER = r"""
+------------------------------------------------------------------+
|          NETWORK PROTOCOL PERFORMANCE ANALYZER                    |
|          Queuing-Theory based Simulation  (SimPy)                 |
|          Performance Engineering Lab - JIIT Sector 62            |
+------------------------------------------------------------------+
"""

MENU = """
  Choose an option:
   1. Simulate M/M/1  (single server)              + validate vs theory
   2. Simulate M/M/c  (multiple servers)           + validate vs theory
   3. Simulate M/M/c/K (finite buffer / loss)      + validate vs theory
   4. Load sweep graph (delay & throughput vs rho)
   5. Simulation-vs-Theory bar chart
   6. M/M/1 vs M/M/c comparison graph
   7. TCP vs UDP comparison (table + graph)
   8. RUN FULL DEMO  (everything, saves all graphs)
   0. Exit
"""


def _ask_float(prompt, default):
    raw = input(f"{prompt} [{default}]: ").strip()
    return float(raw) if raw else default


def _ask_int(prompt, default):
    raw = input(f"{prompt} [{default}]: ").strip()
    return int(raw) if raw else default


def option_mm1():
    lam = _ask_float("  Arrival rate lambda", 8)
    mu = _ask_float("  Service rate  mu", 10)
    t = _ask_int("  Simulation time (s)", 3000)
    print_report(simulate(lam, mu, c=1, sim_time=t, seed=1), "M/M/1 SIMULATION")


def option_mmc():
    lam = _ask_float("  Arrival rate lambda", 15)
    mu = _ask_float("  Service rate  mu", 10)
    c = _ask_int("  Number of servers c", 2)
    t = _ask_int("  Simulation time (s)", 3000)
    print_report(simulate(lam, mu, c=c, sim_time=t, seed=1), "M/M/c SIMULATION")


def option_mmck():
    lam = _ask_float("  Arrival rate lambda", 18)
    mu = _ask_float("  Service rate  mu", 10)
    c = _ask_int("  Number of servers c", 2)
    K = _ask_int("  System capacity K", 5)
    t = _ask_int("  Simulation time (s)", 3000)
    print_report(simulate(lam, mu, c=c, K=K, sim_time=t, seed=1),
                 "M/M/c/K SIMULATION (finite buffer)")


def option_tcp_udp(show=False):
    print("\n  Running TCP vs UDP load sweep (several simulations)...")
    res = compare_protocols(mu=10, c=1, K=10, sim_time=2000)
    summarise(res)
    viz.plot_tcp_vs_udp(res, show=show)


def run_full_demo(show=False):
    print(BANNER)
    print("  >>> RUNNING FULL DEMO — reproduces every result & graph.\n")

    print_report(simulate(8, 10, c=1, sim_time=4000, seed=1), "M/M/1  (single server)")
    print_report(simulate(15, 10, c=2, sim_time=4000, seed=1), "M/M/c  (two servers)")
    print_report(simulate(18, 10, c=2, K=6, sim_time=4000, seed=1), "M/M/c/K  (finite buffer)")

    print("\n  Generating graphs into results/ ...")
    viz.plot_load_sweep(mu=10, c=1, show=show)
    viz.plot_load_sweep(mu=10, c=2, show=show)
    viz.plot_sim_vs_theory(8, 10, c=1, show=show)
    viz.plot_mm1_vs_mmc(show=show)

    res = compare_protocols(mu=10, c=1, K=10, sim_time=2000)
    summarise(res)
    viz.plot_tcp_vs_udp(res, show=show)
    print("\n  >>> DEMO COMPLETE.  All graphs saved in results/.\n")


def main():
    if "--demo" in sys.argv:
        run_full_demo(show=False)
        return

    print(BANNER)
    actions = {
        "1": option_mm1, "2": option_mmc, "3": option_mmck,
        "4": lambda: viz.plot_load_sweep(show=True),
        "5": lambda: viz.plot_sim_vs_theory(8, 10, c=1, show=True),
        "6": lambda: viz.plot_mm1_vs_mmc(show=True),
        "7": lambda: option_tcp_udp(show=True),
        "8": lambda: run_full_demo(show=False),
    }
    while True:
        print(MENU)
        choice = input("  > ").strip()
        if choice == "0":
            print("  Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("  Invalid choice, please try again.")


if __name__ == "__main__":
    main()
