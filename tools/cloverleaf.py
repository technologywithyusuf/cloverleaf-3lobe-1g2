"""
3 yaprakli (3-lobe) cloverleaf anten - parametrik NEC2 modeli.

Bu modul:
  * Yaprak geometrisini (daire yayi + besleme baglantilari) uretir,
  * 4nec2 ile dogrudan acilabilen .nec dosyasi yazar,
  * nec2c ile simulasyonu calistirir ve ciktiyi ayristirir
    (empedans, SWR, RHCP/LHCP kazanc, eksenel oran).

Koordinat sistemi (birimler: metre)
  z ekseni = koaksiyel kablo ekseni (anten dik tutuldugunda yukari).
  Besleme: koaks blendaji (shield) z=0'da, merkez iletken (pin) z=+gap'te.
  Her yaprak pin'den cikar, bir halka cizer ve blendaja geri doner.

Yaprak geometrisi
  Her yaprak, besleme noktasindan gecen bir dairedir. Dairenin duzlemi iki
  aciyla tanimlanir:
    beta  (elev)  : yapragin uzanma yonunun yataydan yukari egimi
    alpha (twist) : halka duzleminin kendi ekseni etrafinda bukulmesi.
                    Dairesel polarizasyonu ve yonunu (RHCP/LHCP) bu aci belirler.
  Yapraklar azimutta 360/N derece aralikla dizilir.
"""

from __future__ import annotations

import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict

import numpy as np

C0 = 299_792_458.0


@dataclass
class CloverParams:
    f0_mhz: float = 1280.0          # tasarim frekansi
    n_lobes: int = 3                # yaprak sayisi
    # Varsayilanlar = optimize edilmis nihai tasarim (bkz. docs/03-simulasyon-sonuclari.md)
    lobe_len_mm: float = 245.0      # bir yapragin TOPLAM tel boyu (pin -> halka -> blendaj)
    elev_deg: float = 0.0           # beta: yaprak egimi (yataydan yukari)
    twist_deg: float = 57.0         # alpha: halka duzlemi bukulmesi (+ = RHCP, - = LHCP)
    wire_d_mm: float = 1.8          # tel capi (2.5 mm2 NYA bakir ~1.8 mm)
    gap_mm: float = 4.0             # pin-blendaj arasi besleme boslugu
    theta0_deg: float = 75.0        # duz bacaklarin bittigi/yayin basladigi aci (gozyasi formu)
    seg_per_lobe: int = 36          # yay icin kirik cizgi (segment) sayisi
    max_seg_mm: float = 3.0         # duz bacaklarda azami segment boyu (~lambda/80, yakinsama testi ile)
    coax_len_mm: float = 0.0        # >0 ise blendaj bir tel olarak modellenir (common-mode etkisi)

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------- geometri --
def _lobe_basis(phi, beta, alpha):
    """Yaprak i icin (u, w) birim vektorleri."""
    r_hat = np.array([math.cos(phi), math.sin(phi), 0.0])
    t_hat = np.array([-math.sin(phi), math.cos(phi), 0.0])
    z_hat = np.array([0.0, 0.0, 1.0])
    u = math.cos(beta) * r_hat + math.sin(beta) * z_hat        # uzanma yonu
    n = -math.sin(beta) * r_hat + math.cos(beta) * z_hat       # u'ya dik, dusey duzlemde
    w = math.cos(alpha) * n + math.sin(alpha) * t_hat          # halka duzleminin 2. ekseni
    return u, w


def _lobe_points(R, phi, p: CloverParams):
    """Tek bir yapragin kose noktalari (pin -> yay -> blendaj)."""
    g = p.gap_mm / 1000
    beta, alpha = math.radians(p.elev_deg), math.radians(p.twist_deg)
    th0 = math.radians(p.theta0_deg)
    u, w = _lobe_basis(phi, beta, alpha)
    P0 = np.array([0.0, 0.0, g / 2])
    ths = np.linspace(th0, 2 * math.pi - th0, p.seg_per_lobe + 1)
    arc = [P0 + R * (1 - math.cos(t)) * u + R * math.sin(t) * w for t in ths]
    pin = np.array([0.0, 0.0, g])
    shield = np.array([0.0, 0.0, 0.0])
    # yayin w>0 tarafi (yukari) pin'e, w<0 tarafi blendaja baglanir
    if w[2] < 0:
        arc = arc[::-1]
    return [pin] + arc + [shield]


