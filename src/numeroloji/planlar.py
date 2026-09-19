"""Tablonun butun olarak okunmasi: tek/cift dengesi, uclu eksenler, ifade planlari.

1.0 surumunde tablo yalnizca hucre hucre okunuyordu; butunun kendisi hic
okunmuyordu. Bu modul o katmani ekler.

Her uc olcum de ham oran degil BEKLENTIDEN SAPMA uzerinden siniflanir. Turkce
adlarda tek sayilar dogal olarak baskin oldugu icin (tek sayili harflerin toplam
olasiligi ~%78) ham oran yorumlanamaz.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .kapsam import KapsamTablosu
from .veri import yukle

TEK = (1, 3, 5, 7, 9)
CIFT = (2, 4, 6, 8)


def _z(gozlenen: int, L: int, p: float) -> float:
    if L == 0 or p <= 0 or p >= 1:
        return 0.0
    return (gozlenen - L * p) / (math.sqrt(L * p * (1 - p)) or 1e-9)


def _sinif(z: float, alt: float = -0.75, ust: float = 0.75) -> str:
    if z < alt:
        return "zayif"
    if z <= ust:
        return "dengeli"
    return "baskin"


@dataclass(frozen=True)
class EksenOkuma:
    anahtar: str
    ad: str
    sayilar: tuple[int, ...]
    toplam: int
    beklenen: float
    z: float
    sinif: str
    metin: str


@dataclass(frozen=True)
class DengeOkuma:
    tek_toplam: int
    cift_toplam: int
    tek_z: float
    tek_cift_sinif: str            # tek_agir | dengeli | cift_agir
    tek_cift_metni: str
    eksenler: tuple[EksenOkuma, ...]

    @property
    def agirlik_merkezi(self) -> EksenOkuma | None:
        baskinlar = [e for e in self.eksenler if e.sinif == "baskin"]
        return max(baskinlar, key=lambda e: e.z) if baskinlar else None

    @property
    def zayif_eksenler(self) -> tuple[EksenOkuma, ...]:
        return tuple(e for e in self.eksenler if e.sinif == "zayif")


def denge_hesapla(tablo: KapsamTablosu) -> DengeOkuma:
    taban = yukle("taban-oranlar")
    veri = yukle("denge")
    p = taban["harf_olasiligi"]
    L = tablo.harf_sayisi
    f = tablo.frekanslar

    tek_toplam = sum(f[n] for n in TEK)
    cift_toplam = sum(f[n] for n in CIFT)
    p_tek = sum(p[str(n)] for n in TEK)
    tek_z = _z(tek_toplam, L, p_tek)

    if tek_z > 0.75:
        tc = "tek_agir"
    elif tek_z < -0.75:
        tc = "cift_agir"
    else:
        tc = "dengeli"

    eksenler = []
    for anahtar, e in veri["ucul_eksenler"]["eksenler"].items():
        sayilar = tuple(e["sayilar"])
        toplam = sum(f[n] for n in sayilar)
        p_e = sum(p[str(n)] for n in sayilar)
        z = _z(toplam, L, p_e)
        sinif = _sinif(z)
        eksenler.append(EksenOkuma(
            anahtar=anahtar, ad=e["ad"], sayilar=sayilar, toplam=toplam,
            beklenen=round(L * p_e, 2), z=round(z, 2), sinif=sinif,
            metin=e[sinif],
        ))

    return DengeOkuma(
        tek_toplam=tek_toplam,
        cift_toplam=cift_toplam,
        tek_z=round(tek_z, 2),
        tek_cift_sinif=tc,
        tek_cift_metni=veri["tek_cift"]["metinler"][tc],
        eksenler=tuple(eksenler),
    )


@dataclass(frozen=True)
class PlanOkuma:
    anahtar: str
    ad: str
    sayim: int
    beklenen: float
    z: float
    sinif: str
    metin: str


def planlar_hesapla(tablo: KapsamTablosu) -> tuple[PlanOkuma, ...]:
    """Harf tabanli Ifade Planlari.

    data/ifade-planlari.json icindeki harf gruplamasi kaynaklar arasinda
    degistigi icin DOGRULANMAMIS olarak isaretlidir. 'etkin': false oldugu
    surece bu fonksiyon bos donus verir ve rapor bolumu basilmaz.
    """
    veri = yukle("ifade-planlari")
    if not veri.get("etkin"):
        return ()

    duz = tablo.ad_duz
    L = len(duz)
    if L == 0:
        return ()

    toplam_harf = sum(len(g) for g in veri["harf_gruplari"].values())
    okumalar = []
    for anahtar, harfler in veri["harf_gruplari"].items():
        kume = set(harfler)
        sayim = sum(1 for h in duz if h in kume)
        # Beklenti, grubun alfabedeki payina gore; harf sikligi agirliklandirmasi
        # ancak gruplama onaylandiktan sonra eklenmelidir.
        p = len(kume) / toplam_harf
        z = _z(sayim, L, p)
        sinif = _sinif(z)
        bilgi = veri["planlar"][anahtar]
        okumalar.append(PlanOkuma(
            anahtar=anahtar, ad=bilgi["ad"], sayim=sayim,
            beklenen=round(L * p, 2), z=round(z, 2), sinif=sinif,
            metin=bilgi[sinif],
        ))
    return tuple(okumalar)
