#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genis kabul taramasi: motoru binlerce ad-tarih kombinasyonunda calistirir.

Uc seyi olcer:
  1. Rapor uretimi hic kirilmiyor mu (tekrar denetimi ACIK calistirilir).
  2. Telafi kuralinin etkisi: tabloda sifir olan sayilarin kaci gercekten
     Karmik Ders olarak okunuyor.
  3. Sentez bolumunun kapsami ve rapor uzunlugu dagilimi.

Not: dogum tarihi MUTLAKA cesitlendirilmelidir. Sabit tek bir tarihle
calistirildiginda o tarihin Yasam Yolu / Dogum Ayi degerleri her ornekte ayni
sayiyi telafi eder ve bazi Karmik Dersler yapay olarak %0 cikar.

Kullanim:  python3 scripts/kabul_taramasi.py [--tekrar N]
"""

from __future__ import annotations

import argparse
import collections
import itertools
import random
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from numeroloji import Kisi, rapor_uret  # noqa: E402
from numeroloji.sentez import tekrar_denetle  # noqa: E402

ON_ADLAR = ["MEHMET", "AYŞE", "ALİ", "ZEYNEP", "İBRAHİM", "FATMA", "HÜSEYİN",
            "ELİF", "MUSTAFA", "GÜLSÜM", "SERKAN", "DERYA", "OSMAN", "HATİCE",
            "YUSUF", "MERVE", "EMRE", "PINAR", "KAAN", "ŞERİFE"]
SOYADLAR = ["YILMAZ", "KAYA", "DEMİR", "ŞAHİN", "ÇELİK", "ÖZTÜRK",
            "KARAHASANOĞLU", "ABDÜLKADİROĞLU", "KOÇ", "AVCI", "GÜNEŞ",
            "ZENGİN", "IŞIK", "POLAT"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tekrar", type=int, default=6,
                    help="Her ad icin kac farkli dogum tarihi (varsayilan 6)")
    ap.add_argument("--tohum", type=int, default=7)
    a = ap.parse_args(argv)
    random.seed(a.tohum)

    sifir = collections.Counter()
    ders = collections.Counter()
    telafi = collections.Counter()
    asiri = collections.Counter()
    ihlal = collections.Counter()
    uzunluk: list[int] = []
    sentez_var = 0
    denetim_hatasi = 0
    n = 0

    for on, soy in itertools.product(ON_ADLAR, SOYADLAR):
        for _ in range(a.tekrar):
            dt = (f"{random.randint(1955, 2005)}-"
                  f"{random.randint(1, 12):02d}-{random.randint(1, 28):02d}")
            try:
                r = rapor_uret(Kisi(f"{on} {soy}", dt))   # denetim ACIK
            except AssertionError:
                denetim_hatasi += 1
                continue
            n += 1
            uzunluk.append(len(r.duz_metin()))
            for x in tekrar_denetle(r.duz_metin()):
                ihlal[x["kalip"]] += 1
            if r.sentez:
                sentez_var += 1
            for k, o in r.tablo.okumalar.items():
                if o.sinif == "eksik":
                    sifir[k] += 1
                    (ders if o.karmik_ders_mi else telafi)[k] += 1
                elif o.sinif == "asiri":
                    asiri[k] += 1

    if not n:
        print("hic rapor uretilemedi", file=sys.stderr)
        return 1

    print(f"{n} rapor uretildi  |  tekrar denetiminden dusen: {denetim_hatasi}")
    print(f"uzunluk: ortalama {sum(uzunluk) // n}, "
          f"min {min(uzunluk)}, max {max(uzunluk)} karakter")
    print(f"tekrar esigi ihlali: {dict(ihlal) or 'YOK'}")
    print(f"sentez bolumu olan rapor: {sentez_var}/{n} (%{100 * sentez_var // n})")

    print("\nTelafi kuralinin etkisi:")
    print("  sayi | tabloda sifir | KARMIK DERS | telafi edildi | telafi orani")
    print("  " + "-" * 62)
    for k in range(1, 10):
        s0 = sifir[k]
        oran = 100 * telafi[k] / s0 if s0 else 0.0
        print(f"   {k}   |    {100*s0/n:5.1f}%     |    {100*ders[k]/n:5.1f}%   "
              f"|    {100*telafi[k]/n:5.1f}%    |   %{oran:.0f}")

    print("\n'asiri' kaydina dusen sayi sikligi:")
    print("  " + "  ".join(f"{k}: %{100*asiri[k]/n:.1f}" for k in range(1, 10)))

    if denetim_hatasi or ihlal:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
