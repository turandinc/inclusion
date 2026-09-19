# Metodoloji

Bu dosya, kapsam tablosu okumasında verilen **disiplin kararlarını** ve
gerekçelerini kayda geçirir. Bir kararın tartışmalı olduğu yerde tartışma
gizlenmez; hangi tarafın seçildiği ve nedeni yazılır.

---

## 1. Harf–sayı haritası ve Türkçe sorunu

**Karar:** 26 harfli Pitagor haritası, Türkçe harfler Latin tabanlarına
katlanarak (`Ç→C`, `Ğ→G`, `İ→I`, `I→I`, `Ö→O`, `Ş→S`, `Ü→U`).

**Gerekçe:**
1. Pitagor 1–9 haritası tarihsel olarak 26 harfli Latin alfabesi üzerinde
   tanımlıdır. 29 harfli Türk alfabesini 1–9 döngüsüne sokmanın geleneksel bir
   dayanağı yoktur; tamamen modern bir yorumdur.
2. Türkçe diakritikler aynı harfin yazım varyantıdır.
3. Katlama, aynı adın ASCII ve Unicode yazımlarında (Ayse / Ayşe) **aynı
   tabloyu** üretir. Nüfus kayıtlarında ve dijital sistemlerde harf çevrimi
   tutarsız olduğu için bu pratik olarak zorunludur.

**Alternatif açıkta bırakıldı:** `data/harf-haritasi.json` içindeki
`turk29_dongusel` şeması. Etkinleştirilebilir, ama **tüm tablo değişir** ve
hücre metinleri başka sayılara denk gelir; korpus yeniden doğrulanmadan
üretime alınmamalıdır. Şema `HarfHaritasi.varsayilan(sema=...)` ile seçilir.

**Sesli/sessiz ayrımı:** Ruh Arzusu ve Kişilik sayıları için Türkçe sesliler
`A E I İ O Ö U Ü`. **Y her zaman sessizdir** — İngiliz ekolündeki "koşullu
sesli Y" kuralı Türkçe'ye taşınmaz.

**Ad kaynağı:** Nüfus kaydındaki tam doğum adı (tüm ön adlar + doğum soyadı).
İkinci ve üçüncü ön adlar sayılır. Kullanılan ad ve evlilik soyadı ikincil
tablolar üretir, Karmik Ders üretmez.

---

## 2. Frekans normalizasyonu

**Sorun:** 1.0 sürümünde frekans mutlak bir sayaçtı. `AYŞE KAYA` ile
`MEHMET ABDÜLKADİROĞLU` aynı "4 frekansı" metnini okuyordu — birincisinde 4
adet bir sayı ciddi bir yoğunlaşma, ikincisinde normalin altı.

**Karar:** Sayım `Binom(L, pₙ)` kabul edilir; `L` addaki harf sayısı, `pₙ` o
sayıya düşen harflerin Türkçe adlardaki toplam olasılığı. Sınıf, z-skorundan
belirlenir:

| z | sınıf |
|---|---|
| frekans = 0 | `eksik` |
| z < −0.75 | `normalin_alti` |
| −0.75 ≤ z ≤ 0.75 | `dengeli` |
| 0.75 < z ≤ 1.75 | `normalin_ustu` |
| z > 1.75 | `asiri` |

**Neden Anglo tablosu ithal edilmedi:** Klasik pratikte beklenti ~15 harflik
bir *İngilizce* ad için sabitlenmiştir (1:3, 2:1, 3:2, 4:1, 5:4, 6:1, 7:1,
8:0-1, 9:2). Türkçe'nin harf dağılımı farklıdır, dolayısıyla o tablo Türkçe
adlarda yanlış beklenti üretir. `pₙ` bunun yerine Türkçe ad korpusundan
ölçülür (`scripts/taban_oran_uret.py`).

---

## 3. Üç kayıt ve "aşırı" sorunu

**Sorun:** 1.0'da yüksek frekans metinleri neredeyse tamamen olumluydu
("çok belirgin olacak", "büyük bir…"). Disiplinde ise ortalamanın çok üstü
frekans bir **kusur işaretidir**: fazla 4 katılık, fazla 5 dağılma, fazla 6
duygusal boğulma. Raporun duygusal profili iki kutupluydu — sıfır = yıkım,
sıfır-dışı = iltifat. Bu, Forer/Barnum etkisinin klasik tuzağıdır.

