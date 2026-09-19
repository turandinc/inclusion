# Port kılavuzu

Motoru başka bir dile taşımak için gereken her şey. `src/numeroloji/` bir
**referans uygulamadır**, kutsal değildir; asıl sözleşme bu belge ile
`tests/uyumluluk-vektorleri.json` dosyasıdır.

Portunuz 24 vektörün tamamını geçiyorsa doğrudur.

---

## Ne taşınır, ne taşınmaz

| Taşınır | Taşınmaz |
|---|---|
| Hesaplama (bu belge) | `data/*.json` — olduğu gibi okunur |
| Metin seçim kuralları | Metinlerin kendisi |

`data/` saf JSON'dur ve hiçbir dile bağlı değildir. Portun işi: doğru sayıları
üretmek ve doğru metin anahtarını seçmek.

---

## 1. Normalizasyon

Girdi: ham ad dizesi. Çıktı: yalnızca `A–Z` içeren dize.

1. **Türkçe'ye duyarlı büyüt.** `i → İ`, `ı → I`, sonra genel büyütme.
   Sıralama önemli: önce bu iki harf, sonra `toUpperCase()`. Aksi halde
   `i → I` olur ve sayı değişir.
2. Her karakter için sırayla:
   - `harf-haritasi.json → semalar.<etkin>.katlama` içindeyse karşılığını yaz
     (`Ç→C`, `Ğ→G`, `İ→I`, `I→I`, `Ö→O`, `Ş→S`, `Ü→U`, `Â→A`, `Î→I`, `Û→U`,
     `Ê→E`, `Ô→O`).
   - `harita` içindeyse olduğu gibi yaz.
   - Değilse **NFD ile ayrıştır**, birleşen aksanları at, tabanı yukarıdaki iki
     testten geçir.
   - Hiçbiri tutmuyorsa **sessizce at** (boşluk, tire, kesme, rakam, noktalama).

> Tire ve kesme atılır ama kelimeler **birleştirilmez** — `Al-i` → `ALI`,
> harfler zaten ardışıktır. Boşluklar tablo için anlamsızdır.

**Harf → sayı:** `harita[harf]`. Türkçe'de `Q W X` da haritada vardır; yabancı
kökenli adlarda çıkabilir.

**Sesli/sessiz** (yalnızca Ruh Arzusu ve Kişilik için): katlama **sonrası**
`A E I O U` sesli sayılır. **Y her zaman sessizdir.**

---

## 2. İndirgeme

```
indirge(sayilar, usta_koru = true):
    toplam = sum(sayilar)
    while toplam > 9:
        if usta_koru and toplam in {11, 22, 33}: return toplam
        toplam = basamaklarinin_toplami(toplam)
    return toplam
```

Usta sayı kontrolü **döngünün içindedir** — ara toplam 11/22/33 olduğunda
durur. `indirge([5,6])` → `11`, `indirge([9,9,2])` → `2` (20 → 2).

---

## 3. Çekirdek sayılar

Tarih `YYYY-MM-DD`.

| Sayı | Hesap |
|---|---|
| Yaşam Yolu | `YYYYAAGG` dizesinin **tüm rakamları** indirgenir (`1990-03-17` → 1+9+9+0+0+3+1+7) |
| İfade (Kader) | Tam doğum adının **tüm harflerinin** sayıları indirgenir |
| Ruh Arzusu | Yalnızca seslilerin sayıları indirgenir |
| Kişilik | Yalnızca sessizlerin sayıları indirgenir |
| Doğum Günü | Gün sayısının basamakları indirgenir (`17` → 8) |
| Doğum Ayı | Ay sayısının basamakları indirgenir (`10` → 1) |
| Olgunluk | `indirge([yasam_yolu, ifade])` |

Hepsinde `usta_koru = true`.

**Telafi kümesi:** yedi çekirdek sayının kümesi; her biri 11/22/33 ise
indirgenmiş hâli de (`usta_koru=false`) kümeye eklenir. `telafi_eder_mi(n)`
= `n ∈ küme`.

---

## 4. Frekanslar ve sınıf

`L` = normalize edilmiş addaki harf sayısı. `f[n]` = sayısı `n` olan harflerin
adedi.

Her `n ∈ 1..9` için:

```
p       = taban-oranlar.json → harf_olasiligi[n]
beklenen = L * p
sapma    = sqrt(L * p * (1 - p))          // 0 ise 1e-9 kullan
z        = (f[n] - beklenen) / sapma
```

Sınıf (`taban-oranlar.json → esikler`):

| Koşul | Sınıf |
|---|---|
| `f[n] == 0` | `eksik` |
| `z < -0.75` | `normalin_alti` |
| `z <= 0.75` | `dengeli` |
| `z <= 1.75` | `normalin_ustu` |
| aksi | `asiri` |

Sıra önemli: **`f[n] == 0` kontrolü z'den önce gelir.**

Vektörlerde `beklenen` 2, `z` 2 ondalığa yuvarlanmıştır (`round-half-even`
değil, olağan yuvarlama yeter — sınır değerler vektörlerde yok).

---

## 5. Metin varyantı seçimi

```
if sinif != "eksik":            varyant = "hucre"
else if telafi_eder_mi(n):      varyant = "telafili"
else if siddet_sinifi[n] in {"kolektif","yaygin"}:  varyant = "kolektif"
else:                           varyant = "kisisel"
```

`siddet_sinifi` → `taban-oranlar.json`.

