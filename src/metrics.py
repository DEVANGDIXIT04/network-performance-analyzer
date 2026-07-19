"""Compute performance metrics from a simulation and compare them with theory."""

import pandas as pd

from . import theoretical


def compute_metrics(df):
    sim_time = df.attrs["sim_time"]
    busy_time = df.attrs["busy_time"]
    c = df.attrs["c"]

    total = len(df)
    served = int(df["served"].sum())
    dropped = int(df["dropped"].sum())
    served_df = df[df["served"]]

    throughput = served / sim_time if sim_time else 0.0
    avg_delay = served_df["sojourn_time"].mean() if served else 0.0
    avg_wait = served_df["waiting_time"].mean() if served else 0.0

    return {
        "arrivals": total,
        "served": served,
        "dropped": dropped,
        "throughput": throughput,
        "avg_delay": avg_delay,
        "avg_wait": avg_wait,
        "packet_loss": dropped / total if total else 0.0,
        "utilisation": busy_time / (c * sim_time) if sim_time else 0.0,
        "L": throughput * avg_delay,  # Little's Law
    }


def compare_with_theory(df):
    lam, mu, c, K = df.attrs["lam"], df.attrs["mu"], df.attrs["c"], df.attrs["K"]
    sim = compute_metrics(df)
    th = theoretical.analyse(lam, mu, c=c, K=K)

    # Effective utilisation keeps M/M/c/K consistent with the simulation
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
    print_report(simulate(lam=8, mu=10, c=1, sim_time=3000, seed=1), "SELF-TEST")
