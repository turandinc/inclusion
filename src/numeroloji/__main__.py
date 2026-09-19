# -*- coding: utf-8 -*-
"""Komut satirindan rapor uretir ve tabloyu inceler.

    python3 -m numeroloji "Ayşe Nur Karahasanoğlu" 1990-03-17
    python3 -m numeroloji "Ali Kaya" 1985-08-08 --tablo
    python3 -m numeroloji "Ali Kaya" 1985-08-08 --json
"""

from __future__ import annotations

import argparse
import json
import sys

from .cekirdek import Kisi
from .harf import HarfHaritasi
from .rapor import rapor_uret


def _tablo_yaz(r) -> None:
    t, c = r.tablo, r.cekirdek
    print(f"Ad        : {r.kisi_adi}  ->  {t.ad_duz}  ({t.harf_sayisi} harf)")
    print(f"Cekirdek  : Yasam Yolu {c.yasam_yolu} | Ifade {c.ifade} | "
          f"Ruh Arzusu {c.ruh_arzusu} | Kisilik {c.kisilik} | "
          f"Dogum Gunu {c.dogum_gunu} | Olgunluk {c.olgunluk}")
    print(f"Gizli Tutku: {t.gizli_tutku} ({t.gizli_tutku_karakteri})\n")
    print("  sayi  frek  beklenen       z  sinif           not")
    print("  " + "-" * 68)
    for n in range(1, 10):
        o = t.okumalar[n]
        not_ = ""
        if o.sinif == "eksik":
            not_ = (f"telafi: {', '.join(o.telafi_kaynaklari)}"
                    if o.telafi_edildi
                    else f"KARMIK DERS ({o.siddet}, taban %{o.taban_orani*100:.0f})")
        print(f"   {n}     {o.frekans:2d}    {o.beklenen:6.2f}  {o.z:+6.2f}  "
              f"{o.sinif:<14}  {not_}")
    d = r.denge
    print(f"\n  Tek/cift  : {d.tek_toplam}/{d.cift_toplam}  z={d.tek_z:+.2f}  "
          f"-> {d.tek_cift_sinif}")
    for e in d.eksenler:
        print(f"  {e.ad:<16}: {e.toplam:2d}  bek {e.beklenen:5.2f}  "
              f"z={e.z:+.2f}  {e.sinif}")
    if r.sentez:
        print("\n  Sentez notlari:")
        for s in r.sentez:
            print(f"    [{s.tur}] {s.ad}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="numeroloji",
        description="Kapsam tablosu raporu uretir.")
    ap.add_argument("ad", help="Nufus kaydindaki tam dogum adi")
    ap.add_argument("dogum_tarihi", help="YYYY-MM-DD")
    ap.add_argument("--tablo", action="store_true",
                    help="Metin yerine sayisal tabloyu yaz")
    ap.add_argument("--json", action="store_true",
                    help="Raporu JSON olarak yaz")
    ap.add_argument("--sema", default=None,
                    help="Harf semasi (varsayilan: data/harf-haritasi.json)")
    ap.add_argument("--tekrar-denetimi-kapali", action="store_true",
                    help="Kaliplasmis ifade denetimini atla")
    a = ap.parse_args(argv)

    try:
        hm = HarfHaritasi.varsayilan(a.sema)
        r = rapor_uret(Kisi(a.ad, a.dogum_tarihi), hm,
                       tekrar_denetimi=not a.tekrar_denetimi_kapali)
    except (ValueError, AssertionError) as e:
        print(f"hata: {e}", file=sys.stderr)
        return 1

    if a.json:
        print(json.dumps(r.sozluk(), ensure_ascii=False, indent=2))
    elif a.tablo:
        _tablo_yaz(r)
    else:
        print(f"# {r.kisi_adi}\n")
        print(r.duz_metin())
    return 0


if __name__ == "__main__":
    sys.exit(main())
