# 3. Simülasyon Yöntemi ve Sonuçlar

## Yöntem

* **Hesap motoru:** NEC2 (moment yöntemi, ince tel yaklaşımı). Analizler açık kaynak `nec2c` ile çalıştırıldı; `.nec` dosyaları 4nec2'de aynı motorla aynı sonucu verir.
* **Ortam:** serbest uzay (`GE 0`), kayıpsız iletken (bakırın 1.3 GHz'deki kaybı Ø1.8 mm tel için ihmal edilebilir düzeydedir).
* **Çekirdek:** genişletilmiş ince tel çekirdeği (`EK`) — kalın tel ve kısa segmentli bölgelerde (besleme düğümü) daha doğru.
* **Besleme:** koaks blendajı z = 0, merkez iletken z = 4 mm. Aralarındaki 4 mm'lik tel (tag 1) gerilim kaynağıdır (`EX 0 1 1 0 1 0`). Tüm pin bacakları üst düğüme, tüm blendaj bacakları alt düğüme bağlanır.
* **Dairesel polarizasyon ayrıştırması:** NEC çıktısındaki karmaşık E<sub>θ</sub> ve E<sub>φ</sub> değerlerinden IEEE tanımıyla
  E<sub>R</sub> = (E<sub>θ</sub> + jE<sub>φ</sub>)/√2, E<sub>L</sub> = (E<sub>θ</sub> − jE<sub>φ</sub>)/√2 hesaplandı; RHCP/LHCP kazancı (dBic) ve eksenel oran
  AR = 20·log<sub>10</sub>((|E<sub>R</sub>|+|E<sub>L</sub>|)/||E<sub>R</sub>|−|E<sub>L</sub>||) bunlardan türetildi. Sonuçlar NEC'in kendi "RIGHT/LEFT" polarizasyon etiketiyle çapraz kontrol edildi.

### Geometri modeli

Her yaprak: pin → düz bacak → daire yayı → düz bacak → blendaj. Yaprak düzlemi iki açıyla tanımlanır:

| Parametre | Anlamı | Nihai değer |
|---|---|---|
| `lobe_len_mm` | Bir yaprağın toplam tel boyu | 245.0 mm |
| `twist_deg` | Yaprak düzleminin kendi ekseni etrafında dönmesi (CP ve yönünü belirler) | 57° |
| `elev_deg` | Yaprak ekseninin yataydan eğimi | 0° |
| `theta0_deg` | Düz bacakların bittiği açı (gözyaşı formu) | 75° |
| `wire_d_mm` | Tel çapı | 1.8 mm |

### Segmentasyon yakınsama testi

NEC'te segment boyu λ/10'dan küçük olmalı ve besleme bölgesinde komşu segmentler benzer uzunlukta olmalıdır. Nihai modelde 319 segment kullanılır (yayda ~2 mm, bacaklarda ≤3 mm; λ/80 civarı).

| Bacak segmenti | Yay kırığı | Z @ 1280 MHz |
|---|---|---|
| 6 mm | 36 | 46.4 + j0.5 Ω |
| 4 mm | 36 | 44.2 + j0.9 Ω |
| **3 mm (kullanılan)** | **36** | **43.4 + j1.2 Ω** |
| 2 mm | 60 | 43.1 + j1.5 Ω |

3 mm ile 2 mm arasındaki fark < 0.5 Ω'dur; model yakınsamıştır.

> Not: Geliştirme sırasında ilk sürümde düz bacaklar tek segment (~50 mm ≈ λ/4.7) olarak modellenmişti; bu NEC kuralını ihlal ettiği için bacaklar bölündü ve optimizasyon baştan yapıldı.

## Optimizasyon

`tools/optimize.py` iki aşamalıdır:

1. **Izgara taraması** — 2310 kombinasyon: yaprak boyu 220–270 mm, eğim −30…+30°, bükülme 35–80°, θ0 ∈ {20, 40, 60}°. Her nokta 1220/1280/1340 MHz'de hesaplanır. Tüm sonuçlar: `results/optimization_grid.csv`.
2. **Nelder–Mead ince ayarı** — ızgaradaki en iyi 6 noktadan başlayarak 4 parametre birlikte.

Maliyet fonksiyonu:

```
maliyet = 4·max(0, SWR(f0) − 1.2) + 3·max(0, SWR_maks(1220–1340) − 1.5)
        + AR_ort(θ=60…100°, f0) + 0.3·AR_ort(bant kenarları)
        + 0.5·azimut_dalgalanması − 0.5·RHCP_kazanç_ort
```

Optimum (`results/best_params.json`): 245.4 mm, eğim −10.3°, bükülme 57.1°, θ0 = 75°. Yapım kolaylığı için **245 mm / 0° / 57° / 75°** değerlerine yuvarlandı; maliyet farkı ihmal edilebilir (ufuk AR 3.71 → 3.72 dB). θ0 tarama sınırına (75°) dayandı: daha uzun düz bacaklı, "gözyaşı" formu eksenel oranı iyileştiriyor.

## Sonuçlar (nihai tasarım)

### Empedans ve SWR — `results/swr_impedance.png`

| | |
|---|---|
| Z @ 1280 MHz | 43.4 + j1.2 Ω |
| SWR @ 1280 MHz | 1.16 |
| SWR ≤ 1.5 | 1220 – 1350 MHz |
| SWR ≤ 2.0 | 1175 – 1400+ MHz (tarama sınırı) |

Reaktans 1280 MHz civarında sıfırdan geçer; direnç 1150–1400 MHz boyunca 36–56 Ω arasında yavaşça artar. Ham veri: `results/sweep_rhcp.csv`.

### Kazanç ve eksenel oran — `results/gain_axialratio_vs_freq.png`

| | 1280 MHz | 1220–1340 MHz bandı |
|---|---|---|
| RHCP kazanç (ufuk, azimut ort.) | +0.42 dBic | +0.20 … +0.62 dBic |
| LHCP kazanç (ufuk) | −14.1 dBic | |
| Çapraz polarizasyon bastırma | 14.6 dB | |
| Eksenel oran (ufuk) | 3.7 dB | 3.2 … 4.3 dB |
| Azimut dalgalanması | 0.75 dB | |

Eksenel oran frekansla artar: alt bant kenarında (<1180 MHz) 3 dB'nin altına iner, 1340 MHz'de 4.3 dB olur. AR öncelikliyse bükülmeyi 60–62°'ye çıkarmak ufuk AR'yi ~3.4 dB'ye düşürür (SWR ~1.3'e çıkar).