**Karar:** Frekansın **niceliği** ile **niteliği** ayrı katmanlara bölündü.

| katman | dosya | ne söyler |
|---|---|---|
| Hücre metni | `data/kapsam-hucreleri.json` | sayı ile frekansın *karışımı* (blend) |
| Yoğunluk kaydı | `data/yogunluk.json` | frekansın beklentiye göre *niceliği* |

Bu ayrım 1.0'daki en derin kavramsal sorunu çözer: aynı korpus içinde bazı
hücreler basamak karışımı ("5'in açık fikirliliği somut etkinliklere yönelir"),
bazıları yoğunluk ("çok fazla 6 var, sağlığınıza dikkat") anlamında
kullanılıyordu. Artık her hücre karışımı, her yoğunluk kaydı niceliği anlatır.

---

## 4. Telafi kuralı

**Sorun:** 1.0'da yoktu. Sonuç somut bir yanlış okumaydı: Yaşam Yolu 8 olan,
adında H/Q/Z bulunmayan bir kullanıcıya "mali konularda korkaksın, muhakemen
zayıf" deniyordu.

**Karar:** Tabloda sıfır olan bir sayı, **çekirdek sayılarda varsa Karmik Ders
değildir**; ders zaten çalışılmaktadır ve okuma `telafili` varyanta düşer.

Telafi kümesi: Yaşam Yolu, İfade (Kader), Ruh Arzusu, Kişilik, Doğum Günü,
**Doğum Ayı**, Olgunluk. Usta sayılar indirgenerek de test edilir (11 → 2,
22 → 4, 33 → 6).

**Bu kural korpusun kendi içinde iki yerde kazara belirmişti** ve
sistematikleştirildi:
- `inclusion.md` 2|0: *"11'in varlığı, … bu eksikliği telafi edecek"* → usta
  sayı indirgemesi.
- `inclusion.md` 1|0: *"Eğer Ocak ya da Ekim aylarında doğduysan…"* → Doğum Ayı.

**Ölçülen etki** (`scripts/kabul_taramasi.py`, 1.680 rapor, değişken doğum
tarihi): telafi kuralı, tabloda sıfır olan sayıların **%47–72'sini** Karmik
Ders okumasından çıkarır.

| sayı | tabloda sıfır | Karmik Ders olarak okunan | telafi edilen |
|---|---|---|---|
| 1 | %8,9 | %4,5 | %49 |
| 2 | %27,9 | %7,7 | %72 |
| 3 | %23,2 | %8,5 | %64 |
| 4 | %39,3 | %18,7 | %52 |
| 5 | %17,1 | %9,2 | %47 |
| 6 | %45,0 | %16,8 | %63 |
| 7 | %32,5 | %13,2 | %59 |
| 8 | %48,2 | %21,2 | %56 |
| 9 | %12,9 | %5,7 | %56 |

> Taramada doğum tarihi **mutlaka çeşitlendirilmelidir**. Sabit tek bir tarihle
> çalıştırıldığında o tarihin Yaşam Yolu ve Doğum Ayı değerleri her örnekte aynı
> sayıyı telafi eder ve bazı Karmik Dersler yapay olarak %0 çıkar.

Geriye kalan sıfırların yüksek taban oranlı olanları (6, 7, 8) ayrıca
`kolektif` varyantla okunur — yani 1.0'da %45–48 kullanıcıya sert kişisel
teşhis olarak giden içerik, artık ya hiç Karmik Ders sayılmıyor ya da kuşaksal
tema diliyle anlatılıyor.

---

## 5. Taban oran ve şiddet ölçeklemesi

**Ölçüm** (`scripts/taban_oran_uret.py`, 346.752 ad–soyad kombinasyonu):

| sayı | tabloda hiç çıkmama oranı | şiddet sınıfı |
|---|---|---|
| 1 | %5,3 | kişisel |
| 2 | %27,0 | yaygın |
| 3 | %9,9 | kişisel |
| 4 | %33,9 | yaygın |
| 5 | %4,3 | kişisel |
| 6 | **%54,5** | kolektif |
| 7 | **%36,8** | kolektif |
| 8 | **%44,8** | kolektif |
| 9 | %12,3 | kişisel |

**Karar:** Taban oranı yüksek eksiklik `kolektif` varyantla okunur.

**Gerekçe (disiplin):** Neredeyse herkeste bulunan bir eksiklik kişisel bir
ders değil, kuşaksal bir temadır. Türk kullanıcıların yarıya yakını 6, 7 ve 8
Karmik Derslerini alır; 1.0'da bunlar korpusun en sert üç metniydi.

