"""
protocol_comparison.py
----------------------
Compares the transport-layer behaviour of TCP and UDP under increasing load,
built on top of the same finite-capacity (M/M/c/K) queue simulation.

Behavioural model (deliberately simplified, but textbook-consistent):

UDP  -- lightweight, best-effort, NO retransmission and NO congestion control.
        * Dropped packets are simply LOST (they are never recovered).
        * Goodput = accepted-and-served rate; it rises with load, then FALLS
          once the buffer starts overflowing badly.
        * Delay stays comparatively low because lost packets never wait.

TCP  -- reliable, congestion-controlled.
        * Lost packets are RETRANSMITTED, so effective data loss -> ~0.
        * Congestion control keeps the offered load from exceeding capacity,
          so goodput SATURATES near the link capacity (c * mu) instead of
          collapsing.
        * The price of reliability is DELAY: retransmissions and queueing make
          the average delivery time grow sharply as load increases.

For each offered load lambda we run one finite-buffer simulation and derive the
TCP and UDP curves from its measured throughput / loss / delay.
"""

import numpy as np
import pandas as pd

from .queue_models import simulate
from .metrics import compute_metrics


def compare_protocols(mu=10, c=1, K=10, loads=None, sim_time=2000, seed=42):
    """
    Sweep a range of arrival rates (lambda) and return a DataFrame with the
    TCP and UDP throughput, delay and loss at each load.
    """
    capacity = c * mu                      # maximum service capacity
    if loads is None:
        # sweep offered load from light (0.2) to heavy (1.6) x capacity
        loads = np.round(np.linspace(0.2, 1.6, 12) * capacity, 2)

    rows = []
    for lam in loads:
        df = simulate(lam, mu, c=c, K=K, sim_time=sim_time, seed=seed)
        m = compute_metrics(df)

        served_rate = m["throughput"]          # packets actually served / sec
        loss = m["packet_loss"]
        delay = m["avg_delay"]

        # ---- UDP: best-effort, no recovery ---------------------------------
        udp_goodput = served_rate              # lost packets are gone for good
        udp_loss = loss
        udp_delay = delay

        # ---- TCP: reliable + congestion controlled -------------------------
        # Goodput cannot exceed capacity; congestion control caps it there.
        tcp_goodput = min(lam, capacity * (1 - 0.02))   # ~link capacity
        tcp_goodput = min(tcp_goodput, served_rate / (1 - loss + 1e-9))
        tcp_goodput = min(tcp_goodput, capacity)
        tcp_loss = 0.0                          # retransmission recovers loss
        # Reliability cost: base delay inflated by retransmissions (~ loss)
        # plus congestion-window queueing growth as the system saturates.
        rho = lam / capacity
        tcp_delay = delay * (1 + 2.0 * loss) * (1 + max(0.0, rho - 0.7))

        rows.append({
            "lambda": lam,
            "offered_rho": round(lam / capacity, 3),
            "udp_goodput": udp_goodput,
            "udp_delay": udp_delay,
            "udp_loss": udp_loss,
            "tcp_goodput": tcp_goodput,
            "tcp_delay": tcp_delay,
            "tcp_loss": tcp_loss,
        })

    result = pd.DataFrame(rows)
    result.attrs["capacity"] = capacity
    result.attrs["mu"] = mu
    result.attrs["c"] = c
    result.attrs["K"] = K
    return result


def summarise(df):
    """Print a compact TCP-vs-UDP summary table."""
    print("\n" + "=" * 70)
    print("  TCP vs UDP  --  behaviour under increasing load")
    print(f"  capacity = c*mu = {df.attrs['capacity']}  pkts/s   "
          f"(c={df.attrs['c']}, mu={df.attrs['mu']}, K={df.attrs['K']})")
    print("=" * 70)
    show = df[["lambda", "offered_rho",
               "udp_goodput", "udp_loss",
               "tcp_goodput", "tcp_delay"]].copy()
    with pd.option_context("display.float_format", lambda x: f"{x:8.3f}"):
        print(show.to_string(index=False))
    print("=" * 70)
    return df


if __name__ == "__main__":
    summarise(compare_protocols(sim_time=1500))