**Gerçek Karmik Ders** = `sinif == "eksik" && !telafi_eder_mi(n)`.

Metin kaynakları:
- `varyant == "hucre"` → `kapsam-hucreleri.json → hucreler["<n>|<f>"].metin`
  (yoksa hücresiz uyarı metni) **+** `yogunluk.json → metinler[n][sinif]`
- diğerleri → `karmik-dersler.json → dersler[n][varyant]`; `telafili` değilse
  ayrıca `yasam_zorlamasi` ve `calisma_onerisi`

> `7|8`, `7|9`, `8|9` hücreleri **yoktur** ve olmamalıdır: G/P/Y ve H/Q/Z
> harfleriyle o frekanslara pratikte ulaşılamaz. Port bunu zarif karşılamalı.

---

## 6. Gizli Tutku

```
en_yuksek = max(f.values())
zirve     = f'de degeri en_yuksek olan sayilar, ARTAN sirada
gizli_tutku = zirve[0]                  // esitlikte kucuk sayi kazanir
ikinci    = f degerleri azalan sirada
fark      = en_yuksek - (ikinci[1] varsa o, yoksa 0)

karakter = "paylasimli"  eger len(zirve) > 1
         = "belirgin"    eger fark >= 2
         = "duz"         aksi halde
```

---

## 7. Denge okumaları

**Tek/çift.** `TEK = {1,3,5,7,9}`, `CIFT = {2,4,6,8}`.

```
tek_toplam = sum(f[n] for n in TEK)
p_tek      = sum(harf_olasiligi[n] for n in TEK)
tek_z      = z(tek_toplam, L, p_tek)          // 4. bolumdeki formul

tek_z > 0.75   -> "tek_agir"
tek_z < -0.75  -> "cift_agir"
aksi           -> "dengeli"
```

> Ham oran **kullanılmaz**. Türkçe adlarda tek sayılı harflerin toplam
> olasılığı ~%78'dir; ham oranla neredeyse her ad "tek ağır" çıkar.

**Üçlü eksenler.** `denge.json → ucul_eksenler.eksenler` içindeki her eksen
için aynı z formülü, `p` = eksendeki sayıların olasılık toplamı. Sınıf:
`z < -0.75 → zayif`, `z <= 0.75 → dengeli`, aksi `baskin`.

---

## 8. Sentez

`fazla` = sınıfı `normalin_ustu` veya `asiri` olan sayılar kümesi.
`dersler` = gerçek Karmik Dersler.

- **Çelişki:** `sentez.json → celiskiler` içindeki her `cift = [a,b]` için
  `a ∈ fazla && b ∈ fazla` ise tetiklenir.
- **Pekişme:** `pekismeler` içindeki her kayıt için
  `ders ∈ dersler && fazla_sayisi ∈ fazla` ise tetiklenir.

Sıra: önce tüm çelişkiler (dosyadaki sırayla), sonra tüm pekişmeler.

---

## 9. İfade Planları

`ifade-planlari.json → etkin` **false** olduğu sürece bu bölüm hesaplanmaz ve
basılmaz. Port da bu bayrağa uymalı. Gerekçe: `docs/YOL-HARITASI.md`.

---

## 10. Portu doğrulama

```
tests/uyumluluk-vektorleri.json → vektorler[]
```

Her vektör için `ad` ve `dogum_tarihi` girdi, `beklenen` bloğu çıktıdır.
24 vektörün tamamı geçmelidir. Vektörler şunları sınar: Türkçe diakritikler,
`I`/`İ` ayrımı, tire ve kesme, çok kısa ve çok uzun adlar, usta sayılar,
telafi edilmiş ve edilmemiş dersler, kolektif şiddet, aşırı kayıt, çelişki
tetiklemesi, paylaşımlı ve düz Gizli Tutku.

Vektörler motordan üretilir ve motorla birlikte kaymaları engellenir:

```bash
python3 scripts/vektor_uret.py --dogrula     # sapma varsa 1 döner
```

Hesaplamayı değiştiren her PR bu komutu kırmalı ya da vektörleri bilinçli
olarak yeniden üretmeli — sessiz davranış değişikliği mümkün değil.

---

## Tipik port tuzakları

1. **Büyütme sırası.** Çoğu dilin `toUpperCase()`'i Türkçe'ye duyarlı
   değildir: `ı` ya olduğu gibi kalır (harf haritada bulunmaz ve **atılır**),
   ya da locale'e göre beklenmedik sonuç verir. Bu yüzden genel büyütmeden
   **önce** `i → İ` ve `ı → I` değişimi elle yapılmalıdır. Testi
   `Ilgın Işık` vektörüdür: doğru portta `ILGINISIK` (9 harf) çıkar; `ı`
   atılırsa 7 harf çıkar ve tüm tablo kayar.
2. **Usta sayı kontrolünü döngü dışına almak** — `indirge([5,6])` `2` verirse
   yanlıştır, `11` vermelidir.
3. **`f[n] == 0` kontrolünü z'den sonra yapmak** — sıfır frekans her zaman
   `eksik`tir, z'si ne olursa olsun.
4. **Telafi kümesine Doğum Ayı'nı koymamak** — `Mehmet Öztürk` vektörü bunu
   yakalar.
5. **Gizli Tutku eşitliğinde büyük sayıyı seçmek** — küçük sayı kazanır.
6. **Tek/çift için ham oran kullanmak** — bkz. 7. bölüm.