1.0 bunu 7 için **fark etmişti** — *"Günümüzde büyük çoğunlukla yetişkinlerin
Tablolarında 7'nin olmayışı…"* — ama sonra aynı şiddette okumaya devam
ediyordu. Nadirlik etiketleri de tutarsızdı: 5 ve 9 için "nadir" deniyor
(%4 ve %12 — doğru), %55'lik 6 ve %45'lik 8 hiç nadirlik beyanı yapmıyordu.

> Korpus oranları **büyüklük mertebesi** içindir. Ad–soyad çapraz çarpımı
> nüfus dağılımına göre ağırlıklandırılmamıştır; nüfus istatistiği olarak
> sunulmaz.

---

## 6. Karmik Ders çerçevesi

**Karar:** Karmik Ders bir ceza ya da kader değil, bir **ödevdir**.

Kaldırılan içerik ve gerekçeleri:

| kaynak | kaldırılan | neden |
|---|---|---|
| 6\|0 | boşanma öngörüsü, "evlat edinerek Karmayı tamamlama" | Bir tablo boşluğu bir evliliğe dair öngörü taşıyamaz. Üstelik %54,5 kullanıcıya söyleniyordu. |
| 8\|0 | "Muhakemen zayıf", mali çöküş öngörüsü | Bilişsel yetersizlik teşhisi + %44,8 kullanıcıya finansal kehanet. |
| 3\|0 | "psikolojik bir çöküntü içindesin", "yuvarlak omuzlu olmana yol açar", "kendini mahvetmene yol açacak" | Ruh sağlığı teşhisi ve beden yorumu. |
| 2\|0 | "Kleptomanlar genellikle Karmik Ders 2'ye sahip olur" | Klinik/adli iddia. |
| 5\|0 | "hayat senin için bir ızdırap olacak" | Umut kapatan dil. |
| 7\|0 | "ayrılıklar, fakirlik, yalnızlık ve tecrit yoluyla" | Yoksulluk öngörüsü. |
| 9\|0 | "şanssızlık olarak görülen bir durumdasın" | Kader dili. |

**Korunan içerik:** Campbell geleneğinin ayrıştırıcı iki unsuru bilinçli olarak
tutuldu ve ayrı alanlara taşındı — `yasam_zorlamasi` (hayatın dersi nasıl
öğrettiği) ve `cocukluk_notu` (çocuk yetiştirme notu). Bunlar piyasada yok ve
korpusun gerçek değeridir; sorun tonlarıydı, varlıkları değil.

Ayrıca `calisma_onerisi` alanı eklendi: her ders için tek, somut, yapılabilir
bir egzersiz.

---

## 7. Ses birleştirme

**Sorun:** 1.0'da frekans = 0 satırları 2. tekil ("görüyorum", "zorundasın",
ortalama 948 karakter, kaderci), frekans ≥ 1 satırları 2. çoğul ("edersiniz",
ortalama 355 karakter, ölçülü) idi. Rapor iki ayrı kişi tarafından konuşuyormuş
gibi okunuyordu.

**Karar (ilk):** Tümü **2. çoğul (siz)**. 87 hücrenin 78'i zaten öyleydi.

**Karar (revize):** Tek ses ilkesi korunur, ama seçilen ses **2. tekil (sen)**.
Kapsam tablosu, baştan sona "sen" ile konuşan üretimdeki numeroloji raporuna
gömülüyor; bir bölümün "siz" olması, 1.0'daki iki-anlatıcı kusurunun aynısını
rapor düzeyinde yeniden üretirdi. Metinler "siz" ile yazılıp bakımı yapılır,
`scripts/hitap.py` ile "sen"e çevrilir (hücre migrasyonu bunu en son adım olarak
uygular). Dönüşüm kurala dayalıdır (`n + ünlü + z` → `n`), istisnaları —
zamirler, emir kipi, kökünde `niz` geçen kelimeler — dosyada tek tek listelidir.

Ayrıca 11 yerde Fransızca `on aime` kalıbı "severiz" diye çevrilmişti ve cümle
ortasında anlatıcı değişiyordu: *"Yalnız çalışmayı **sever**, yeteneklerin**ize**
güven duyar**sınız**"*. Düzeltildi. Birinci tekil kâhin sesi ("görüyorum")
kaldırıldı.

