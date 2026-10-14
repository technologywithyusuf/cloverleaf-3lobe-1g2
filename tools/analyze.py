"""
Nihai tasarimin tum analizlerini uretir.

  python3 tools/analyze.py

Uretilenler
  models/  : 4nec2 ile acilacak .nec dosyalari (tarama, 3D desen, LHCP ve koaks varyantlari)
  results/ : grafikler (.png), tarama verisi (.csv), ozet (summary.json)
  docs/    : 1:1 olcekli yaprak bukme sablonu (PDF)
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cloverleaf import (CloverParams, build_wires, circular_components, simulate,  # noqa: E402
                        swr, write_nec, _lobe_points, solve_radius, _polyline_len)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD, RES, DOC = (os.path.join(ROOT, d) for d in ("models", "results", "docs"))
for d in (MOD, RES, DOC):
    os.makedirs(d, exist_ok=True)

P = CloverParams()                  # nihai tasarim (cloverleaf.py varsayilanlari)
F0 = P.f0_mhz
F1, F2, FS = 1150.0, 1400.0, 5.0

# ---- grafik stili (dataviz referans paleti) --------------------------------
BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2.0, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "legend.frameon": False, "figure.dpi": 130,
})


def band_edges(f, ok):
    """ok maskesinin f0'i iceren kesintisiz araligi."""
    i0 = int(np.argmin(abs(f - F0)))
    if not ok[i0]:
        return None
    a = i0
    while a > 0 and ok[a - 1]:
        a -= 1
    b = i0
    while b < len(f) - 1 and ok[b + 1]:
        b += 1
    return float(f[a]), float(f[b])


# =============================================================== 1) modeller
def write_models():
    write_nec(P, os.path.join(MOD, "cloverleaf3_1280_rhcp_sweep.nec"), F1, F2, FS, "horizon",
              title="3-lobe cloverleaf RHCP 1280 MHz - frequency sweep 1150-1400 MHz")
    write_nec(P, os.path.join(MOD, "cloverleaf3_1280_rhcp_3d.nec"), F0, F0, 0, "full",
              title="3-lobe cloverleaf RHCP 1280 MHz - 3D far field")
    lh = CloverParams(**{**P.to_dict(), "twist_deg": -P.twist_deg})
    write_nec(lh, os.path.join(MOD, "cloverleaf3_1280_lhcp_3d.nec"), F0, F0, 0, "full",
              title="3-lobe cloverleaf LHCP (mirror) 1280 MHz - 3D far field")
    cx = CloverParams(**{**P.to_dict(), "coax_len_mm": 150.0})
    write_nec(cx, os.path.join(MOD, "cloverleaf3_1280_rhcp_with_coax150.nec"), F1, F2, FS, "horizon",
              title="3-lobe cloverleaf RHCP + 150 mm coax shield (common-mode check)")


# ============================================================== 2) taramalar
def sweep(params, pattern="horizon"):
    res = simulate(params, F1, F2, FS, pattern=pattern)
    rows = []
    for r in res:
        th, ph, gt, gR, gL, ar = circular_components(r["pattern"])
        rows.append(dict(f=r["f"], R=r["Z"].real, X=r["Z"].imag, swr=swr(r["Z"]),
                         gR=float(np.mean(gR)), gL=float(np.mean(gL)), gT=float(np.mean(gt)),
                         ripple=float(gR.max() - gR.min()), ar=float(np.mean(ar))))
    return {k: np.array([row[k] for row in rows]) for k in rows[0]}


def full_pattern(params):
    r = simulate(params, F0, F0, 0, pattern="full")[0]
    return r, circular_components(r["pattern"])


