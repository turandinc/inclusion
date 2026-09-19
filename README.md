# inclusion

Türkçe numeroloji uygulamaları için **kapsam tablosu (inclusion table)** motoru
ve yorum korpusu.

Bir adın harflerinden 1–9 frekans tablosu çıkarır, frekansları ad uzunluğuna
göre normalize eder, Karmik Dersleri çekirdek sayılarla çapraz kontrol eder ve
sentezlenmiş bir rapor üretir.

## Kurulum

Bağımlılık yok — yalnızca Python 3.10+ standart kütüphanesi.

```bash
git clone https://github.com/turandinc/inclusion
cd inclusion
export PYTHONPATH=src
```

## Kullanım

```bash
# Tam rapor
python3 -m numeroloji "Ayşe Nur Karahasanoğlu" 1990-03-17

# Sayısal tablo (hesaplamayı denetlemek için)
python3 -m numeroloji "Mehmet Öztürk" 1977-01-03 --tablo

# Uygulama katmanı için JSON
python3 -m numeroloji "Ali Kaya" 1985-08-08 --json
```

Kütüphane olarak:

```python
from numeroloji import Kisi, rapor_uret

rapor = rapor_uret(Kisi("Ayşe Nur Karahasanoğlu", "1990-03-17"))
print(rapor.duz_metin())      # Markdown
veri = rapor.sozluk()         # JSON'a serileştirilebilir
```

## Yapı

```
data/                     Yorum korpusu ve parametreler (dilden bağımsız)
  harf-haritasi.json        harf → sayı, Türkçe katlama, ad kaynağı kuralları
  taban-oranlar.json        beklenen frekans temeli + taban oranlar (üretilir)
  karmik-dersler.json       frekans 0 — 9 ders × 3 varyant
  kapsam-hucreleri.json     frekans ≥ 1 — 78 hücre (üretilir)
  yogunluk.json             frekansın niceliği — 9 sayı × 4 kayıt
  gizli-tutku.json          en yüksek frekans okuması
  denge.json                tek/çift + üçlü eksenler
  sentez.json               çelişki/pekişme çiftleri, tekrar eşikleri
  ifade-planlari.json       harf tabanlı planlar — KAPALI, bkz. YOL-HARITASI
src/numeroloji/           Referans uygulama (stdlib, bağımlılıksız)
scripts/                  Üretim betikleri (idempotent)
tests/                    41 test, bağımlılıksız
docs/METODOLOJI.md        Disiplin kararları ve gerekçeleri
docs/YOL-HARITASI.md      Madde madde durum
inclusion.md              1.0 korpusu — kaynak belge, silinmedi
```

`data/` içeriği saf JSON'dur; Python motoru bir **referans uygulamadır**.
Uygulamanız başka bir dilde ise korpusu doğrudan tüketip motoru porte
edebilirsiniz — `docs/METODOLOJI.md` tüm hesaplama kurallarını yazar.

## Testler

```bash
python3 -m unittest discover -s tests
```

Testler hesaplamayı doğrulamakla kalmaz; **içerik regresyonu** da korur:
1.0 sürümünden kaldırılan kaderci öngörüler, klinik iddialar, çeviri hataları
ve 2. tekil ses geri gelirse test kırılır.

## Veri yeniden üretimi

```bash
python3 scripts/taban_oran_uret.py      # data/taban-oranlar.json
python3 scripts/hucre_migrasyonu.py     # data/kapsam-hucreleri.json
```

İkisi de idempotenttir ve `inclusion.md`'yi kaynak alır.
