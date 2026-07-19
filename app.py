"""
app.py  --  Interactive web frontend (Streamlit)
=================================================
A dynamic dashboard for the Network Protocol Performance Analyzer.

Move the sliders in the sidebar and every metric, table and graph recomputes
live.  Run with:

    streamlit run app.py

Performance Engineering Lab [17M15CS122], JIIT Sector 62, Noida
Team: Abhijeet Kumar (22803029), Viyom Shukla (22803030), Devang Dixit (22803031)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from src import theoretical
from src.queue_models import simulate
from src.metrics import compute_metrics, compare_with_theory
from src.protocol_comparison import compare_protocols


# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Network Performance Analyzer",
                   page_icon="📡", layout="wide")

st.title("📡 Network Protocol Performance Analyzer")
st.caption("Queuing-theory based simulation (SimPy) · Performance Engineering "
           "Lab · JIIT Sector 62 — Abhijeet Kumar, Viyom Shukla, Devang Dixit")


# ----------------------------- Sidebar controls ---------------------------- #
st.sidebar.header("⚙️  Simulation parameters")

model = st.sidebar.selectbox(
    "Queue model",
    ["M/M/1  (single server)",
     "M/M/c  (multi-server)",
     "M/M/c/K  (finite buffer / loss)"],
)

lam = st.sidebar.slider("Arrival rate  λ  (packets/s)", 1.0, 40.0, 8.0, 0.5)
mu = st.sidebar.slider("Service rate  μ  (packets/s per server)",
                       1.0, 40.0, 10.0, 0.5)

c = 1
K = None
if model.startswith("M/M/c"):
    c = st.sidebar.slider("Number of servers  c", 1, 8, 2)
if "K" in model:
    K = st.sidebar.slider("System capacity  K", c, 30, max(c + 3, 6))

sim_time = st.sidebar.slider("Simulation time  (seconds)", 500, 8000, 3000, 500)
seed = st.sidebar.number_input("Random seed", 0, 9999, 1)

rho = lam / (c * mu)
st.sidebar.markdown("---")
st.sidebar.metric("Traffic intensity  ρ = λ/(c·μ)", f"{rho:.3f}")
if K is None and rho >= 1:
    st.sidebar.error("ρ ≥ 1 → unstable queue! Lower λ or raise μ / c.")


# ------------------------------- Tabs -------------------------------------- #
tab1, tab2, tab3, tab4 = st.tabs(
    ["🎯 Single Simulation", "📈 Load Sweep",
     "🖥️ Server Comparison", "🔀 TCP vs UDP"])


# =========================================================================== #
#  TAB 1 — single simulation + validation
# =========================================================================== #
with tab1:
    model_str = f"M/M/{c}" + (f"/{K}" if K is not None else "")
    st.subheader(f"Scenario:  {model_str}   (λ={lam}, μ={mu}, c={c}"
                 + (f", K={K}" if K is not None else "") + ")")

    if K is None and rho >= 1:
        st.warning("The queue is unstable (ρ ≥ 1). Adjust the parameters "
                   "in the sidebar to run this scenario.")
    else:
        with st.spinner("Running discrete-event simulation…"):
            df = simulate(lam, mu, c=c, K=K, sim_time=sim_time, seed=int(seed))
            m = compute_metrics(df)
            table = compare_with_theory(df)

        # KPI cards
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Throughput", f"{m['throughput']:.2f} pkt/s")
        k2.metric("Avg delay  W", f"{m['avg_delay']*1000:.1f} ms")
        k3.metric("Packet loss", f"{m['packet_loss']*100:.2f} %")
        k4.metric("Utilisation", f"{m['utilisation']*100:.1f} %")

        c_left, c_right = st.columns([1.1, 1])

        with c_left:
            st.markdown("**Simulation vs Theory** — validation table")
            st.dataframe(
                table.style.format(
                    {"Simulation": "{:.4f}", "Theory": "{:.4f}",
                     "Abs. Error": "{:.4f}"}),
                use_container_width=True, hide_index=True)
            st.caption("Small absolute errors confirm the simulation "
                       "reproduces closed-form queuing theory.")

        with c_right:
            # Histogram of sojourn times of served packets
            served = df[df["served"]]
            fig, ax = plt.subplots(figsize=(5, 3.6))
            ax.hist(served["sojourn_time"], bins=40, color="#4C72B0",
                    edgecolor="white")
            ax.axvline(m["avg_delay"], color="red", ls="--",
                       label=f"mean = {m['avg_delay']:.3f}s")
            ax.set_xlabel("Time in system  W  (s)")
            ax.set_ylabel("Packets")
            ax.set_title("Distribution of packet delay")
            ax.legend()
            fig.tight_layout()
            st.pyplot(fig)

        st.caption(f"Arrivals: {m['arrivals']}  |  served: {m['served']}  |  "
                   f"dropped: {m['dropped']}")


# =========================================================================== #
#  TAB 2 — load sweep
# =========================================================================== #
with tab2:
    st.subheader(f"Load sweep — how performance changes with traffic  (M/M/{c})")
    st.caption("λ is varied so that ρ goes from light to heavy load. "
               "Simulation markers are drawn on the theoretical curves.")

    rhos = np.linspace(0.1, 0.95, 10)
    lams = rhos * c * mu
    sim_delay, th_delay, sim_thr, th_thr = [], [], [], []
    prog = st.progress(0.0)
    for i, l in enumerate(lams):
        d = simulate(l, mu, c=c, sim_time=min(sim_time, 3000), seed=int(seed))
        mm = compute_metrics(d)
        t = theoretical.analyse(l, mu, c=c)
        sim_delay.append(mm["avg_delay"]); th_delay.append(t["W"])
        sim_thr.append(mm["throughput"]); th_thr.append(t["throughput"])
        prog.progress((i + 1) / len(lams))
    prog.empty()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(rhos, th_delay, "b-", label="Theory")
    ax1.plot(rhos, sim_delay, "ro", label="Simulation")
    ax1.set_xlabel("Traffic intensity  ρ"); ax1.set_ylabel("Avg delay W (s)")
    ax1.set_title("Delay vs Load"); ax1.grid(alpha=0.3); ax1.legend()
    ax2.plot(rhos, th_thr, "g-", label="Theory")
    ax2.plot(rhos, sim_thr, "ks", label="Simulation")
    ax2.set_xlabel("Traffic intensity  ρ"); ax2.set_ylabel("Throughput (pkt/s)")
    ax2.set_title("Throughput vs Load"); ax2.grid(alpha=0.3); ax2.legend()
    fig.tight_layout()
    st.pyplot(fig)
    st.info("Notice how the average delay stays flat and then **explodes** as "
            "ρ → 1 — the classic queuing 'knee'.")


# =========================================================================== #
#  TAB 3 — M/M/1 vs M/M/c
# =========================================================================== #
with tab3:
    st.subheader("Effect of adding servers:  M/M/1 vs M/M/c")
    st.caption("Same per-server load ρ, more servers → far lower delay.")

    servers = st.multiselect("Servers to compare", [1, 2, 3, 4], default=[1, 2, 3])
    if servers:
        rhos = np.linspace(0.1, 0.9, 9)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        colors = ["#C44E52", "#4C72B0", "#55A868", "#8172B3"]
        for i, cc in enumerate(sorted(servers)):
            delays = [theoretical.analyse(r * cc * mu, mu, c=cc)["W"] for r in rhos]
            ax.plot(rhos, delays, "o-", color=colors[i % 4], label=f"M/M/{cc}")
        ax.set_xlabel("Traffic intensity  ρ"); ax.set_ylabel("Avg delay W (s)")
        ax.set_title("Average delay vs load"); ax.grid(alpha=0.3); ax.legend()
        fig.tight_layout()
        st.pyplot(fig)


# =========================================================================== #
#  TAB 4 — TCP vs UDP
# =========================================================================== #
with tab4:
    st.subheader("TCP vs UDP under increasing network load")
    st.caption("Same finite-buffer queue; TCP retransmits + congestion-controls, "
               "UDP is best-effort.")

    cap_c = st.slider("Servers for this test", 1, 4, 1, key="tcp_c")
    cap_K = st.slider("Buffer capacity K", 2, 30, 10, key="tcp_K")

    with st.spinner("Sweeping load for TCP and UDP…"):
        res = compare_protocols(mu=mu, c=cap_c, K=cap_K,
                                sim_time=min(sim_time, 2000), seed=int(seed))

    rr = res["offered_rho"]
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(14, 4))
    a1.plot(rr, res["tcp_goodput"], "b-o", label="TCP")
    a1.plot(rr, res["udp_goodput"], "r-s", label="UDP")
    a1.axhline(res.attrs["capacity"], color="gray", ls="--", label="Capacity")
    a1.set_title("Goodput vs Load"); a1.set_xlabel("Offered load ρ")
    a1.set_ylabel("Goodput (pkt/s)"); a1.grid(alpha=0.3); a1.legend()
    a2.plot(rr, res["tcp_delay"], "b-o", label="TCP")
    a2.plot(rr, res["udp_delay"], "r-s", label="UDP")
    a2.set_title("Delay vs Load"); a2.set_xlabel("Offered load ρ")
    a2.set_ylabel("Avg delay (s)"); a2.grid(alpha=0.3); a2.legend()
    a3.plot(rr, res["tcp_loss"] * 100, "b-o", label="TCP")
    a3.plot(rr, res["udp_loss"] * 100, "r-s", label="UDP")
    a3.set_title("Packet Loss vs Load"); a3.set_xlabel("Offered load ρ")
    a3.set_ylabel("Loss (%)"); a3.grid(alpha=0.3); a3.legend()
    fig.tight_layout()
    st.pyplot(fig)

    st.success("**Key insight:** under overload UDP loses many packets but keeps "
               "low delay, while TCP recovers all data (≈0 loss) at the cost of "
               "higher delay — the reliability-vs-latency trade-off.")

st.sidebar.markdown("---")
st.sidebar.caption("Built with SimPy · NumPy · SciPy · Matplotlib · Streamlit")
