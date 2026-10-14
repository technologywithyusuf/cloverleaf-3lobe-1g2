# 2. Yapım Kılavuzu

Hedef: 1280 MHz merkezli, RHCP, 3 yapraklı cloverleaf. Tüm ölçüler simülasyondan gelir (`results/summary.json`).

## Malzeme

| Malzeme | Not |
|---|---|
| Bakır tel, Ø1.8 mm, ~80 cm | 2.5 mm² tek damarlı NYA tesisat kablosu (izolasyonu soyulur). Ø1.5–2.0 mm da olur; ayar hassasiyet analizine göre değişir. |
| Koaks kablo | RG-402 semi-rigid (en sağlam) veya RG-316 / RG-174 |
| Konnektör | Video verici/alıcınıza uygun SMA / RP-SMA (erkek/dişi kontrol edin!) |
| Ortak mod bastırma | Bakır boru veya bakır folyo (sleeve balun için) ya da GHz bandı için üretilmiş ferrit kılıf (bkz. 6. adım) |
| Bükme aparatı | ~75–80 mm çaplı silindir (kavanoz, PVC boru), 33° kama (karton ya da 3D baskı) |
| Diğer | Havya, akı (flux), ısıyla daralan makaron, sıcak silikon, cetvel/kumpas |
| Test | NanoVNA (veya benzeri anten analizörü) |

## 1. Şablonu yazdır

[`bukme_sablonu_1-1.pdf`](bukme_sablonu_1-1.pdf) dosyasını yazdırırken **"Gerçek boyut / %100"** seçin. Sayfadaki ölçek çizgisinin tam **100 mm** olduğunu cetvelle kontrol edin.

## 2. Teli kes ve hazırla

1. Üç adet **251 mm** tel kesin (245 mm yaprak + 2 × 3 mm lehim payı).
2. Teli bir ucundan mengeneye sabitleyip diğer ucundan pense ile hafifçe çekerek düzleştirin.
3. İzolasyonu tamamen soyun; uçları zımparalayıp kalaylayın.
4. Her teli işaretleyin: `3 mm | 49.2 mm | 148.2 mm (yay) | 49.2 mm | 3 mm`.

## 3. Yaprakları bük (gözyaşı formu)

1. Ortadaki 148.2 mm'lik kısmı **~75 mm çaplı** silindir etrafında bükün (bakır geri esner; hedef çap 80.9 mm, yani R = 40.4 mm).
2. İşaretli noktalardan (şablondaki turuncu noktalar) bacakları içeri doğru bükün; iki bacak arasındaki açı **105°** olmalı.
3. Her yaprağı şablonun üzerine koyup karşılaştırın. Üç yaprak birbirinin **aynısı** olmalıdır — simetri, eksenel orandan ve omni desenden daha önemlidir.
4. Bacakların uçları (pin ve blendaj tarafı) arasında ~4 mm boşluk kalmalı; pin tarafındaki uç ~4 mm daha yukarıda olacak.

## 4. Bükülme açısı (twist) — polarizasyonu belirleyen adım

Her yaprağın düzlemi, yaprağın kendi uzanma ekseni etrafında **57°** döndürülür. Pratikte:

* Yaprağı **yatay** masaya koyun, uzanma ekseni merkezden dışarı baksın.
* **Pin'e bağlanacak bacağı** (üst bacak) **kaldırarak** yaprak düzlemini yataydan **33°** yükseltin (90° − 57° = 33°). Blendaj bacağı aşağıda kalır.
* **RHCP için:** anteni ucundan (yukarıdan, koaks size uzak) bakarak görün — her yaprağın **pin bacağı, yaprağın saat yönünün TERSİ tarafında** olmalı. Üç yaprak da **aynı yöne** bükülür; yukarıdan bakınca pervane kanatlarına benzer.
* **LHCP için** her şeyin aynası: pin bacağı saat yönü tarafında.

`results/geometry.png` (üstten görünüş) yapılacak antenin birebir görünüşüdür; yapım sırasında yanınızda bulundurun.

> 33° kama: karton/kontrplak üzerine 33° açılı bir üçgen kesin veya 3D yazıcıdan basın. Hassasiyet analizine göre ±4° hata SWR'yi 1.3'ün altında tutar.

## 5. Koaksı hazırla ve lehimle