# =============================================================== 3) grafikler
def plot_geometry():
    wires, R = build_wires(P)
    fig = plt.figure(figsize=(11, 4.2))
    views = [("Izometrik", 25, -60), ("Ustten (+z)", 90, -90), ("Yandan", 0, -90)]
    for k, (name, el, az) in enumerate(views):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        for tag, ns, a, b, rad in wires:
            col = INK if tag == 1 else [BLUE, ORANGE, AQUA][(tag - 2) % 3]
            ax.plot([a[0] * 1e3, b[0] * 1e3], [a[1] * 1e3, b[1] * 1e3], [a[2] * 1e3, b[2] * 1e3],
                    color=col, lw=2.2)
        ax.plot([0, 0], [0, 0], [0, -35], color=INK2, lw=5, alpha=.5)  # koaks (temsili)
        ax.set_box_aspect((1, 1, 1))
        lim = 90
        ax.set(xlim=(-lim, lim), ylim=(-lim, lim), zlim=(-lim, lim), xlabel="x [mm]",
               ylabel="y [mm]", zlabel="z [mm]")
        ax.view_init(el, az)
        if el == 90:
            ax.set_zticks([])
            ax.set_zlabel("")
        if el == 0:
            ax.set_yticks([])
            ax.set_ylabel("")
        ax.set_title(name)
        ax.tick_params(labelsize=7)
    fig.suptitle("3 yaprakli cloverleaf geometrisi (gri: koaks kablo, siyah: besleme)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "geometry.png"))
    plt.close(fig)


def plot_swr_z(s):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    a1.plot(s["f"], s["swr"], color=BLUE)
    a1.axhline(1.5, color=INK2, lw=1, ls="--")
    a1.axhline(2.0, color=INK2, lw=1, ls=":")
    a1.text(F1 + 3, 1.53, "SWR 1.5", color=INK2, fontsize=8)
    a1.text(F1 + 3, 2.03, "SWR 2.0", color=INK2, fontsize=8)
    a1.axvline(F0, color=GRID, lw=1)
    a1.set(title="SWR (Z0 = 50 ohm)", xlabel="Frekans [MHz]", ylabel="SWR", ylim=(1, 3))
    a2.plot(s["f"], s["R"], color=BLUE, label="R (direnc)")
    a2.plot(s["f"], s["X"], color=ORANGE, label="X (reaktans)")
    a2.axhline(50, color=INK2, lw=1, ls="--")
    a2.axhline(0, color=INK2, lw=0.8)
    a2.set(title="Giris empedansi", xlabel="Frekans [MHz]", ylabel="Empedans [ohm]")
    a2.text(F1 + 3, 52, "50 ohm", color=INK2, fontsize=8)
    a2.legend(loc="lower right")
    for ax in (a1, a2):
        ax.axvline(F0, color=GRID, lw=1)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "swr_impedance.png"))
    plt.close(fig)


def plot_gain_ar(s):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    a1.plot(s["f"], s["gR"], color=BLUE, label="RHCP (es-polar)")
    a1.plot(s["f"], s["gL"], color=ORANGE, label="LHCP (capraz-polar)")
    a1.set(title="Ufuk duzlemi kazanci (azimut ortalamasi)", xlabel="Frekans [MHz]",
           ylabel="Kazanc [dBic]")
    a1.legend(loc="lower right")
    a2.plot(s["f"], s["ar"], color=BLUE)
    a2.axhline(3, color=INK2, lw=1, ls="--")
    a2.text(F1 + 3, 3.1, "AR 3 dB", color=INK2, fontsize=8)
    a2.set(title="Eksenel oran - ufuk (theta = 90)", xlabel="Frekans [MHz]",
           ylabel="Eksenel oran [dB]", ylim=(0, max(8, float(s['ar'].max()) + 1)))
    for ax in (a1, a2):
        ax.axvline(F0, color=GRID, lw=1)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "gain_axialratio_vs_freq.png"))
    plt.close(fig)


