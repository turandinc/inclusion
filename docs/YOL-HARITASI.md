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
| 11b | İfade Planları (harf tabanlı) | ⚠️ **kapalı** | `ifade-planlari.json` — gruplama doğrulanmadı |

---

## Tek açık kalem: İfade Planları

Harf tabanlı dört planın (fiziksel / zihinsel / duygusal / sezgisel) harf
gruplaması kaynaklar arasında önemli ölçüde değişiyor ve yerleşik tek bir tablo
yok. Motor ve metinler hazır, ama bölüm `"etkin": false` olduğu için rapora
basılmıyor.

**Açmak için:** kendi kaynağınızdaki gruplamayı `data/ifade-planlari.json`
içindeki `harf_gruplari` ile karşılaştırın, düzeltin, `"etkin": true` ve
`"kaynak_dogrulamasi": "<kaynağınız>"` yapın. `tests/test_numeroloji.py`
içindeki `test_ifade_planlari_dogrulanmadan_kapali` testi de o zaman
güncellenmeli.

Doğrulanmamış bir harf tablosunu gelenek gibi sunmak, bu revizyonun düzelttiği
kusurun aynısı olurdu — o yüzden kapalı bırakıldı.

---

## Port kiti

Motor Python referans uygulamasıdır. Başka bir dile taşımak için:

| Dosya | Ne işe yarar |
|---|---|
| `docs/PORT-KILAVUZU.md` | Adım adım algoritma şartnamesi + tipik tuzaklar |
| `tests/uyumluluk-vektorleri.json` | 24 altın vektör (girdi → beklenen çıktı) |
| `scripts/vektor_uret.py --dogrula` | Vektörlerin motorla uyumunu denetler |
| `ports/js/numeroloji.js` | Node (CommonJS) portu — 24/24 vektör geçiyor: `node ports/js/uyumluluk.test.js` |

`data/*.json` hiçbir dile bağlı değildir ve olduğu gibi okunur. Portun işi
yalnızca doğru sayıları üretmek ve doğru metin anahtarını seçmek.

---

## Sonraki adımlar için öneriler (bu turun kapsamı dışında)

1. **Karmik Borç (13/14/16/19).** Karmik Ders'ten farklı bir kavram; doğum
   tarihi ve çekirdek sayı toplamlarından okunur. Korpusta hiç yok.
2. **İkincil tablolar.** `kapsam_hesapla(..., ad=...)` kullanılan ad ve evlilik
   soyadı için çalışıyor, ama bunlara ait yorum çerçevesi ("sonradan edinilen
   titreşim") henüz yazılmadı.
3. **Hücre metinlerinin tema etiketleriyle filtrelenmesi.** Metadata
   (`temalar`) hazır; "kariyer raporu" / "ilişki raporu" gibi tematik kesitler
   bu alandan üretilebilir.
4. **Nüfus ağırlıklı taban oranlar.** Mevcut oranlar ad–soyad çapraz
   çarpımından; TÜİK ad sıklıkları ile ağırlıklandırılabilir.
