"""
Parametre taramasi + yerel optimizasyon (NEC2 / nec2c).

Optimize edilen 4 parametre:
  lobe_len_mm  : bir yapragin toplam tel boyu
  elev_deg     : yaprak egimi
  twist_deg    : halka duzlemi bukulmesi (RHCP icin +)
  theta0_deg   : yaprak "bacaklarinin" acikligi (gozyasi / yaprak formu)

Hedefler:
  * f0 = 1280 MHz'de SWR <= 1.2, 1220-1340 MHz bandinda SWR <= 1.5
  * Ufuk civarinda (theta 60..100) dusuk eksenel oran (AR)
  * Azimutta duzgun (omni) RHCP desen, yuksek RHCP kazanc

Kullanim:  python3 tools/optimize.py
Cikti   :  results/optimization_grid.csv, results/best_params.json
"""
import itertools
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cloverleaf import CloverParams, simulate, circular_components, swr  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
BOUNDS = dict(L=(200, 290), elev=(-35, 45), twist=(15, 85), t0=(8, 75))
KEYS = ["L", "elev", "twist", "t0", "R", "X", "swr", "swr_max", "ar_mean", "ar_h",
        "ar_edge", "gR", "gR_h", "ripple", "cost"]


def evaluate(x):
    L, elev, tw, t0 = map(float, x)
    pen = 0.0
    for v, (lo, hi) in zip((L, elev, tw, t0), BOUNDS.values()):
        pen += 10 * (max(0, lo - v) + max(0, v - hi))
    if pen > 0:
        return dict(L=L, elev=elev, twist=tw, t0=t0, cost=1e3 + pen)
    p = CloverParams(lobe_len_mm=L, elev_deg=elev, twist_deg=tw, theta0_deg=t0)
    try:
        res = simulate(p, f_start=1220, f_stop=1340, f_step=60, pattern="band")
        mid = res[1]
        th, ph, gt, gR, gL, ar = circular_components(mid["pattern"])
        ar_edges = [np.mean(np.minimum(circular_components(r["pattern"])[5], 30)) for r in (res[0], res[2])]
    except Exception:
        return dict(L=L, elev=elev, twist=tw, t0=t0, cost=1e3)
    s = swr(mid["Z"])
    s_max = max(swr(r["Z"]) for r in res)
    ar_mean = float(np.mean(np.minimum(ar, 30)))
    hz = th == 90
    ripple = float(gR[hz].max() - gR[hz].min())
    cost = (4 * max(0.0, s - 1.2) + 3 * max(0.0, s_max - 1.5) + ar_mean
            + 0.3 * float(np.mean(ar_edges)) + 0.5 * ripple - 0.5 * float(np.mean(gR)))
    return dict(L=L, elev=elev, twist=tw, t0=t0, R=mid["Z"].real, X=mid["Z"].imag, swr=s,
                swr_max=s_max, ar_mean=ar_mean, ar_h=float(np.mean(ar[hz])),
                ar_edge=float(np.mean(ar_edges)), gR=float(np.mean(gR)),
                gR_h=float(np.mean(gR[hz])), ripple=ripple, cost=cost)


def _cost(x):
    return evaluate(x)["cost"]


def main():
    os.makedirs(RES, exist_ok=True)
    # 1) Kaba izgara taramasi
    grid = list(itertools.product(np.arange(220, 271, 5), np.arange(-30, 31, 10),
                                  np.arange(35, 81, 5), (20, 40, 60)))
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(evaluate, grid, chunksize=16))
    rows = [r for r in rows if r["cost"] < 1e3]
    rows.sort(key=lambda r: r["cost"])
    with open(os.path.join(RES, "optimization_grid.csv"), "w") as fh:
        fh.write(",".join(KEYS) + "\n")
        for r in rows:
            fh.write(",".join(f"{r[k]:.4f}" for k in KEYS) + "\n")
    print(f"Izgara: {len(rows)} gecerli nokta. En iyi 5:")
    for r in rows[:5]:
        print({k: round(float(r[k]), 3) for k in KEYS})

    # 2) En iyi 6 baslangictan Nelder-Mead ince ayar (paralel)
    starts = [[r["L"], r["elev"], r["twist"], r["t0"]] for r in rows[:6]]
    with ProcessPoolExecutor() as ex:
        opts = list(ex.map(_nm, starts))
    best = min(opts, key=lambda o: o[1])
    e = evaluate(best[0])
    print("Ince ayar sonucu:", {k: round(float(e[k]), 3) for k in KEYS})
    with open(os.path.join(RES, "best_params.json"), "w") as fh:
        json.dump({k: round(float(e[k]), 4) for k in KEYS}, fh, indent=2)


def _nm(x0):
    o = minimize(_cost, x0, method="Nelder-Mead",
                 options=dict(maxiter=500, xatol=0.05, fatol=1e-4))
    return list(o.x), float(o.fun)


if __name__ == "__main__":
    main()