def plot_patterns(fp):
    th, ph, gt, gR, gL, ar = fp
    fig = plt.figure(figsize=(11, 4.6))
    # Elevasyon kesiti: phi=0 ve phi=180 birlestirilmis tam daire
    ax = fig.add_subplot(1, 3, 1, projection="polar")
    m0, m1 = ph == 0, ph == 180
    ang = np.concatenate([np.radians(th[m0]), 2 * np.pi - np.radians(th[m1][::-1])])
    floor = -30
    for g, col, lab in ((gR, BLUE, "RHCP"), (gL, ORANGE, "LHCP")):
        val = np.concatenate([g[m0], g[m1][::-1]])
        ax.plot(ang, np.maximum(val, floor), color=col, label=lab)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_rlim(floor, 5)
    ax.set_rlabel_position(22)
    ax.set_title("Elevasyon kesiti (phi = 0/180)\n0 derece = anten ucu (+z)", pad=14)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.15, -0.15))
    # Azimut kesiti
    ax = fig.add_subplot(1, 3, 2, projection="polar")
    m = th == 90
    a_ = np.radians(np.append(ph[m], 360))
    for g, col, lab in ((gR, BLUE, "RHCP"), (gL, ORANGE, "LHCP")):
        ax.plot(a_, np.maximum(np.append(g[m], g[m][0]), floor), color=col, label=lab)
    ax.set_rlim(floor, 5)
    ax.set_rlabel_position(22)
    ax.set_title("Azimut kesiti (theta = 90, ufuk)", pad=14)
    # AR vs elevasyon
    ax = fig.add_subplot(1, 3, 3)
    ths = np.unique(th)
    ths = ths[(ths >= 10) & (ths <= 170)]
    arm = [np.mean(ar[th == t]) for t in ths]
    gRm = [np.mean(gR[th == t]) for t in ths]
    elev = 90 - ths
    ax.plot(elev, arm, color=BLUE, label="Eksenel oran [dB]")
    ax.axhline(3, color=INK2, lw=1, ls="--")
    ax.set(title="Yukselme acisina gore AR", xlabel="Yukselme acisi [derece]  (+ = antenin ucu yonu)",
           ylabel="Eksenel oran [dB]", ylim=(0, 8))
    ax2y = gRm  # ayni grafikte ikinci eksen yok; kazanc metin olarak verilir
    i = int(np.argmax(ax2y))
    ax.text(0.02, 0.95, f"Maks. RHCP: {max(ax2y):.1f} dBic @ {elev[i]:+.0f} derece",
            transform=ax.transAxes, color=INK2, fontsize=8, va="top")
    fig.suptitle(f"Isima deseni @ {F0:.0f} MHz (kazanc dBic)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(RES, "patterns_1280MHz.png"))
    plt.close(fig)


def plot_pattern_3d(fp):
    th, ph, gt, gR, gL, ar = fp
    T = np.unique(th)
    PH = np.unique(ph)
    G = np.zeros((len(T), len(PH)))
    for i, t in enumerate(T):
        for j, p_ in enumerate(PH):
            G[i, j] = gR[(th == t) & (ph == p_)][0]
    rng = 25
    r = np.maximum(G + rng, 0)
    TT, PP = np.meshgrid(np.radians(T), np.radians(PH), indexing="ij")
    X, Y, Z = r * np.sin(TT) * np.cos(PP), r * np.sin(TT) * np.sin(PP), r * np.cos(TT)
    fig = plt.figure(figsize=(6, 5.5))
    ax = fig.add_subplot(111, projection="3d")
    norm = plt.Normalize(-12, G.max())
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("seq", ["#cfe0f6", "#2a78d6", "#0d3f7a"])
    ax.plot_surface(X, Y, Z, facecolors=cmap(norm(G)), linewidth=0.2, edgecolor=(1, 1, 1, 0.25),
                    antialiased=True, shade=False, rstride=1, cstride=1)
    lim = rng + 2
    ax.set(xlim=(-lim, lim), ylim=(-lim, lim), zlim=(-lim, lim))
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    ax.view_init(18, -50)
    ax.set_title(f"RHCP 3D desen @ {F0:.0f} MHz (toroid / 'elma' formu)\n"
                 f"maks. {G.max():.1f} dBic, olcek: {-rng} dBic merkez", fontsize=10)
    fig.savefig(os.path.join(RES, "pattern3d_rhcp.png"))
    plt.close(fig)


def sensitivity():
    """Yapim toleranslari: tek parametre degisirken f0'daki SWR ve ufuk AR."""
    cases = {
        "lobe_len_mm": np.arange(235, 266, 2.5),
        "twist_deg": np.arange(46, 71, 2),
        "elev_deg": np.arange(-25, 26, 5),
        "wire_d_mm": np.array([1.0, 1.2, 1.5, 1.8, 2.0, 2.5]),
    }
    labels = {"lobe_len_mm": "Yaprak tel boyu [mm]", "twist_deg": "Bukulme acisi [derece]",
              "elev_deg": "Yaprak egimi [derece]", "wire_d_mm": "Tel capi [mm]"}
    out = {}
    fig, axes = plt.subplots(2, 4, figsize=(13, 5.6), sharex="col")
    for k, (name, vals) in enumerate(cases.items()):
        sw, arh, fres = [], [], []
        for v in vals:
            q = CloverParams(**{**P.to_dict(), name: float(v)})
            res = simulate(q, 1220, 1340, 10, pattern="horizon")
            f = np.array([r["f"] for r in res])
            s_ = np.array([swr(r["Z"]) for r in res])
            mid = res[int(np.argmin(abs(f - F0)))]
            sw.append(swr(mid["Z"]))
            arh.append(float(np.mean(circular_components(mid["pattern"])[5])))
            fres.append(float(f[np.argmin(s_)]))
        out[name] = dict(values=vals.tolist(), swr_f0=sw, ar_h=arh, f_min_swr=fres)
        a, b = axes[0, k], axes[1, k]
        a.plot(vals, sw, color=BLUE, marker="o", ms=4)
        a.axhline(1.5, color=INK2, lw=1, ls="--")
        a.axvline(getattr(P, name), color=GRID, lw=2)
        a.set(title=labels[name], ylabel="SWR @ 1280 MHz" if k == 0 else None, ylim=(1, 3))
        b.plot(vals, arh, color=ORANGE, marker="o", ms=4)
        b.axhline(3, color=INK2, lw=1, ls="--")
        b.axvline(getattr(P, name), color=GRID, lw=2)
        b.set(xlabel=labels[name], ylabel="Ufuk AR [dB]" if k == 0 else None, ylim=(0, 10))
    fig.suptitle("Tolerans / hassasiyet analizi (dikey gri cizgi = nominal tasarim)", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "sensitivity.png"))
    plt.close(fig)
    return out