### Işıma deseni — `results/patterns_1280MHz.png`, `results/pattern3d_rhcp.png`

* Eksen etrafında simetrik, geniş bir toroid ("elma"): yükselmede −3 dB huzme genişliği ~**120°** (±60°).
* Azimut ortalamalı RHCP maksimumu +0.46 dBic; ufuk ile ±20° arasında desen düzdür.
* Anten ekseni yönünde (±90°) derin sıfır vardır — cloverleaf'in tipik davranışı. Anteni yere dik (ucu gökyüzüne) monte edin.
* Eksenel oran ufukta en yüksek (3.7 dB), eksene doğru iyileşir (±60°'nin üstünde < 3 dB).

### Tolerans / hassasiyet — `results/sensitivity.png`

| Değişiklik | SWR @ 1280 | Ufuk AR | SWR minimumu |
|---|---|---|---|
| Nominal | 1.16 | 3.72 dB | 1280 MHz |
| Yaprak −5 mm (240) | 1.24 | 3.51 dB | 1310 MHz |
| Yaprak +5 mm (250) | 1.21 | 3.95 dB | 1260 MHz |
| Bükülme 52° | 1.06 | 4.21 dB | 1290 MHz |
| Bükülme 62° | 1.35 | 3.38 dB | 1280 MHz |
| Eğim ±10° | 1.19 | 3.70 dB | 1280 MHz |
| Tel Ø1.5 mm | 1.17 | 3.67 dB | 1280 MHz |
| Tel Ø2.0 mm | 1.15 | 3.75 dB | 1290 MHz |

Çıkarımlar:

* **Yaprak boyu** rezonansı belirler: ~**4 MHz/mm**. ±2.5 mm hata kabul edilebilir.
* **Bükülme açısı** SWR–AR dengesini belirler; rezonans frekansını neredeyse değiştirmez. ±4° kabul edilebilir.
* **Eğim** neredeyse etkisizdir (±15°'ye kadar) — yapımda en toleranslı parametre.
* Tel çapı Ø1.5–2.0 mm arasında serbestçe seçilebilir.

### Koaks blendajı etkisi — `results/coax_effect.png`

Koaks blendajı 150 mm'lik bir tel (Ø5 mm) olarak modele eklendiğinde:

| | İdeal besleme | 150 mm koaks ile |
|---|---|---|
| SWR @ 1280 MHz | 1.16 | 1.23 |
| Ufuk AR @ 1280 MHz | 3.7 dB | 4.7 dB |
| Bant içi en kötü AR | 4.3 dB | 5.2 dB (1325 MHz) |

Koaks dış yüzeyindeki ortak mod akımı SWR'yi az, polarizasyon saflığını belirgin bozar. Yapım kılavuzundaki **sleeve balun** önerisi bu yüzden vardır.

## Sınırlamalar

* İdeal, kayıpsız model; radom, lehim kütlesi, koaks dielektriği ve montaj elemanları modelde yok.
* NEC ince tel modeli, çok telin birleştiği besleme düğümünü yaklaşık olarak modeller; gerçek empedans birkaç ohm farklı olabilir.
* Sonuçlar mutlaka **NanoVNA ölçümü** ile doğrulanmalı, rezonans yaprak boyuyla ince ayarlanmalıdır.
