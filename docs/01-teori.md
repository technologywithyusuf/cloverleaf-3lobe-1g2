# 1. Teori — Cloverleaf anten nasıl çalışır?

## Neden dairesel polarizasyon?

FPV'de verici (uçak/drone) sürekli yatar, döner ve takla atar. Doğrusal polarizasyonlu iki anten birbirine dik geldiğinde sinyal 20 dB'den fazla düşebilir. Dairesel polarizasyonda (CP) alan vektörü her periyotta bir tam tur döner; bu yüzden antenler arasındaki dönme açısı bağlantıyı neredeyse etkilemez.

İkinci büyük fayda **çok yollu yansımaların bastırılmasıdır**. RHCP bir dalga düz bir yüzeyden (bina, zemin) yansıdığında yön değiştirip büyük ölçüde LHCP'ye dönüşür. RHCP alıcı anten bu yansımayı çapraz polarizasyon bastırması kadar (bu tasarımda ~14 dB) zayıflatır; görüntüdeki "yırtılma" ve titreme azalır.

> Verici ve alıcıda **aynı yönde** (ikisi de RHCP) anten kullanılmalıdır. RHCP–LHCP eşleşmesi 15–20 dB kayıp demektir.

## Cloverleaf'in çalışma prensibi

Cloverleaf, besleme noktası etrafına eşit açılarla dizilmiş, birbirinin aynısı **eğik halkalardan (yaprak)** oluşur. Her yaprak yaklaşık **1 dalga boyu** (λ) uzunluğunda bir tel halkadır:

* Her yaprak koaksın **merkez iletkeninden (pin)** çıkar, bir halka çizer ve **blendaja (shield)** geri döner. Böylece tüm yapraklar beslemeye paralel bağlanır.
* 1λ halkada akım dağılımı, besleme noktası ve karşı uçta maksimum olan bir duran dalgadır. Tek başına bir halka, düzlemine dik yönde **doğrusal** polarizasyonlu ışır.
* Yapraklar kendi eksenleri etrafında aynı yönde **bükülür (twist)**. Bükülme, her halkanın ürettiği alanın hem yatay hem dikey bileşene sahip olmasını sağlar; halkaların uzaydaki konumundan gelen faz farkıyla birleşince bu iki bileşen arasında ~90° faz farkı oluşur → **dairesel polarizasyon**.
* Bükülme yönü polarizasyon yönünü belirler: bu modelde pozitif açı RHCP, negatif açı LHCP üretir.
* Simetrik dizilim sayesinde toplam desen, eksen etrafında neredeyse dairesel (omni) bir **toroid** ("elma" formu) olur.

## Neden 3 yaprak?

| | 3 yaprak | 4 yaprak |
|---|---|---|
| Yapım | Daha kolay, daha az lehim | Daha zor, yapraklar arası mesafe dar |
| Boyut | Daha kompakt | Daha büyük |
| Azimut dalgalanması | ~0.75 dB (bu tasarım) | Genellikle daha düşük |
| Eksenel oran | Biraz daha yüksek (~3–4 dB) | Daha iyi (~2–3 dB) |
| Empedans | 50 Ω'a doğrudan uygun | 50 Ω'a doğrudan uygun |

Paralel bağlı N yaprakta empedans kabaca tek yaprağın 1/N'idir; yaprak boyu ve bükülme açısı ayarlanarak 3 yaprakta da 50 Ω'a doğrudan uyum sağlanabilir (balun/eşleştirme devresi gerekmez).

## 1.2–1.3 GHz bandı

1.2/1.3 GHz analog video, 5.8 GHz'e göre engelleri ve ağaçları çok daha iyi geçer; bedeli büyük antenlerdir. Bu bölgede kullanılan kanallar tipik olarak 1080–1360 MHz arasına yayılır; tasarım merkezi bu yüzden **1280 MHz** seçildi ve SWR ≤ 1.5 bandı 1220–1350 MHz'i kapsar.

> **Yasal not:** 1.2–1.3 GHz bölgesi pek çok ülkede GNSS (GPS L2, Galileo E6, GLONASS G2) ve amatör radyo ile paylaşılır. Bu bantta yayın yapmadan önce ülkenizdeki frekans tahsisini ve gerekli lisansı (Türkiye'de BTK düzenlemeleri, amatör telsizcilik belgesi) kontrol edin. Bu bant, drone'daki GPS alıcısını da bozabilir.

## Dalga boyu referansı

| Frekans | λ (serbest uzay) |
|---|---|
| 1200 MHz | 249.8 mm |
| 1280 MHz | 234.2 mm |
| 1300 MHz | 230.6 mm |

Optimize edilmiş yaprak boyu 245 mm ≈ **1.05 λ**'dır; halkanın bükülmüş geometrisi ve yapraklar arası kuplaj nedeniyle 1λ'dan biraz uzundur.
