"""
theoretical.py
--------------
Closed-form queuing-theory formulas used to VALIDATE the discrete-event
simulation results.

Implements:
    * M/M/1      -- single server, infinite buffer
    * M/M/c      -- c parallel servers, infinite buffer (Erlang-C)
    * M/M/c/K    -- c servers, finite buffer of size K (blocking / packet loss)

Symbols
    lam  (lambda) : mean packet arrival rate   [packets / sec]
    mu   (mu)     : mean service rate / server  [packets / sec]
    c             : number of parallel servers
    K             : system capacity (servers + buffer) for the finite model
    rho           : traffic intensity / utilisation  =  lam / (c * mu)

All time values are in seconds; all rate values in packets/sec.
Little's Law  L = lam * W  is used throughout and is checked in the demo.
"""

from math import factorial


# --------------------------------------------------------------------------- #
#  M/M/1  --  single server, infinite queue
# --------------------------------------------------------------------------- #
def mm1(lam, mu):
    """
    Analytical results for an M/M/1 queue.

    Returns a dict with utilisation, mean number in system/queue,
    mean time in system/queue and throughput.
    Raises ValueError if the system is unstable (rho >= 1).
    """
    rho = lam / mu
    if rho >= 1:
        raise ValueError(
            f"M/M/1 unstable: rho = {rho:.3f} >= 1 (lambda must be < mu)."
        )

    L = rho / (1 - rho)            # mean number in system
    Lq = rho ** 2 / (1 - rho)      # mean number waiting in queue
    W = 1 / (mu - lam)             # mean sojourn (system) time
    Wq = rho / (mu - lam)          # mean waiting time in queue

    return {
        "model": "M/M/1",
        "rho": rho,
        "L": L,
        "Lq": Lq,
        "W": W,
        "Wq": Wq,
        "throughput": lam,         # infinite buffer -> everything is served
        "P_block": 0.0,
    }


# --------------------------------------------------------------------------- #
#  M/M/c  --  c servers, infinite queue  (Erlang-C)
# --------------------------------------------------------------------------- #
def erlang_c(c, a):
    """
    Erlang-C probability that an arriving customer has to WAIT
    (all c servers busy).  'a' = offered load in Erlangs = lam / mu.
    """
    rho = a / c
    # sum_{n=0}^{c-1}  a^n / n!
    sum_terms = sum(a ** n / factorial(n) for n in range(c))
    last = a ** c / (factorial(c) * (1 - rho))
    return last / (sum_terms + last)


def mmc(lam, mu, c):
    """
    Analytical results for an M/M/c queue (c parallel servers, infinite buffer).
    """
    a = lam / mu                   # offered load (Erlangs)
    rho = a / c                    # per-server utilisation
    if rho >= 1:
        raise ValueError(
            f"M/M/c unstable: rho = {rho:.3f} >= 1 (need lambda < c*mu)."
        )

    Pw = erlang_c(c, a)            # prob. of waiting
    Lq = Pw * rho / (1 - rho)      # mean number waiting
    Wq = Lq / lam                  # mean waiting time
    W = Wq + 1 / mu                # mean sojourn time
    L = lam * W                    # Little's Law

    return {
        "model": f"M/M/{c}",
        "rho": rho,
        "L": L,
        "Lq": Lq,
        "W": W,
        "Wq": Wq,
        "P_wait": Pw,
        "throughput": lam,
        "P_block": 0.0,
    }


# --------------------------------------------------------------------------- #
#  M/M/c/K  --  c servers, finite capacity K  (blocking -> packet loss)
# --------------------------------------------------------------------------- #
def mmck(lam, mu, c, K):
    """
    Analytical results for an M/M/c/K queue.

    K = maximum number of packets in the system (in service + waiting).
    An arrival that finds the system full (K packets present) is dropped,
    which models buffer overflow / packet loss.
    """
    if K < c:
        raise ValueError("Capacity K must be >= number of servers c.")

    a = lam / mu                   # offered load

    # Un-normalised state probabilities  p_n / p_0
    p = [0.0] * (K + 1)
    p[0] = 1.0
    for n in range(1, K + 1):
        if n <= c:
            p[n] = p[n - 1] * a / n
        else:
            p[n] = p[n - 1] * a / c

    p0 = 1.0 / sum(p)
    p = [p0 * x for x in p]        # normalised probabilities  p_0 .. p_K

    P_block = p[K]                 # prob. system full  -> loss probability
    lam_eff = lam * (1 - P_block)  # effective (accepted) arrival rate

    L = sum(n * p[n] for n in range(K + 1))     # mean number in system
    W = L / lam_eff                              # Little's Law (effective rate)
    Wq = W - 1 / mu                              # mean waiting time
    Lq = lam_eff * Wq

    return {
        "model": f"M/M/{c}/{K}",
        "rho": a / c,
        "L": L,
        "Lq": Lq,
        "W": W,
        "Wq": Wq,
        "P_block": P_block,
        "packet_loss": P_block,
        "throughput": lam_eff,      # only accepted packets are served
    }


# --------------------------------------------------------------------------- #
#  Convenience dispatcher
# --------------------------------------------------------------------------- #
def analyse(lam, mu, c=1, K=None):
    """
    Pick the right analytical model based on the arguments.
        c == 1, K is None   -> M/M/1
        c  > 1, K is None   -> M/M/c
        K is not None       -> M/M/c/K
    """
    if K is not None:
        return mmck(lam, mu, c, K)
    if c == 1:
        return mm1(lam, mu)
    return mmc(lam, mu, c)


if __name__ == "__main__":
    # Quick self-test / Little's Law check
    print("M/M/1 :", mm1(8, 10))
    print("M/M/2 :", mmc(15, 10, 2))
    print("M/M/2/5:", mmck(18, 10, 2, 5))