def plot_coax(s, sc):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    a1.plot(s["f"], s["swr"], color=BLUE, label="Ideal besleme")
    a1.plot(sc["f"], sc["swr"], color=ORANGE, label="150 mm koaks blendaji ile")
    a1.set(title="SWR - koaks dis yuzey akimi etkisi", xlabel="Frekans [MHz]", ylabel="SWR",
           ylim=(1, 3))
    a1.legend(loc="upper center")
    a2.plot(s["f"], s["ar"], color=BLUE, label="Ideal besleme")
    a2.plot(sc["f"], sc["ar"], color=ORANGE, label="150 mm koaks blendaji ile")
    a2.set(title="Ufuk eksenel orani", xlabel="Frekans [MHz]", ylabel="AR [dB]", ylim=(0, 10))
    a2.legend(loc="upper center")
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "coax_effect.png"))
    plt.close(fig)


# ================================================== 4) 1:1 bukme sablonu PDF
def bending_template():
    R = solve_radius(P)
    g = P.gap_mm
    t0 = math.radians(P.theta0_deg)
    Rm = R * 1000
    # Yaprak duzleminde 2B koordinatlar (u: uzanma, w: duzlem ici dik)
    ths = np.linspace(t0, 2 * math.pi - t0, 200)
    U = Rm * (1 - np.cos(ths))
    W = Rm * np.sin(ths)
    leg = math.hypot(U[0], W[0] - 0)  # besleme merkezinden yay baslangicina
    arc_len = Rm * (2 * math.pi - 2 * t0)
    pts = _lobe_points(R, 0.0, P)
    total = _polyline_len(pts) * 1000
    info = dict(arc_radius_mm=Rm, arc_len_mm=arc_len, leg_len_mm=leg, total_mm=total,
                lobe_width_mm=2 * Rm * 1.0, lobe_reach_mm=float(U.max()),
                leg_angle_deg=math.degrees(math.atan2(W[0], U[0])) * 2)
    with PdfPages(os.path.join(DOC, "bukme_sablonu_1-1.pdf")) as pdf:
        fig = plt.figure(figsize=(210 / 25.4, 297 / 25.4))   # A4, 1:1 mm
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 210)
        ax.set_ylim(0, 297)
        ax.set_aspect("equal")
        ax.axis("off")
        ox, oy = 30, 170
        ax.plot(ox + U, oy + W, color=INK, lw=1.2)
        ax.plot([ox, ox + U[0]], [oy + g / 2, oy + W[0]], color=INK, lw=1.2)
        ax.plot([ox, ox + U[-1]], [oy - g / 2, oy + W[-1]], color=INK, lw=1.2)
        ax.plot([ox - 8, ox + 2 * Rm + 8], [oy, oy], color=INK2, lw=0.4, ls="-.")
        ax.plot(ox + Rm, oy, "+", color=INK2, ms=8)
        for x, y in ((U[0], W[0]), (U[-1], W[-1])):
            ax.plot(ox + x, oy + y, "o", ms=3, color=ORANGE)
        ax.text(ox - 3, oy + g / 2 + 2, "PIN (merkez iletken)", ha="right", fontsize=7)
        ax.text(ox - 3, oy - g / 2 - 4, "BLENDAJ (shield)", ha="right", fontsize=7)
        ax.text(ox + Rm, oy - 5, f"merkez, R = {Rm:.1f} mm", ha="center", fontsize=7, color=INK2)
        ax.text(105, 285, "3 yaprakli cloverleaf - 1:1 yaprak bukme sablonu", ha="center",
                fontsize=12, weight="bold")
        ax.text(105, 278, f"f0 = {F0:.0f} MHz  |  RHCP  |  tel capi {P.wire_d_mm} mm", ha="center",
                fontsize=9)
        lines = [
            f"Toplam tel boyu (bir yaprak, pin->blendaj): {total:.1f} mm  (+ lehim payi 2x3 mm)",
            f"Daire yayi yaricapi: {Rm:.1f} mm   Yay boyu: {arc_len:.1f} mm",
            f"Duz bacak boyu (besleme -> yay): {leg:.1f} mm  x 2",
            f"Bacaklar arasi aci: {info['leg_angle_deg']:.1f} derece",
            "Turuncu noktalar: duz bacagin bittigi / yayin basladigi yer (buradan bukun).",
            f"Uc yapragi ayni sablonla bukun, sonra her birini {P.twist_deg:.0f} derece",
            "ayni yone bukun (docs/02-yapim-kilavuzu.md).",
            "Yazdirirken 'Gercek boyut / %100' secin. Kontrol: asagidaki cizgi tam 100 mm olmali.",
        ]
        for i, t in enumerate(lines):
            ax.text(20, 105 - i * 7, t, fontsize=8.5)
        ax.plot([55, 155], [35, 35], color=INK, lw=1.5)
        ax.plot([55, 55], [33, 37], color=INK, lw=1.5)
        ax.plot([155, 155], [33, 37], color=INK, lw=1.5)
        ax.text(105, 28, "100 mm olcek kontrolu", ha="center", fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)
    return info


