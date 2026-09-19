#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/uyumluluk-vektorleri.json uretir.

PORT ICIN ALTIN VEKTORLER. Motor baska bir dile (Dart, TypeScript, Kotlin,
Swift, PHP...) tasindiginda portun dogrulugu bu dosyayla kanitlanir: ayni
girdiler ayni ciktiyi vermelidir. Dilden bagimsizdir, saf JSON'dur.

Vektorler bilincli olarak sinir durumlarini kapsar:
  - Turkce diakritikler ve I / I ayrimi
  - Tire, kesme, rakam iceren adlar
  - Cok kisa ve cok uzun adlar (normalizasyonun ad uzunluguna duyarliligi)
  - Usta sayi (11/22/33) ureten cekirdekler ve bunlarin telafi etkisi
  - Telafi edilmis ve edilmemis Karmik Dersler
  - Kolektif siddet sinifina dusen eksiklikler
  - 'asiri' kaydina dusen sayilar ve bunlarin urettigi sentez celiskileri
  - Paylasimli ve duz Gizli Tutku zirveleri

Kullanim:  python3 scripts/vektor_uret.py [--dogrula]
           --dogrula : yeniden uretmez, mevcut dosyayla motoru karsilastirir
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from numeroloji import Kisi, rapor_uret  # noqa: E402

HEDEF = KOK / "tests" / "uyumluluk-vektorleri.json"

#: (ad, dogum tarihi, bu vektorun neyi sinadigi)
ORNEKLER = [
    ("Ayşe Nur Karahasanoğlu", "1990-03-17", "uzun ad; usta sayi 22 Ruh Arzusu; 22->4 telafisi"),
    ("Mehmet Öztürk", "1977-01-03", "1 telafi edilmis; 7 kolektif ders; 2 ve 8 asiri -> celiski"),
    ("Ali Kaya", "1985-08-08", "cok kisa ad; ayni sayim farkli sinif"),
    ("Zeynep Çelik", "2001-11-29", "Ç ve ç katlamasi"),
    ("İbrahim Şahin", "1963-02-04", "bas harf I; S katlamasi"),
    ("Ilgın Işık", "1999-09-09", "noktasiz I ve noktali I ayni sayiya"),
    ("Öznur Ünlüoğlu", "1970-06-30", "O, U, G katlamasi; uzun soyad"),
    ("Al-i Osman Bey", "1955-12-25", "tire; atilan kelime yok, harfler sayilir"),
    ("D'Artagnan Kaya", "2004-04-04", "kesme isareti"),
    ("Ece Su", "2010-10-10", "asgari uzunluk; yuksek z duyarliligi"),
    ("Mustafa Kemal Atatürk", "1881-05-19", "uc parcali ad"),
    ("Şule Ağaoğlu", "1988-08-18", "S ve G katlamasi bir arada"),
    ("Gülşah Yılmazoğlu", "1992-02-29", "artik yil"),
    ("Hüseyin Çakıroğlu", "1966-11-11", "usta sayi uretme egilimi"),
    ("Ayşegül Kahraman", "1983-07-22", "22 dogum gunu"),
    ("Emre Koç", "2000-01-01", "kisa; Yasam Yolu 4"),
    ("Fatma Nur Şimşek", "1975-03-13", "cift S"),
    ("Yağmur Özdemircioğlu", "1997-09-27", "en uzun soyad"),
    ("Kaan Uz", "2015-05-05", "cok kisa; 5 agirlikli"),
    ("Pınar Güngörmüş", "1979-04-16", "noktasiz i; U katlamasi"),
    ("Ömer Faruk Aydın", "1986-12-08", "uc parcali; O katlamasi"),
    ("Sevda Ak", "2020-02-02", "en kisa vektor"),
    ("Nazlı Ceylan Erdoğan", "1961-10-31", "uc parcali; G katlamasi"),
    ("Zübeyde Hanım", "1857-01-15", "eski tarih"),
]


