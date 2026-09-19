"""Sentez katmani: celisen hucreleri adiyla kurar, pekisen hucreleri birlestirir.

1.0 surumunde hucreler atomikti. Tablo cogu zaman celisen hucreler uretir
(ornegin 4 fazlaligi ile 5 fazlaligi) ve rapor bunlari iki ayri paragraf olarak
basip geciyordu. Iyi bir okuma gerilimi ADIYLA kurar ve cozer.
"""

from __future__ import annotations

from dataclasses import dataclass

from .kapsam import KapsamTablosu
from .veri import yukle

FAZLA_SINIFLAR = ("normalin_ustu", "asiri")


@dataclass(frozen=True)
class SentezNotu:
    tur: str                      # "celiski" | "pekisme"
    ad: str
    sayilar: tuple[int, ...]
    metin: str


def sentez_uret(tablo: KapsamTablosu) -> tuple[SentezNotu, ...]:
    veri = yukle("sentez")
    notlar: list[SentezNotu] = []

    fazla = {n for n, o in tablo.okumalar.items() if o.sinif in FAZLA_SINIFLAR}
    dersler = set(tablo.karmik_dersler)

    for c in veri["celiskiler"]:
        a, b = c["cift"]
        if a in fazla and b in fazla:
            notlar.append(SentezNotu("celiski", c["ad"], (a, b), c["metin"]))

    for p in veri["pekismeler"]:
        if p["ders"] in dersler and p["fazla"] in fazla:
            notlar.append(SentezNotu(
                "pekisme",
                f"Karmik Ders {p['ders']} ile {p['fazla']} fazlaligi",
                (p["ders"], p["fazla"]),
                p["metin"],
            ))

    return tuple(notlar)


def tekrar_denetle(metin: str) -> list[dict]:
    """Raporda esigi asan kaliplasmis ifadeleri dondurur.

    Rapor tek seferde dokuz hucre bastigi icin sablon, tek tek okunurken
    gorunmeyen ama birlikte okunurken belirgin hale gelen bir kusurdur.
    Bos liste = rapor tekrar denetiminden gecti.
    """
    veri = yukle("sentez")["tekrar_denetimi"]
    asanlar = []
    for k in veri["kaliplar"]:
        sayim = metin.lower().count(k["kalip"].lower())
        if sayim > k["esik"]:
            asanlar.append({"kalip": k["kalip"], "sayim": sayim, "esik": k["esik"]})
    return asanlar