def _polyline_len(pts):
    return sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1))


def solve_radius(p: CloverParams):
    """Istenen toplam yaprak boyunu veren daire yaricapini bul (bisection)."""
    target = p.lobe_len_mm / 1000
    lo, hi = 1e-3, target / 2
    for _ in range(60):
        mid = (lo + hi) / 2
        if _polyline_len(_lobe_points(mid, 0.0, p)) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def build_wires(p: CloverParams):
    """NEC GW kartlari icin tel listesi: (tag, nseg, P1, P2, radius)."""
    rad = p.wire_d_mm / 2000
    R = solve_radius(p)
    wires = []
    tag = 1
    g = p.gap_mm / 1000
    # Tag 1: besleme teli (blendaj -> pin), kaynak burada
    wires.append((tag, 1, np.array([0, 0, 0.0]), np.array([0, 0, g]), rad))
    tag += 1
    for i in range(p.n_lobes):
        phi = 2 * math.pi * i / p.n_lobes
        pts = _lobe_points(R, phi, p)
        for k in range(len(pts) - 1):
            # NEC kurali: segment boyu < lambda/10; burada ~lambda/40 hedeflenir
            seg_len = np.linalg.norm(pts[k + 1] - pts[k])
            ns = max(1, int(math.ceil(seg_len / (p.max_seg_mm / 1000))))
            wires.append((tag, ns, pts[k], pts[k + 1], rad))
        tag += 1  # her yaprak ayri tag numarasi
    if p.coax_len_mm > 0:
        L = p.coax_len_mm / 1000
        nseg = max(3, int(round(L / 0.008)))
        wires.append((tag, nseg, np.array([0, 0, 0.0]), np.array([0, 0, -L]), 2.5e-3))
    return wires, R


# ------------------------------------------------------------- NEC yazici --
def write_nec(p: CloverParams, path: str, f_start=1150.0, f_stop=1400.0, f_step=5.0,
              pattern="full", title=None):
    """4nec2 uyumlu .nec dosyasi yaz.

    pattern: "full"   -> 3D desen (theta 0..180, phi 0..355, 5 derece)
             "band"   -> theta 60..100 (ufuk civari), optimizasyon icin
             "horizon"-> sadece ufuk duzlemi
             "none"   -> yalnizca empedans taramasi
    """
    wires, R = build_wires(p)
    lines = []
    title = title or f"{p.n_lobes}-lobe cloverleaf RHCP, f0={p.f0_mhz:.0f} MHz"
    lines.append(f"CM {title}")
    lines.append(f"CM lobe_len={p.lobe_len_mm:.2f} mm  elev={p.elev_deg:.1f} deg  twist={p.twist_deg:.1f} deg")
    lines.append(f"CM wire_d={p.wire_d_mm:.2f} mm  gap={p.gap_mm:.1f} mm  arc_radius={R*1000:.2f} mm")
    lines.append("CM Units: meters. Feed = tag 1 seg 1 (shield z=0 -> center pin z=gap).")
    lines.append("CM Generated by tools/cloverleaf.py - edit parameters there and regenerate.")
    lines.append("CE")
    for tag, ns, a, b, rad in wires:
        lines.append(
            f"GW {tag} {ns} {a[0]:.6f} {a[1]:.6f} {a[2]:.6f} {b[0]:.6f} {b[1]:.6f} {b[2]:.6f} {rad:.6f}"
        )
    lines.append("GE 0")
    lines.append("EK")
    lines.append("EX 0 1 1 0 1 0")
    nf = int(round((f_stop - f_start) / f_step)) + 1 if f_step > 0 else 1
    lines.append(f"FR 0 {nf} 0 0 {f_start:.3f} {f_step:.3f}")
    if pattern == "full":
        lines.append("RP 0 37 72 1000 0 0 5 5")
    elif pattern == "band":
        lines.append("RP 0 5 24 1000 60 0 10 15")
    elif pattern == "horizon":
        lines.append("RP 0 1 72 1000 90 0 0 5")
    lines.append("EN")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------- calistir/oku --
