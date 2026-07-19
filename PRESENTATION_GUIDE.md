# Presentation & Viva Guide
### Network Protocol Performance Analyzer

Use this to demo the project to your teacher and to answer likely questions.

---

## A. Before the presentation (one-time)

```bash
cd NetworkPerformanceAnalyzer
pip install -r requirements.txt
python main.py --demo        # generates all graphs into results/
```

Open the `results/` folder so the five graphs are ready to show.

---

## B. Live demo flow (≈5 minutes)

1. **Open `main.py`** and explain it is a modular, menu-driven app; each `src/`
   module is one stage of the pipeline in the synopsis.

2. **Run `python main.py`** and walk through the menu live:
   - **Option 1 (M/M/1):** press Enter to accept defaults (λ=8, μ=10).
     → point at the *Simulation vs Theory* table: errors are tiny → "our
     simulation is validated against queuing theory."
   - **Option 3 (M/M/c/K):** use λ=18, μ=10, c=2, K=5.
     → show the **packet loss** column appear because the buffer is finite.
   - **Option 7 (TCP vs UDP):** show the table, then the graph pops up.

3. **Show the graphs** in `results/` and explain each (see section D).

> Tip: `python main.py --demo` does all of this non-interactively if you prefer
> a hands-off run.

---

## C. One-line explanation of each file

| File                     | What to say |
|--------------------------|-------------|
| `traffic_generator.py`   | "Generates Poisson arrivals — inter-arrival times are exponential." |
| `queue_models.py`        | "The SimPy discrete-event engine; one simulator handles M/M/1, M/M/c and M/M/c/K." |
| `theoretical.py`         | "The exact maths — Little's Law, Erlang-C, and the M/M/c/K birth–death solution — used to validate the simulation." |
| `metrics.py`             | "Turns raw per-packet data into throughput, delay, loss, utilisation and builds the comparison table." |
| `protocol_comparison.py` | "Models TCP (reliable, congestion-controlled) vs UDP (best-effort) on the same queue." |
| `visualization.py`       | "All the Matplotlib graphs." |
| `main.py`                | "The menu that ties the whole pipeline together." |

---

## D. What each graph proves

- **`load_sweep_mm1.png` / `load_sweep_mm2.png`** — simulation dots sit exactly
  on the theory curve. Delay is low, then explodes as ρ → 1. *This validates the
  model.*
- **`sim_vs_theory_mm1.png`** — bar chart: simulated and theoretical utilisation,
  delay, wait and L are the same height.
- **`mm1_vs_mmc.png`** — adding servers (M/M/2, M/M/3) keeps delay far below
  M/M/1 at the same load → *more servers = better performance.*
- **`tcp_vs_udp.png`** — the headline result:
  - *Goodput:* both rise, then saturate at link capacity.
  - *Loss:* UDP loss climbs steeply; TCP stays ≈0 (retransmission).
  - *Delay:* TCP delay grows sharply — the **reliability vs latency trade-off.**

---

## E. Likely viva questions & answers

**Q: What does M/M/1 mean?**
Markovian (Poisson) arrivals / Markovian (exponential) service / 1 server. The
first M is arrivals, second M is service, the number is servers.

**Q: What is ρ (rho) and why must it be < 1?**
Traffic intensity = λ/(c·μ), the fraction of capacity used. If ρ ≥ 1 packets
arrive faster than they can be served, so the queue grows without bound (unstable).

**Q: What is Little's Law?**
L = λ·W — the average number of packets in the system equals arrival rate times
average time in system. We use it to cross-check simulation and theory.

**Q: What is Erlang-C?**
The formula giving the probability that an arriving packet must wait because all
c servers are busy; it's how we get delay for the multi-server M/M/c model.

**Q: Why does M/M/c/K have packet loss but M/M/1 doesn't?**
M/M/1 has an infinite buffer, so nothing is ever dropped. M/M/c/K has a finite
buffer of size K; when it's full, new arrivals are dropped — that models real
router buffer overflow.

**Q: How is TCP different from UDP here?**
UDP is best-effort: dropped packets are lost forever, so under overload its
useful goodput falls and loss is high. TCP retransmits lost packets and uses
congestion control, so it delivers all data (≈0 loss) but pays with higher delay
and its goodput is capped at the link capacity.

**Q: How do you know the simulation is correct?**
Every scenario prints a Simulation-vs-Theory table; the absolute error is
typically under 1–2%, and on the load-sweep graph the simulation points lie on
the analytical curve.

**Q: What is discrete-event simulation / SimPy?**
Instead of stepping time in fixed ticks, we jump from event to event (arrival,
start-of-service, departure). SimPy is a Python library that schedules these
events, which makes the simulation fast and exact.

**Q: Why is the last simulation point slightly below theory at very high load?**
At ρ ≈ 0.95 the true delays are dominated by rare, very long queues. A
finite-length simulation under-samples those rare events, so the average is a
little low — increasing `sim_time` closes the gap. (Good thing to mention!)

---

## F. If something goes wrong on the day

- `ModuleNotFoundError: simpy` → run `pip install -r requirements.txt`.
- Graph window doesn't pop up → the PNGs are still saved in `results/`; open them there.
- Run from **inside** the `NetworkPerformanceAnalyzer` folder so `import src...` works.
