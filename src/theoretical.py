"""Closed-form queuing formulas (M/M/1, M/M/c, M/M/c/K) for validating the simulation."""

from math import factorial


def mm1(lam, mu):
    # M/M/1: single server, infinite buffer
    rho = lam / mu
    if rho >= 1:
        raise ValueError(f"M/M/1 unstable: rho = {rho:.3f} >= 1 (need lambda < mu).")
    return {
        "model": "M/M/1",
        "rho": rho,
        "L": rho / (1 - rho),
        "Lq": rho ** 2 / (1 - rho),
        "W": 1 / (mu - lam),
        "Wq": rho / (mu - lam),
        "throughput": lam,
        "P_block": 0.0,
    }


def erlang_c(c, a):
    # Probability an arrival must wait (all c servers busy); a = lam/mu
    rho = a / c
    sum_terms = sum(a ** n / factorial(n) for n in range(c))
    last = a ** c / (factorial(c) * (1 - rho))
    return last / (sum_terms + last)


def mmc(lam, mu, c):
    # M/M/c: c parallel servers, infinite buffer
    a = lam / mu
    rho = a / c
    if rho >= 1:
        raise ValueError(f"M/M/c unstable: rho = {rho:.3f} >= 1 (need lambda < c*mu).")
    Pw = erlang_c(c, a)
    Lq = Pw * rho / (1 - rho)
    Wq = Lq / lam
    W = Wq + 1 / mu
    return {
        "model": f"M/M/{c}",
        "rho": rho,
        "L": lam * W,
        "Lq": Lq,
        "W": W,
        "Wq": Wq,
        "P_wait": Pw,
        "throughput": lam,
        "P_block": 0.0,
    }


def mmck(lam, mu, c, K):
    # M/M/c/K: c servers, finite capacity K -> blocking / packet loss
    if K < c:
        raise ValueError("Capacity K must be >= number of servers c.")
    a = lam / mu

    # Un-normalised state probabilities, then normalise
    p = [1.0] + [0.0] * K
    for n in range(1, K + 1):
        p[n] = p[n - 1] * a / n if n <= c else p[n - 1] * a / c
    p0 = 1.0 / sum(p)
    p = [p0 * x for x in p]

    P_block = p[K]
    lam_eff = lam * (1 - P_block)
    L = sum(n * p[n] for n in range(K + 1))
    W = L / lam_eff
    Wq = W - 1 / mu
    return {
        "model": f"M/M/{c}/{K}",
        "rho": a / c,
        "L": L,
        "Lq": lam_eff * Wq,
        "W": W,
        "Wq": Wq,
        "P_block": P_block,
        "packet_loss": P_block,
        "throughput": lam_eff,
    }


def analyse(lam, mu, c=1, K=None):
    # Dispatch to the right model based on c and K
    if K is not None:
        return mmck(lam, mu, c, K)
    return mm1(lam, mu) if c == 1 else mmc(lam, mu, c)


if __name__ == "__main__":
    print("M/M/1 :", mm1(8, 10))
    print("M/M/2 :", mmc(15, 10, 2))
    print("M/M/2/5:", mmck(18, 10, 2, 5))
