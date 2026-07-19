"""
main.py
=======
Network Protocol Performance Analyzer  --  menu-driven entry point.

Performance Engineering Lab [17M15CS122], JIIT Sector 62, Noida
Team:  Abhijeet Kumar (22803029), Viyom Shukla (22803030), Devang Dixit (22803031)

Run:
    python main.py            # interactive menu
    python main.py --demo     # run everything once (great for the viva/demo)

The application ties together the pipeline described in the synopsis:
    Traffic Generation -> Queue Modelling -> Packet Processing ->
    Data Collection -> Performance Evaluation -> Protocol Comparison & Plots.
"""

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


# --------------------------------------------------------------------------- #
def option_mm1():
    lam = _ask_float("  Arrival rate lambda", 8)
    mu = _ask_float("  Service rate  mu", 10)
    t = _ask_int("  Simulation time (s)", 3000)
    df = simulate(lam, mu, c=1, sim_time=t, seed=1)
    print_report(df, "M/M/1 SIMULATION")


def option_mmc():
    lam = _ask_float("  Arrival rate lambda", 15)
    mu = _ask_float("  Service rate  mu", 10)
    c = _ask_int("  Number of servers c", 2)
    t = _ask_int("  Simulation time (s)", 3000)
    df = simulate(lam, mu, c=c, sim_time=t, seed=1)
    print_report(df, "M/M/c SIMULATION")


def option_mmck():
    lam = _ask_float("  Arrival rate lambda", 18)
    mu = _ask_float("  Service rate  mu", 10)
    c = _ask_int("  Number of servers c", 2)
    K = _ask_int("  System capacity K", 5)
    t = _ask_int("  Simulation time (s)", 3000)
    df = simulate(lam, mu, c=c, K=K, sim_time=t, seed=1)
    print_report(df, "M/M/c/K SIMULATION (finite buffer)")


def option_tcp_udp(show=False):
    print("\n  Running TCP vs UDP load sweep (this runs several simulations)...")
    res = compare_protocols(mu=10, c=1, K=10, sim_time=2000)
    summarise(res)
    viz.plot_tcp_vs_udp(res, show=show)


def run_full_demo(show=False):
    print(BANNER)
    print("  >>> RUNNING FULL DEMO — this reproduces every result & graph.\n")

    # 1. Three core queue models, each validated against theory
    print_report(simulate(8, 10, c=1, sim_time=4000, seed=1),
                 "M/M/1  (single server)")
    print_report(simulate(15, 10, c=2, sim_time=4000, seed=1),
                 "M/M/c  (two servers)")
    print_report(simulate(18, 10, c=2, K=6, sim_time=4000, seed=1),
                 "M/M/c/K  (finite buffer)")

    # 2. Graphs
    print("\n  Generating graphs into results/ ...")
    viz.plot_load_sweep(mu=10, c=1, show=show)
    viz.plot_load_sweep(mu=10, c=2, show=show)
    viz.plot_sim_vs_theory(8, 10, c=1, show=show)
    viz.plot_mm1_vs_mmc(show=show)

    # 3. TCP vs UDP
    res = compare_protocols(mu=10, c=1, K=10, sim_time=2000)
    summarise(res)
    viz.plot_tcp_vs_udp(res, show=show)

    print("\n  >>> DEMO COMPLETE.  All graphs saved in the results/ folder.\n")


# --------------------------------------------------------------------------- #
def main():
    if "--demo" in sys.argv:
        run_full_demo(show=False)
        return

    print(BANNER)
    while True:
        print(MENU)
        choice = input("  > ").strip()
        if choice == "1":
            option_mm1()
        elif choice == "2":
            option_mmc()
        elif choice == "3":
            option_mmck()
        elif choice == "4":
            viz.plot_load_sweep(show=True)
        elif choice == "5":
            viz.plot_sim_vs_theory(8, 10, c=1, show=True)
        elif choice == "6":
            viz.plot_mm1_vs_mmc(show=True)
        elif choice == "7":
            option_tcp_udp(show=True)
        elif choice == "8":
            run_full_demo(show=False)
        elif choice == "0":
            print("  Goodbye!")
            break
        else:
            print("  Invalid choice, please try again.")


if __name__ == "__main__":
    main()