Regresyon testleri: `test_tek_ses_sen` kullanıcıya basılan her metinde tek bir
2. çoğul biçim bile kalmadığını, `test_rapor_iskeleti_tek_ses` rapor
kodundaki sabit metinleri, `test_hitap_donusumu_kararli` dönüşümün idempotent
olduğunu denetler. Kaldırılan çeviri kalıpları hem "siz" hem "sen" hâliyle
aranır.

---

## 8. Tek/çift ve üçlü eksenler

**Tek/çift:** Türkçe adlarda tek sayılı harflerin toplam olasılığı **~%78**
olduğu için ham oran yorumlanamaz — neredeyse her ad "tek ağır" çıkar.
Beklentiden sapma (z) kullanılır.

**Üçlü eksenler:** Sayılar 1–9 üçlü kolonlar halinde okunur: 1-4-7, 2-5-8,
3-6-9. **Eksen adları (`Eylem`, `İlişki`, `İfade`) bu depoda tanımlanmış bir
uzlaşımdır**; yazarlar arasında adlandırma değişir. Motor ağırlıkları hesaplar,
adlandırma `data/denge.json` içinden gelir ve değiştirilebilir.

---

## 9. İfade Planları — doğrulanmadı, kapalı

Harf tabanlı İfade Planları'nın (fiziksel / zihinsel / duygusal / sezgisel)
**harf gruplaması kaynaklar arasında önemli ölçüde değişir ve tek bir yerleşik
tablo yoktur.**

`data/ifade-planlari.json` motoru ve metinleri içerir, ama:

```json
"etkin": false,
"kaynak_dogrulamasi": "ONAYLANMADI"
```

`planlar_hesapla()` bu bayrak açılmadıkça boş döner ve bölüm rapora
**basılmaz**. Kendi kaynağınıza göre gruplamayı onaylayıp `etkin: true` yapın.

Bu, bilerek verilmiş bir karardır: doğrulanmamış bir harf tablosunu gelenek
gibi sunmak, bu revizyonun düzeltmeye çalıştığı kusurun aynısı olurdu.
Tek/çift ve üçlü eksen okumaları bu belirsizliği taşımaz ve etkindir.

---

## 10. Sentez ve şablon tekrarı

**Sentez:** 1.0'da hücreler atomikti; çelişen iki hücre yan yana basılıp
geçiliyordu (4 fazlalığı = katılık, 5 fazlalığı = özgürlük — iki paragraf
birbirini yalanlıyordu). `data/sentez.json` 10 çelişki ve 8 pekişme çifti
tanımlar:

- **çelişki** → iki sayı da `normalin_ustu` veya `asiri` ise gerilim canlıdır.
- **pekişme** → biri telafi edilmemiş Karmik Ders, diğeri fazlalık ise okuma
  pekişir.

**Şablon tekrarı:** Rapor tek seferde dokuz hücre basar; kalıp bu yüzden
görünür olur. `sentez.tekrar_denetle()` eşik aşan kalıpları ölçer ve
`rapor_uret()` varsayılan olarak bunu zorunlu tutar.

Bu denetim üretim sırasında **gerçek bir kusur yakaladı**: "girişimde bulunur"
kalıbı altı hücrede geçiyor ve 280 örnek raporun 27'sinde eşiği aşıyordu. Altı
hücre çeşitlendirildi; sweep artık sıfır ihlal veriyor.

---

## 11. Derinlik tahsisi

1.0'da içerik yatırımı isabet olasılığıyla ters orantılıydı:

| sayı | 1.0 ortalama uzunluk | Türkçe adlarda kullanım |
|---|---|---|
| **1** | **256 karakter (en ince)** | Gizli Tutku'nun %39'u |
| 5 | 302 | %4 oranında sıfır — sürekli basılır |
| **7** | **488 (en zengin)** | %37 oranında sıfır |

`1|N` ve `5|N` satırlarının 18 hücresi elle yeniden yazıldı ve
derinleştirildi; şablon açılışları (`"… ile kendinizi ifade edersiniz"`)
kırıldı.

---

## Değişmeyen şey

`inclusion.md` **silinmedi**. 1.0 korpusu kaynak belge olarak durur:
`scripts/hucre_migrasyonu.py` her çalıştığında ondan yeniden üretir, yani
migrasyon idempotenttir ve her düzeltme denetlenebilir. Regresyon testleri de
1.0 metnini referans alır.
