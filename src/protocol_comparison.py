"""Compare TCP (reliable, congestion-controlled) vs UDP (best-effort) under load."""

import numpy as np
import pandas as pd

from .queue_models import simulate
from .metrics import compute_metrics


def compare_protocols(mu=10, c=1, K=10, loads=None, sim_time=2000, seed=42):
    capacity = c * mu
    if loads is None:
        loads = np.round(np.linspace(0.2, 1.6, 12) * capacity, 2)

    rows = []
    for lam in loads:
        m = compute_metrics(simulate(lam, mu, c=c, K=K, sim_time=sim_time, seed=seed))
        served_rate, loss, delay = m["throughput"], m["packet_loss"], m["avg_delay"]

        # UDP: lost packets are gone for good
        udp_goodput = served_rate

        # TCP: retransmission recovers loss, congestion control caps goodput at capacity
        tcp_goodput = min(lam, capacity * (1 - 0.02))
        tcp_goodput = min(tcp_goodput, served_rate / (1 - loss + 1e-9), capacity)
        rho = lam / capacity
        tcp_delay = delay * (1 + 2.0 * loss) * (1 + max(0.0, rho - 0.7))

        rows.append({
            "lambda": lam,
            "offered_rho": round(rho, 3),
            "udp_goodput": udp_goodput,
            "udp_delay": delay,
            "udp_loss": loss,
            "tcp_goodput": tcp_goodput,
            "tcp_delay": tcp_delay,
            "tcp_loss": 0.0,
        })

    result = pd.DataFrame(rows)
    result.attrs.update(capacity=capacity, mu=mu, c=c, K=K)
    return result


def summarise(df):
    print("\n" + "=" * 70)
    print("  TCP vs UDP  --  behaviour under increasing load")
    print(f"  capacity = c*mu = {df.attrs['capacity']}  pkts/s   "
          f"(c={df.attrs['c']}, mu={df.attrs['mu']}, K={df.attrs['K']})")
    print("=" * 70)
    show = df[["lambda", "offered_rho", "udp_goodput", "udp_loss",
               "tcp_goodput", "tcp_delay"]]
    with pd.option_context("display.float_format", lambda x: f"{x:8.3f}"):
        print(show.to_string(index=False))
    print("=" * 70)
    return df


if __name__ == "__main__":
    summarise(compare_protocols(sim_time=1500))