# ==================================================================== main
def main():
    write_models()
    plot_geometry()
    s = sweep(P)
    np.savetxt(os.path.join(RES, "sweep_rhcp.csv"),
               np.column_stack([s[k] for k in ("f", "R", "X", "swr", "gR", "gL", "ar", "ripple")]),
               delimiter=",", fmt="%.4f",
               header="f_MHz,R_ohm,X_ohm,SWR,G_RHCP_horizon_dBic,G_LHCP_horizon_dBic,AR_horizon_dB,"
                      "RHCP_azimuth_ripple_dB", comments="")
    plot_swr_z(s)
    plot_gain_ar(s)
    r0, fp = full_pattern(P)
    plot_patterns(fp)
    plot_pattern_3d(fp)
    sc = sweep(CloverParams(**{**P.to_dict(), "coax_len_mm": 150.0}))
    plot_coax(s, sc)
    sens = sensitivity()
    tmpl = bending_template()

    th, ph, gt, gR, gL, ar = fp
    i0 = int(np.argmin(abs(s["f"] - F0)))
    T = np.array([t for t in np.unique(th) if 10 <= t <= 170])
    gR_az = np.array([np.mean(gR[th == t]) for t in T])   # azimut ortalamali RHCP
    imax = int(np.argmax(gR_az))
    hz = th == 90
    summary = dict(
        params=P.to_dict(),
        geometry=tmpl,
        f0=dict(Z=[float(s["R"][i0]), float(s["X"][i0])], swr=float(s["swr"][i0]),
                gR_horizon=float(s["gR"][i0]), gL_horizon=float(s["gL"][i0]),
                ar_horizon=float(s["ar"][i0]), ripple_horizon=float(s["ripple"][i0]),
                gR_max_azavg=float(gR_az[imax]), gR_max_elev_deg=float(90 - T[imax]),
                gR_peak_any=float(gR.max()),
                elev_3db_deg=[float(90 - T[gR_az >= gR_az.max() - 3].max()),
                              float(90 - T[gR_az >= gR_az.max() - 3].min())],
                xpd_horizon=float(np.mean(gR[hz] - gL[hz])),
                ar_min_theta=float(min(np.mean(ar[th == t]) for t in np.unique(th) if 10 <= t <= 170))),
        bands=dict(swr15=band_edges(s["f"], s["swr"] <= 1.5), swr20=band_edges(s["f"], s["swr"] <= 2.0),
                   ar4=band_edges(s["f"], s["ar"] <= 4.0)),
        swr_min=dict(f=float(s["f"][np.argmin(s["swr"])]), swr=float(s["swr"].min())),
        coax150=dict(swr_f0=float(sc["swr"][i0]), ar_f0=float(sc["ar"][i0])),
        sensitivity=sens,
    )
    with open(os.path.join(RES, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=float)
    print(json.dumps({k: summary[k] for k in ("f0", "bands", "swr_min", "coax150", "geometry")},
                     indent=1, default=float))


if __name__ == "__main__":
    main()
