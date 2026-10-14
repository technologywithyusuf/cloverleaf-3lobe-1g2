# 4. 4nec2 ile Adım Adım Analiz

[4nec2](https://www.qsl.net/4nec2/) (Arie Voors), NEC2/NEC4 motorları için ücretsiz bir Windows arayüzüdür. Linux/macOS'ta Wine ile de çalışır. Bu depodaki `.nec` dosyaları 4nec2'nin doğrudan okuyabildiği standart NEC kart formatındadır.

> Menü adları ve kısayollar 4nec2 sürümüne göre küçük farklılık gösterebilir; aşağıdaki adımlar 5.8.x sürümüne göre yazılmıştır.

## Model dosyaları

| Dosya | Amaç |
|---|---|
| `cloverleaf3_1280_rhcp_sweep.nec` | 1150–1400 MHz, 5 MHz adımlı tarama + ufuk deseni → SWR, empedans, kazanç–frekans |
| `cloverleaf3_1280_rhcp_3d.nec` | 1280 MHz tam 3D desen (θ 0–180°, φ 0–355°, 5° adım) |
| `cloverleaf3_1280_lhcp_3d.nec` | Ayna (LHCP) versiyon — polarizasyon yönünün bükülmeyle değiştiğini görmek için |
| `cloverleaf3_1280_rhcp_with_coax150.nec` | Koaks blendajının dış yüzey akımı etkisi |

Dosyalardaki kartlar:

```
CM ...          açıklama satırları (tasarım parametreleri burada yazılı)
GW tag nseg x1 y1 z1 x2 y2 z2 r   düz tel parçaları (birim: metre)
GE 0            geometri sonu, serbest uzay
EK              genişletilmiş ince tel çekirdeği
EX 0 1 1 0 1 0  1 V gerilim kaynağı, tag 1 / segment 1 (besleme)
FR 0 N 0 0 f0 df   frekans (MHz)
RP 0 ...        ışıma deseni hesabı
```

## Adım 1 — Modeli aç ve geometriyi kontrol et

1. 4nec2'yi açın → **File ▸ Open 4nec2 in/out file** → `models/cloverleaf3_1280_rhcp_3d.nec`.
2. **Geometry** penceresini açın (F3). Üç gözyaşı biçimli yaprak ve ortadaki kısa besleme teli görünmelidir.
3. Geometri penceresinde besleme segmentinin (kaynak) tag 1 üzerinde olduğunu doğrulayın.
4. 4nec2'nin segmentasyon kontrolünü çalıştırın; segment uzunluğu/yarıçap ve komşu segment oranı uyarısı **olmamalı** (model λ/80 civarında segmentlidir).

## Adım 2 — 3D ışıma deseni (1280 MHz)

1. **Calculate ▸ Generate** (F7) → *Far Field pattern* seçin, çözünürlüğü 5° bırakın → **Generate**.
2. Ana pencerede empedansı kontrol edin: **Z ≈ 43.4 + j1.2 Ω, SWR ≈ 1.16 (50 Ω)**.
3. **Pattern** penceresinde (F4) elevasyon ve azimut kesitlerini inceleyin.
4. Polarizasyon bileşenini **Total** yerine **RHCP / LHCP** olarak değiştirin (Pattern penceresindeki polarizasyon seçimi). RHCP ufukta ~+0.4 dBic, LHCP ~−14 dBic olmalı.
5. **3D viewer** ile tam deseni görün: eksen yönünde sıfırlı, geniş bir toroid.

## Adım 3 — Frekans taraması

1. `models/cloverleaf3_1280_rhcp_sweep.nec` dosyasını açın.
2. **Generate** (F7) → *Frequency sweep* seçin. Başlangıç 1150, bitiş 1400, adım 5 MHz (dosyadaki FR kartı bu değerleri zaten içerir).
3. **Line chart** penceresinde SWR, R/X, kazanç ve F/B grafiklerini görün. Karşılaştırma için beklenen değerler:

| f [MHz] | SWR | Z [Ω] |
|---|---|---|
| 1220 | 1.49 | 39.3 − j14.4 |
| 1280 | 1.16 | 43.4 + j1.2 |
| 1350 | 1.47 | 49.7 + j19.2 |

   Tam liste: `results/sweep_rhcp.csv`.
4. **Smith chart** penceresinde empedans eğrisinin 50 Ω merkezinin çok yakınından geçtiğini görün.

## Adım 4 — Polarizasyon yönünü doğrula (LHCP karşılaştırması)

`cloverleaf3_1280_lhcp_3d.nec` dosyasını açıp Adım 2'yi tekrarlayın. Empedans aynı kalır, ancak RHCP ve LHCP kazançları **yer değiştirir**. Bu, polarizasyon yönünün yalnızca yaprakların bükülme yönüyle belirlendiğini gösterir.

## Adım 5 — Koaks etkisi

`cloverleaf3_1280_rhcp_with_coax150.nec` dosyasında ek bir tag, koaks blendajını z = 0'dan −150 mm'ye uzanan Ø5 mm'lik bir tel olarak temsil eder. Taramayı çalıştırıp eksenel oranı ideal modelle karşılaştırın: 1280 MHz'de ~3.7 dB → ~4.7 dB.

## Adım 6 — Kendi değişikliklerinizi yapmak

Model `.nec` dosyalarında açık koordinatlarla (GW kartları) tanımlanır; parametre değiştirmenin en güvenilir yolu Python üreticisidir:

```bash
# tools/cloverleaf.py içindeki CloverParams varsayılanlarını düzenleyin, ardından:
python3 tools/analyze.py      # models/ ve results/ yeniden üretilir
```

4nec2 içinde hızlı deneme için:

* **Frekans ölçekleme:** son GW kartından sonra `GS 0 0 k` kartı ekleyin (k = 1280 / yeni_f0). Tüm koordinatlar ve tel yarıçapı k ile çarpılır. Örnek: 1200 MHz için `GS 0 0 1.0667`. (Tel yarıçapının da ölçeklendiğini unutmayın; etki küçüktür.)
* **Malzeme kaybı:** `GE`'den sonra `LD 5 0 0 0 5.8E7` kartıyla bakır iletkenliği eklenebilir (tüm tag'lere uygulanır).
* **Zemin etkisi:** `GE 1` + `GN 2 0 0 0 13 0.005` ile ortalama zemin tanımlanabilir; bu durumda anteni zeminden yükseltmek için tüm geometriye `GM 0 0 0 0 0 0 0 1.5` (z = +1.5 m) eklenmelidir.

## NEC ↔ 4nec2 uyumluluk notu

Depodaki tüm sonuçlar `nec2c` (NEC-2 motorunun C çevirisi) ile hesaplandı. 4nec2 varsayılan olarak `nec2dxs` (NEC-2 double precision) motorunu kullanır; aynı giriş dosyasıyla sonuçlar sayısal yuvarlama düzeyinde (≪1 Ω) aynı olmalıdır.
