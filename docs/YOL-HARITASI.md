# Yol haritası — durum

Analizde çıkan 11 maddenin uygulanma durumu.

| # | Madde | Durum | Nerede |
|---|---|---|---|
| 1 | Telafi kuralı (çekirdek sayı çapraz kontrolü) | ✅ | `cekirdek.py`, `kapsam.py`, `karmik-dersler.json` (`telafili` varyant) |
| 2 | Taban oran ölçeklemesi | ✅ | `scripts/taban_oran_uret.py`, `taban-oranlar.json`, `kolektif` varyant |
| 3 | Karmik Ders ton revizyonu | ✅ | `karmik-dersler.json` — 27 varyant yeniden yazıldı |
| 4 | Anlam bozan çeviri hataları | ✅ | `scripts/hucre_migrasyonu.py` — 50 ikame kuralı |
| 5 | Frekans normalizasyonu + üç kayıt | ✅ | `kapsam.py` (z-skor), `yogunluk.json` (36 metin) |
| 6 | Gizli Tutku + Yoğunluk Sayısı | ✅ | `kapsam.py`, `gizli-tutku.json` (9 metin) |
| 7 | Ses birleştirme | ✅ | migrasyon ikameleri + `TestIcerikRegresyonu` |
| 8 | Harf haritası ve ad kaynağı belgelemesi | ✅ | `harf-haritasi.json`, `docs/METODOLOJI.md` §1 |
| 9 | `1\|N` ve `5\|N` derinleştirme | ✅ | 18 hücre elle yeniden yazıldı |
| 10 | Sentez katmanı + şablon kırma | ✅ | `sentez.py`, `sentez.json`, `tekrar_denetle()` |
| 11 | Tek/çift + üçlü eksenler | ✅ | `planlar.py`, `denge.json` |
| 11b | İfade Planları (harf tabanlı) | ⛔ **kalıcı kapalı** | `ifade-planlari.json` — ürün kendi gruplamasını kullanıyor |

---

## Kapanan kalem: İfade Planları (⛔ kalıcı kapalı)

Harf tabanlı dört planın (fiziksel / zihinsel / duygusal / sezgisel) harf
gruplaması kaynaklar arasında değişiyor ve yerleşik tek bir tablo yok. 20 Eyl
2026'da ürün sahibiyle netleşti: **bu kavram üretimdeki raporda zaten var.**
"İfade Düzlemi (Harf Kaliteleri) Göstergesi" bölümü, ürünün kendi harf
gruplamasıyla (Excel/VBA kaynağı, Türkçe harfleri de kapsıyor) hesaplanıyor.

İki gruplama aynı değil:

| Grup | Üründeki (canlı) | Buradaki (kapalı) |
|---|---|---|
| Zihinsel | A H J N P **G Ğ L** | A H J N P |
| Bedensel/Fiziksel | E W **D M** | E W |
| Duygusal | O Ö R I İ **Z B S Ş T X** | I O R S U Y |
| Sezgisel | K F Q U Ü Y C Ç V | B C D F G K L M Q T V X Z |

Aynı kişi için farklı yüzdeler üretirler; ikisi bir arada yayınlanamaz. Bu
yüzden buradaki katman **açılmayacak** — veri, karşılaştırma yapmak isteyen
için duruyor. Açılması gerekirse önce ürünün kendi gruplamasının kaynağı
gözden geçirilmeli ve hangisinin doğru kabul edileceğine karar verilmeli;
o karar canlı rapordaki yüzdeleri değiştirir.

---

## Port kiti

Motor Python referans uygulamasıdır. Başka bir dile taşımak için:

| Dosya | Ne işe yarar |
|---|---|
| `docs/PORT-KILAVUZU.md` | Adım adım algoritma şartnamesi + tipik tuzaklar |
| `tests/uyumluluk-vektorleri.json` | 24 altın vektör (girdi → beklenen çıktı) |
| `scripts/vektor_uret.py --dogrula` | Vektörlerin motorla uyumunu denetler |
| `ports/js/numeroloji.js` | Node (CommonJS) portu — 24/24 vektör geçiyor: `node ports/js/uyumluluk.test.js` |
| `ports/js/ikincil.test.js` | İkincil tablo (evlilik soyadı) okuması — 6 örnek, 6 etki türü |

`data/*.json` hiçbir dile bağlı değildir ve olduğu gibi okunur. Portun işi
yalnızca doğru sayıları üretmek ve doğru metin anahtarını seçmek.

---

## Sonraki adımlar için öneriler (bu turun kapsamı dışında)

1. **Karmik Borç (13/14/16/19).** Karmik Ders'ten farklı bir kavram; doğum
   tarihi ve çekirdek sayı toplamlarından okunur. Korpusta hiç yok.
2. ~~**İkincil tablolar.**~~ ✅ **Yapıldı (20 Eyl 2026).** Evlilik soyadı için
   çerçeve yazıldı: `data/ikincil-tablo.json` + `ikincilOkuma()` (JS portu).
   Okunan şey adet değil DEĞİŞİMDİR — ad uzadıkça beklenti büyüdüğü için bir
   sayı, adedi artsa bile sınıf olarak inebilir. Altı etki: kapanma, güçlenme,
   yumuşama, aynı yönde destek, destek yok, destek yok + seyrelme. Karmik Ders
   doğum adından okunur; eş soyadı bir dersi KALDIRMAZ (test bunu korur:
   `ports/js/ikincil.test.js`).

   ⚠️ Bu katman şu an YALNIZCA JS portunda var; Python referans uygulaması
   ikincil tabloyu hesaplamıyor. Python'a taşınırsa aynı veri dosyası okunur.
3. **Hücre metinlerinin tema etiketleriyle filtrelenmesi.** Metadata
   (`temalar`) hazır; "kariyer raporu" / "ilişki raporu" gibi tematik kesitler
   bu alandan üretilebilir.
4. **Nüfus ağırlıklı taban oranlar.** Mevcut oranlar ad–soyad çapraz
   çarpımından; TÜİK ad sıklıkları ile ağırlıklandırılabilir.
