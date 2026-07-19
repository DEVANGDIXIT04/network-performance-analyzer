"""
metrics.py
----------
Turns the raw per-packet DataFrame produced by queue_models.py into the
performance metrics described in the synopsis:

    * Throughput        -- packets successfully served per second
    * Average delay     -- mean sojourn time (waiting + service)
    * Average wait      -- mean time spent queued before service
    * Packet loss       -- fraction of arrivals dropped (buffer full)
    * Utilisation       -- fraction of time the server(s) were busy

It also builds a side-by-side comparison table (simulation vs theory) so the
two can be validated against each other.
"""

import pandas as pd

from . import theoretical


def compute_metrics(df):
    """Compute performance metrics from a simulation DataFrame."""
    sim_time = df.attrs["sim_time"]
    busy_time = df.attrs["busy_time"]
    c = df.attrs["c"]

    total = len(df)
    served_mask = df["served"]
    dropped = int(df["dropped"].sum())
    served = int(served_mask.sum())

    served_df = df[served_mask]

    throughput = served / sim_time if sim_time else 0.0
    avg_delay = served_df["sojourn_time"].mean() if served else 0.0
    avg_wait = served_df["waiting_time"].mean() if served else 0.0
    packet_loss = dropped / total if total else 0.0

    # Server utilisation = busy-server-seconds / (c servers * total seconds)
    utilisation = busy_time / (c * sim_time) if sim_time else 0.0

    # Mean number in system via Little's Law  (L = throughput * W)
    L = throughput * avg_delay

    return {
        "arrivals": total,
        "served": served,
        "dropped": dropped,
        "throughput": throughput,
        "avg_delay": avg_delay,
        "avg_wait": avg_wait,
        "packet_loss": packet_loss,
        "utilisation": utilisation,
        "L": L,
    }


def compare_with_theory(df):
    """
    Build a DataFrame comparing simulated metrics with the closed-form
    queuing-theory predictions for the same lambda, mu, c, K.
    """
    lam = df.attrs["lam"]
    mu = df.attrs["mu"]
    c = df.attrs["c"]
    K = df.attrs["K"]

    sim = compute_metrics(df)
    th = theoretical.analyse(lam, mu, c=c, K=K)

    # Actual server utilisation = served-work rate / total service capacity.
    # For infinite-buffer models this equals rho; for the finite M/M/c/K model
    # it is based on the EFFECTIVE (accepted) throughput, so it stays
    # consistent with what the simulation measures.
    th_util = th["throughput"] / (c * mu)

    rows = [
        ("Utilisation (rho)", sim["utilisation"], th_util),
        ("Throughput (pkts/s)", sim["throughput"], th["throughput"]),
        ("Avg delay  W (s)", sim["avg_delay"], th["W"]),
        ("Avg wait   Wq (s)", sim["avg_wait"], th["Wq"]),
        ("Number in system L", sim["L"], th["L"]),
        ("Packet loss", sim["packet_loss"], th.get("P_block", 0.0)),
    ]

    table = pd.DataFrame(rows, columns=["Metric", "Simulation", "Theory"])
    table["Abs. Error"] = (table["Simulation"] - table["Theory"]).abs()
    return table


def print_report(df, title="PERFORMANCE REPORT"):
    """Pretty-print a full report for one scenario."""
    lam, mu, c, K = df.attrs["lam"], df.attrs["mu"], df.attrs["c"], df.attrs["K"]
    model = f"M/M/{c}" + (f"/{K}" if K is not None else "")

    print("\n" + "=" * 62)
    print(f"  {title}  --  {model}")
    print(f"  lambda={lam}  mu={mu}  servers c={c}"
          + (f"  capacity K={K}" if K is not None else "  (infinite buffer)"))
    print("=" * 62)

    table = compare_with_theory(df)
    with pd.option_context("display.float_format", lambda x: f"{x:10.4f}"):
        print(table.to_string(index=False))
    print("=" * 62)
    return table


if __name__ == "__main__":
    from .queue_models import simulate
    df = simulate(lam=8, mu=10, c=1, sim_time=3000, seed=1)
    print_report(df, "SELF-TEST")