1. Koaks dış kılıfını ucundan **~6 mm** soyun; örgüyü/blendajı geriye düzgünce toplayıp kalaylayın (RG-402'de dış iletken zaten borudur).
2. Dielektriği blendajın **~4 mm** üstünde kesin; merkez iletken (pin) dielektrikten **~1–2 mm** çıksın.
3. Önce **3 blendaj bacağını** blendaja 120° aralıklarla lehimleyin (en zor kısım; bir aparat veya sıcak silikonla geçici sabitleme yardımcı olur).
4. Sonra **3 pin bacağını** pin ucunda birleştirip lehimleyin. Dielektriği eritmemek için kısa ve sıcak lehim yapın.
5. Yaprakları azimutta 120° aralığa, eğimleri 33°'ye son kez ayarlayın.

## 6. Koaks dış yüzey akımı (ortak mod) — önemli

Simülasyon (`results/coax_effect.png`), koaks blendajının dış yüzeyinde akan akımın 150 mm'lik bir kabloda bile eksenel oranı **3.7 dB'den 4.7–5.2 dB'ye** çıkardığını gösteriyor (SWR'ye etkisi küçük). Bu yüzden:

* **Sleeve (bazuka) balun önerilir:** besleme noktasının hemen altına, koaksın dış kılıfı üzerine **~55 mm** boyunda bakır boru/folyo geçirin; **alt ucu** blendaja lehimlenir, **üst ucu** (antene bakan taraf) açık bırakılır. (λ/4 = 58.6 mm; kılıf dielektriği yüzünden biraz kısa tutulur.)
* Alternatif: 1.3 GHz'de etkili ferrit (ör. "GHz-band" ferrit kılıf / EMI bastırma tüpü). Yaygın 43 karışım ferritler bu frekansta zayıf kalır.
* Koaks kablo antenin ekseni boyunca düz insin; yaprakların yakınından geçmesin.

## 7. Ölçüm ve ince ayar (NanoVNA)

1. NanoVNA'yı 1100–1450 MHz için kalibre edin (SOL kalibrasyonu, kullanacağınız kablonun ucunda).
2. S11 / SWR ölçün. Hedef: 1280 MHz civarında minimum, 1220–1350 MHz arası SWR ≤ 1.5.
3. **Frekans kayması:** simülasyona göre yaprak boyunda **1 mm ≈ 4 MHz**.
   * Minimum SWR **düşük** frekanstaysa yapraklar uzun → yay kısmını hafifçe sıkıştırın / yaprakları eşit kısaltın.
   * Minimum SWR **yüksek** frekanstaysa yapraklar kısa → yayı hafifçe açın.
   Değişikliği üç yaprağa **eşit** uygulayın.
4. **Uyum (SWR minimum değeri) kötüyse** bükülme açısıyla oynayın: açıyı azaltmak (yaprakları dikleştirmek) direnci yükseltir, artırmak (yataylaştırmak) düşürür. 52–56° aralığı en iyi SWR'yi, 60–64° en iyi eksenel oranı verir.
5. Radom (koruyucu kap) veya sıcak silikon eklendikten sonra rezonans **%1–3 aşağı** kayar; son ölçümü kaplamadan sonra yapın veya biraz kısa bırakın.

## 8. Polarizasyon kontrolü

* Bilinen bir RHCP anteni olan vericiyle sinyal gücünü (RSSI) karşılaştırın; ardından alıcıdaki anteni kendi ekseni etrafında 360° çevirin — sinyal yaklaşık sabit kalmalı (±2 dB).
* Yanlış yönde (LHCP) yapılmış bir antende RSSI 10–20 dB daha düşük olur.

## 9. Koruma

Yapraklar büyüktür ve kolay eğilir. Önerilen seçenekler: ince PETG/PLA'dan 3D baskı radom, köpük top içine gömme veya yapraklar arasına sıcak silikon damlaları. Yaprakların açısını bozmayacak, ince duvarlı (≤1.5 mm) malzeme kullanın.

## Hata kontrol listesi

| Belirti | Olası neden |
|---|---|
| SWR her yerde yüksek, belirgin dip yok | Kısa devre (pin–blendaj teması), soğuk lehim |
| Dip var ama 1.5'in üstünde | Bükülme açısı fazla/az, yapraklar simetrik değil |
| Dip çok düşük frekansta | Yapraklar uzun veya radom/silikon etkisi |
| RSSI anten dönünce çok değişiyor | Eksenel oran kötü: bükülme açıları farklı, ortak mod akımı |
| Menzil beklenenden çok düşük | Polarizasyon yönü yanlış (RHCP/LHCP karışmış) |