def vektor(ad: str, dt: str, sinar: str) -> dict:
    r = rapor_uret(Kisi(ad, dt), tekrar_denetimi=False)
    t, c, d = r.tablo, r.cekirdek, r.denge
    return {
        "ad": ad,
        "dogum_tarihi": dt,
        "sinar": sinar,
        "beklenen": {
            "ad_duz": t.ad_duz,
            "harf_sayisi": t.harf_sayisi,
            "cekirdek": {
                "yasam_yolu": c.yasam_yolu, "ifade": c.ifade,
                "ruh_arzusu": c.ruh_arzusu, "kisilik": c.kisilik,
                "dogum_gunu": c.dogum_gunu, "dogum_ayi": c.dogum_ayi,
                "olgunluk": c.olgunluk,
                "telafi_kumesi": sorted(c.telafi_kumesi),
            },
            "frekanslar": {str(n): t.frekanslar[n] for n in range(1, 10)},
            "beklenen_frekans": {str(n): t.okumalar[n].beklenen for n in range(1, 10)},
            "z": {str(n): t.okumalar[n].z for n in range(1, 10)},
            "siniflar": {str(n): t.okumalar[n].sinif for n in range(1, 10)},
            "metin_varyantlari": {str(n): t.okumalar[n].metin_varyanti
                                  for n in range(1, 10)},
            "karmik_dersler": t.karmik_dersler,
            "telafi_edilmis_dersler": t.telafi_edilmis_dersler,
            "asiri_sayilar": t.asiri_sayilar,
            "gizli_tutku": t.gizli_tutku,
            "gizli_tutku_ortaklari": list(t.gizli_tutku_ortaklari),
            "gizli_tutku_karakteri": t.gizli_tutku_karakteri,
            "tek_toplam": d.tek_toplam,
            "cift_toplam": d.cift_toplam,
            "tek_z": d.tek_z,
            "tek_cift_sinif": d.tek_cift_sinif,
            "eksenler": {e.anahtar: {"toplam": e.toplam, "beklenen": e.beklenen,
                                     "z": e.z, "sinif": e.sinif}
                         for e in d.eksenler},
            "sentez": [{"tur": s.tur, "sayilar": list(s.sayilar)} for s in r.sentez],
        },
    }


def uret() -> dict:
    return {
        "surum": "1.0",
        "aciklama": "Port dogrulama vektorleri. Bir port bu girdileri alip ayni "
                    "'beklenen' bloklarini uretmelidir. Metin icerigi degil, "
                    "HESAPLAMA dogrulanir; metin secimi 'metin_varyantlari' ve "
                    "'siniflar' alanlariyla belirlenir.",
        "sema": "latin26_katlamali",
        "kaynak_parametreler": "data/taban-oranlar.json (harf_olasiligi, esikler)",
        "kilavuz": "docs/PORT-KILAVUZU.md",
        "vektorler": [vektor(a, d, s) for a, d, s in ORNEKLER],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dogrula", action="store_true",
                    help="Yeniden uretme; mevcut dosyayla motoru karsilastir")
    a = ap.parse_args(argv)

    yeni = uret()
    if not a.dogrula:
        HEDEF.write_text(json.dumps(yeni, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
        print(f"yazildi: {HEDEF}  ({len(yeni['vektorler'])} vektor)")
        return 0

    if not HEDEF.exists():
        print(f"hata: {HEDEF} yok", file=sys.stderr)
        return 1
    mevcut = json.loads(HEDEF.read_text(encoding="utf-8"))
    fark = [v["ad"] for v, w in zip(mevcut["vektorler"], yeni["vektorler"])
            if v["beklenen"] != w["beklenen"]]
    if fark or len(mevcut["vektorler"]) != len(yeni["vektorler"]):
        print("VEKTORLER SAPTI:", fark or "vektor sayisi degismis", file=sys.stderr)
        return 1
    print(f"{len(yeni['vektorler'])} vektor motorla uyumlu")
    return 0


if __name__ == "__main__":
    sys.exit(main())