_num = r"[-+]?\d+\.\d+E[-+]\d+"


def run_nec(nec_path: str, out_path: str | None = None) -> str:
    out_path = out_path or os.path.splitext(nec_path)[0] + ".out"
    if os.path.exists(out_path):
        os.remove(out_path)
    # nec2c bazen basarili calismada da 0 disi kod dondurur; ciktinin varligini kontrol et
    subprocess.run(["nec2c", f"-i{nec_path}", f"-o{out_path}"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(out_path):
        raise RuntimeError(f"nec2c cikti uretmedi: {nec_path}")
    with open(out_path) as fh:
        return fh.read()


def parse_output(text: str):
    """Frekans bloklari: [{'f':MHz, 'Z':complex, 'pattern':ndarray}]"""
    blocks = re.split(r"-+\s*FREQUENCY\s*-+", text)[1:]
    res = []
    for b in blocks:
        mf = re.search(r"FREQUENCY\s*[:=]\s*([\d.E+-]+)\s*MHZ", b, re.I)
        if not mf:
            continue
        f = float(mf.group(1))
        mz = re.search(r"ANTENNA INPUT PARAMETERS.*?\n(?:.*\n){2}\s*\d+\s+\d+\s+"
                       rf"({_num})\s+({_num})\s+({_num})\s+({_num})\s+({_num})\s+({_num})", b)
        Z = complex(float(mz.group(5)), float(mz.group(6))) if mz else None
        pat = []
        mp = b.find("RADIATION PATTERNS")
        if mp >= 0:
            for line in b[mp:].splitlines()[5:]:
                tok = line.split()
                if len(tok) < 12:
                    if pat:
                        break
                    continue
                try:
                    th, ph = float(tok[0]), float(tok[1])
                    gt = float(tok[4])
                    em, ep = float(tok[8]), float(tok[9])
                    fm, fp = float(tok[10]), float(tok[11])
                except ValueError:
                    if pat:
                        break
                    continue
                pat.append((th, ph, gt, em, ep, fm, fp))
        res.append({"f": f, "Z": Z, "pattern": np.array(pat) if pat else None})
    return res


def circular_components(pat):
    """RHCP/LHCP kazanc (dBic) ve eksenel oran (dB). IEEE tanimi, e^{jwt}."""
    th, ph, gt, em, ep, fm, fp = pat.T
    Et = em * np.exp(1j * np.radians(ep))
    Ep = fm * np.exp(1j * np.radians(fp))
    ER = (Et + 1j * Ep) / math.sqrt(2)
    EL = (Et - 1j * Ep) / math.sqrt(2)
    pr, pl = np.abs(ER) ** 2, np.abs(EL) ** 2
    tot = pr + pl + 1e-30
    g_lin = 10 ** (gt / 10)
    gR = 10 * np.log10(np.maximum(g_lin * pr / tot, 1e-12))
    gL = 10 * np.log10(np.maximum(g_lin * pl / tot, 1e-12))
    a, b = np.abs(ER), np.abs(EL)
    ar = 20 * np.log10((a + b) / np.maximum(np.abs(a - b), 1e-12))
    return th, ph, gt, gR, gL, ar


def swr(Z, z0=50.0):
    g = abs((Z - z0) / (Z + z0))
    return (1 + g) / (1 - g) if g < 1 else float("inf")


def simulate(p: CloverParams, f_start=None, f_stop=None, f_step=5.0, pattern="horizon",
             keep=None):
    f_start = p.f0_mhz if f_start is None else f_start
    f_stop = f_start if f_stop is None else f_stop
    with tempfile.TemporaryDirectory() as td:
        nec = keep or os.path.join(td, "m.nec")
        write_nec(p, nec, f_start, f_stop, f_step if f_stop > f_start else 0, pattern)
        return parse_output(run_nec(nec, os.path.join(td, "m.out")))
