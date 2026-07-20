"""Interactive Streamlit dashboard.  Run: streamlit run app.py"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from src import theoretical
from src.queue_models import simulate
from src.metrics import compute_metrics, compare_with_theory
from src.protocol_comparison import compare_protocols


st.set_page_config(page_title="Network Performance Analyzer",
                   page_icon="📡", layout="wide")

st.title("📡 Network Protocol Performance Analyzer")
st.caption("Queuing-theory based simulation (SimPy) · Performance Engineering "
           "Lab · JIIT Sector 62 — Abhijeet Kumar, Viyom Shukla, Devang Dixit")


# ----- Sidebar controls -----
st.sidebar.header("⚙️  Simulation parameters")
model = st.sidebar.selectbox(
    "Queue model",
    ["M/M/1  (single server)", "M/M/c  (multi-server)",
     "M/M/c/K  (finite buffer / loss)"])
lam = st.sidebar.slider("Arrival rate  λ  (packets/s)", 1.0, 40.0, 8.0, 0.5)
mu = st.sidebar.slider("Service rate  μ  (packets/s per server)", 1.0, 40.0, 10.0, 0.5)

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

tab1, tab2, tab3, tab4 = st.tabs(
    ["🎯 Single Simulation", "📈 Load Sweep", "🖥️ Server Comparison", "🔀 TCP vs UDP"])


# ----- Tab 1: single simulation + validation -----
with tab1:
    model_str = f"M/M/{c}" + (f"/{K}" if K is not None else "")
    st.subheader(f"Scenario:  {model_str}   (λ={lam}, μ={mu}, c={c}"
                 + (f", K={K}" if K is not None else "") + ")")

    if K is None and rho >= 1:
        st.warning("The queue is unstable (ρ ≥ 1). Adjust the sidebar parameters.")
    else:
        with st.spinner("Running discrete-event simulation…"):
            df = simulate(lam, mu, c=c, K=K, sim_time=sim_time, seed=int(seed))
            m = compute_metrics(df)
            table = compare_with_theory(df)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Throughput", f"{m['throughput']:.2f} pkt/s")
        k2.metric("Avg delay  W", f"{m['avg_delay']*1000:.1f} ms")
        k3.metric("Packet loss", f"{m['packet_loss']*100:.2f} %")
        k4.metric("Utilisation", f"{m['utilisation']*100:.1f} %")

        c_left, c_right = st.columns([1.1, 1])
        with c_left:
            st.markdown("**Simulation vs Theory** — validation table")
            st.dataframe(
                table.style.format({"Simulation": "{:.4f}", "Theory": "{:.4f}",
                                    "Abs. Error": "{:.4f}"}),
                use_container_width=True, hide_index=True)
            st.caption("Small errors confirm the simulation reproduces queuing theory.")
        with c_right:
            served = df[df["served"]]
            fig, ax = plt.subplots(figsize=(5, 3.6))
            ax.hist(served["sojourn_time"], bins=40, color="#4C72B0", edgecolor="white")
            ax.axvline(m["avg_delay"], color="red", ls="--",
                       label=f"mean = {m['avg_delay']:.3f}s")
            ax.set_xlabel("Time in system  W  (s)"); ax.set_ylabel("Packets")
            ax.set_title("Distribution of packet delay"); ax.legend()
            fig.tight_layout()
            st.pyplot(fig)

        st.caption(f"Arrivals: {m['arrivals']}  |  served: {m['served']}  |  "
                   f"dropped: {m['dropped']}")


# ----- Tab 2: load sweep -----
with tab2:
    st.subheader(f"Load sweep — performance vs traffic  (M/M/{c})")
    st.caption("λ varied so ρ goes from light to heavy; markers on theory curves.")

    rhos = np.linspace(0.1, 0.95, 10)
    lams = rhos * c * mu
    sim_delay, th_delay, sim_thr, th_thr = [], [], [], []
    prog = st.progress(0.0)
    for i, l in enumerate(lams):
        mm = compute_metrics(simulate(l, mu, c=c, sim_time=min(sim_time, 3000), seed=int(seed)))
        t = theoretical.analyse(l, mu, c=c)
        sim_delay.append(mm["avg_delay"]); th_delay.append(t["W"])
        sim_thr.append(mm["throughput"]); th_thr.append(t["throughput"])
        prog.progress((i + 1) / len(lams))
    prog.empty()

    growth = sim_delay[-1] / sim_delay[0]
    g1, g2, g3 = st.columns(3)
    g1.metric(f"Delay at ρ={rhos[0]:.2f}", f"{sim_delay[0]*1000:.0f} ms")
    g2.metric(f"Delay at ρ={rhos[-1]:.2f}", f"{sim_delay[-1]*1000:.0f} ms",
              delta=f"{growth:.0f}× higher", delta_color="inverse")
    g3.metric("Max throughput", f"{max(sim_thr):.1f} pkt/s")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(rhos, th_delay, "b-", label="Theory"); ax1.plot(rhos, sim_delay, "ro", label="Simulation")
    ax1.set_xlabel("Traffic intensity  ρ"); ax1.set_ylabel("Avg delay W (s)")
    ax1.set_title("Delay vs Load"); ax1.grid(alpha=0.3); ax1.legend()
    ax2.plot(rhos, th_thr, "g-", label="Theory"); ax2.plot(rhos, sim_thr, "ks", label="Simulation")
    ax2.set_xlabel("Traffic intensity  ρ"); ax2.set_ylabel("Throughput (pkt/s)")
    ax2.set_title("Throughput vs Load"); ax2.grid(alpha=0.3); ax2.legend()
    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("**Values behind the graph**")
    st.dataframe(pd.DataFrame({
        "ρ (load)": [f"{r:.2f}" for r in rhos],
        "λ (pkt/s)": [f"{l:.1f}" for l in lams],
        "Delay – simulated (ms)": [f"{v*1000:.1f}" for v in sim_delay],
        "Delay – theory (ms)": [f"{v*1000:.1f}" for v in th_delay],
        "Error (ms)": [f"{abs(a-b)*1000:.1f}" for a, b in zip(sim_delay, th_delay)],
        "Throughput (pkt/s)": [f"{v:.2f}" for v in sim_thr],
    }), use_container_width=True, hide_index=True)
    st.info(f"Delay grows **{growth:.0f}×** (from {sim_delay[0]*1000:.0f} ms to "
            f"{sim_delay[-1]*1000:.0f} ms) while ρ goes {rhos[0]:.2f} → {rhos[-1]:.2f}. "
            "That sharp rise is the queuing **'knee'**.")


# ----- Tab 3: M/M/1 vs M/M/c -----
with tab3:
    st.subheader("Effect of adding servers:  M/M/1 vs M/M/c")
    servers = st.multiselect("Servers to compare", [1, 2, 3, 4], default=[1, 2, 3])
    if servers:
        rhos = np.linspace(0.1, 0.9, 9)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        colors = ["#C44E52", "#4C72B0", "#55A868", "#8172B3"]
        end_vals, table = {}, {"ρ (load)": [f"{r:.1f}" for r in rhos]}
        for i, cc in enumerate(sorted(servers)):
            delays = [theoretical.analyse(r * cc * mu, mu, c=cc)["W"] for r in rhos]
            end_vals[cc] = delays[-1]
            table[f"M/M/{cc} delay (ms)"] = [f"{v*1000:.0f}" for v in delays]
            ax.plot(rhos, delays, "o-", color=colors[i % 4], label=f"M/M/{cc}")
        ax.set_xlabel("Traffic intensity  ρ"); ax.set_ylabel("Avg delay W (s)")
        ax.set_title("Average delay vs load"); ax.grid(alpha=0.3); ax.legend()
        fig.tight_layout()
        st.pyplot(fig)

        cols = st.columns(len(end_vals))
        base = end_vals[min(end_vals)]
        for col, (cc, v) in zip(cols, sorted(end_vals.items())):
            col.metric(f"M/M/{cc} at ρ=0.9", f"{v*1000:.0f} ms",
                       delta=None if v == base else f"{base/v:.1f}× faster")

        st.markdown("**Values behind the graph**")
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
        st.info("Same load per server, but more servers means far less waiting — "
                "the delay drops sharply going from one server to two.")


# ----- Tab 4: TCP vs UDP -----
with tab4:
    st.subheader("TCP vs UDP under increasing network load")
    cap_c = st.slider("Servers for this test", 1, 4, 1, key="tcp_c")
    cap_K = st.slider("Buffer capacity K", 2, 30, 10, key="tcp_K")

    with st.spinner("Sweeping load for TCP and UDP…"):
        res = compare_protocols(mu=mu, c=cap_c, K=cap_K,
                                sim_time=min(sim_time, 2000), seed=int(seed))

    rr = res["offered_rho"]
    cap = res.attrs["capacity"]
    udp_peak_loss = res["udp_loss"].max() * 100
    tcp_end_delay = res["tcp_delay"].iloc[-1]
    udp_end_delay = res["udp_delay"].iloc[-1]

    q1, q2, q3 = st.columns(3)
    q1.metric("UDP peak packet loss", f"{udp_peak_loss:.1f} %", delta="data lost", delta_color="inverse")
    q2.metric("TCP packet loss", "0.0 %", delta="all data delivered")
    q3.metric("TCP delay at max load", f"{tcp_end_delay:.2f} s",
              delta=f"{tcp_end_delay/udp_end_delay:.1f}× UDP's delay", delta_color="inverse")

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(14, 4))
    a1.plot(rr, res["tcp_goodput"], "b-o", label="TCP"); a1.plot(rr, res["udp_goodput"], "r-s", label="UDP")
    a1.axhline(cap, color="gray", ls="--", label="Capacity")
    a1.set_title("Goodput vs Load"); a1.set_xlabel("Offered load ρ")
    a1.set_ylabel("Goodput (pkt/s)"); a1.grid(alpha=0.3); a1.legend()
    a2.plot(rr, res["tcp_delay"], "b-o", label="TCP"); a2.plot(rr, res["udp_delay"], "r-s", label="UDP")
    a2.set_title("Delay vs Load"); a2.set_xlabel("Offered load ρ")
    a2.set_ylabel("Avg delay (s)"); a2.grid(alpha=0.3); a2.legend()
    a3.plot(rr, res["tcp_loss"] * 100, "b-o", label="TCP"); a3.plot(rr, res["udp_loss"] * 100, "r-s", label="UDP")
    a3.set_title("Packet Loss vs Load"); a3.set_xlabel("Offered load ρ")
    a3.set_ylabel("Loss (%)"); a3.grid(alpha=0.3); a3.legend()
    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("**Values behind the graph**")
    st.dataframe(pd.DataFrame({
        "ρ (offered)": [f"{v:.2f}" for v in rr],
        "λ (pkt/s)": [f"{v:.1f}" for v in res["lambda"]],
        "TCP goodput": [f"{v:.2f}" for v in res["tcp_goodput"]],
        "UDP goodput": [f"{v:.2f}" for v in res["udp_goodput"]],
        "TCP delay (s)": [f"{v:.3f}" for v in res["tcp_delay"]],
        "UDP delay (s)": [f"{v:.3f}" for v in res["udp_delay"]],
        "TCP loss %": [f"{v*100:.1f}" for v in res["tcp_loss"]],
        "UDP loss %": [f"{v*100:.1f}" for v in res["udp_loss"]],
    }), use_container_width=True, hide_index=True)
    st.success(f"**The trade-off in numbers:** at maximum load UDP threw away "
               f"**{udp_peak_loss:.0f}%** of packets but stayed at {udp_end_delay:.2f} s. "
               f"TCP delivered **100%** of the data, but its delay climbed to "
               f"**{tcp_end_delay:.2f} s** — about {tcp_end_delay/udp_end_delay:.1f}× UDP's.")

st.sidebar.markdown("---")
st.sidebar.caption("Built with SimPy · NumPy · SciPy · Matplotlib · Streamlit")
