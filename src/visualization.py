"""
visualization.py
----------------
All Matplotlib plotting for the analyzer.  Every function saves a PNG into the
results/ folder and (optionally) shows it on screen.

Graphs produced:
    1. load_sweep        -- delay / throughput / loss vs traffic intensity,
                            simulation points overlaid on theory curves
    2. sim_vs_theory_bar -- bar chart validating one scenario against theory
    3. mm1_vs_mmc        -- effect of adding servers (M/M/1 vs M/M/c)
    4. tcp_vs_udp        -- goodput, delay and loss of TCP vs UDP under load
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")            # safe on headless machines; still saves PNGs
import matplotlib.pyplot as plt

from . import theoretical
from .queue_models import simulate
from .metrics import compute_metrics, compare_with_theory


RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"
)
os.makedirs(RESULTS_DIR, exist_ok=True)


def _save(fig, name, show):
    path = os.path.join(RESULTS_DIR, name)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    print(f"  [saved] {path}")
    if show:
        plt.show()
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
def plot_load_sweep(mu=10, c=1, sim_time=3000, seed=7, show=False):
    """
    Vary lambda so that rho goes from light to heavy load and plot how
    delay, throughput and packet-loss behave.  Simulation markers are drawn on
    top of the theoretical curves to show they agree.
    """
    rhos = np.linspace(0.1, 0.95, 10)
    lams = rhos * c * mu

    sim_delay, sim_thr = [], []
    th_delay, th_thr = [], []

    for lam in lams:
        df = simulate(lam, mu, c=c, sim_time=sim_time, seed=seed)
        m = compute_metrics(df)
        sim_delay.append(m["avg_delay"])
        sim_thr.append(m["throughput"])

        t = theoretical.analyse(lam, mu, c=c)
        th_delay.append(t["W"])
        th_thr.append(t["throughput"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    model = f"M/M/{c}"

    ax1.plot(rhos, th_delay, "b-", label="Theory  W")
    ax1.plot(rhos, sim_delay, "ro", label="Simulation")
    ax1.set_xlabel("Traffic intensity  rho = lambda/(c*mu)")
    ax1.set_ylabel("Average delay  W  (s)")
    ax1.set_title(f"Average Delay vs Load  ({model})")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.plot(rhos, th_thr, "g-", label="Theory")
    ax2.plot(rhos, sim_thr, "ks", label="Simulation")
    ax2.set_xlabel("Traffic intensity  rho")
    ax2.set_ylabel("Throughput  (packets/s)")
    ax2.set_title(f"Throughput vs Load  ({model})")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    fig.suptitle("Load Sweep: Simulation validated against Queuing Theory",
                 fontsize=13, fontweight="bold")
    return _save(fig, f"load_sweep_mm{c}.png", show)


# --------------------------------------------------------------------------- #
def plot_sim_vs_theory(lam, mu, c=1, K=None, sim_time=4000, seed=3, show=False):
    """Bar chart comparing simulated vs theoretical metrics for one scenario."""
    df = simulate(lam, mu, c=c, K=K, sim_time=sim_time, seed=seed)
    table = compare_with_theory(df)

    # Pick the interpretable rate/time/number metrics for the bars
    keep = table[table["Metric"].isin(
        ["Utilisation (rho)", "Avg delay  W (s)", "Avg wait   Wq (s)",
         "Number in system L"])]

    labels = keep["Metric"].tolist()
    sim_vals = keep["Simulation"].tolist()
    th_vals = keep["Theory"].tolist()

    x = np.arange(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w / 2, sim_vals, w, label="Simulation", color="#4C72B0")
    ax.bar(x + w / 2, th_vals, w, label="Theory", color="#DD8452")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylabel("Value")
    model = f"M/M/{c}" + (f"/{K}" if K is not None else "")
    ax.set_title(f"Simulation vs Theory  ({model},  lambda={lam}, mu={mu})")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    return _save(fig, f"sim_vs_theory_mm{c}.png", show)


# --------------------------------------------------------------------------- #
def plot_mm1_vs_mmc(mu=10, servers=(1, 2, 3), sim_time=3000, seed=11, show=False):
    """
    Show the benefit of parallel servers: keep per-server load rho fixed and
    compare average delay of M/M/1, M/M/2, M/M/3 ...
    """
    rhos = np.linspace(0.1, 0.9, 9)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = ["#C44E52", "#4C72B0", "#55A868", "#8172B3"]

    for i, c in enumerate(servers):
        delays = []
        for rho in rhos:
            lam = rho * c * mu
            t = theoretical.analyse(lam, mu, c=c)
            delays.append(t["W"])
        ax.plot(rhos, delays, "o-", color=colors[i % len(colors)],
                label=f"M/M/{c}")

    ax.set_xlabel("Traffic intensity  rho")
    ax.set_ylabel("Average delay  W  (s)")
    ax.set_title("Effect of Adding Servers:  M/M/1 vs M/M/c")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return _save(fig, "mm1_vs_mmc.png", show)


# --------------------------------------------------------------------------- #
def plot_tcp_vs_udp(result, show=False):
    """Plot TCP-vs-UDP goodput, delay and loss from protocol_comparison."""
    rho = result["offered_rho"]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.5))

    ax1.plot(rho, result["tcp_goodput"], "b-o", label="TCP")
    ax1.plot(rho, result["udp_goodput"], "r-s", label="UDP")
    ax1.axhline(result.attrs["capacity"], color="gray", ls="--",
                label="Link capacity")
    ax1.set_xlabel("Offered load  rho")
    ax1.set_ylabel("Goodput  (packets/s)")
    ax1.set_title("Goodput vs Load")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.plot(rho, result["tcp_delay"], "b-o", label="TCP")
    ax2.plot(rho, result["udp_delay"], "r-s", label="UDP")
    ax2.set_xlabel("Offered load  rho")
    ax2.set_ylabel("Average delay  (s)")
    ax2.set_title("Delay vs Load")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    ax3.plot(rho, result["tcp_loss"] * 100, "b-o", label="TCP")
    ax3.plot(rho, result["udp_loss"] * 100, "r-s", label="UDP")
    ax3.set_xlabel("Offered load  rho")
    ax3.set_ylabel("Packet loss  (%)")
    ax3.set_title("Packet Loss vs Load")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    fig.suptitle("TCP vs UDP under Increasing Network Load",
                 fontsize=13, fontweight="bold")
    return _save(fig, "tcp_vs_udp.png", show)


if __name__ == "__main__":
    plot_load_sweep()
    plot_sim_vs_theory(8, 10, c=1)
    plot_mm1_vs_mmc()
