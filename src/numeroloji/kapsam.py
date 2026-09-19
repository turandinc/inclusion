"""Kapsam tablosu (inclusion table) ve turevleri.

Bu modul SAYILARI uretir, metin secmez. Metin kompozisyonu rapor.py'nin isidir.

Disiplin acisindan kritik iki karar burada uygulanir:

1. FREKANS NORMALIZASYONU. Bir frekansin anlami mutlak degil, o sayinin ad
   uzunluguna gore beklenen ortalamasina goredir. Sayim ~Binom(L, p_n) kabul
   edilir ve z-skoru ile bes sinifa ayrilir:
   eksik / normalin_alti / dengeli / normalin_ustu / asiri.
   Boylece "4 frekansi" kisa bir adda yogunlasma, uzun bir adda normalin alti
   olarak okunabilir.

2. TELAFI VE SIDDET. Sifir frekans, ayni sayi cekirdekte varsa Karmik Ders
   olmaktan cikar (telafi edilmis ders). Ayrica taban orani yuksek eksiklikler
   kusaksal tema olarak isaretlenir; kisisel ders diliyle anlatilmaz.
"""

from __future__ import annotations

import collections
import math
from dataclasses import dataclass

from .cekirdek import CekirdekSayilar, Kisi, cekirdek_hesapla
from .harf import HarfHaritasi, normalize
from .veri import yukle

#: Frekans siniflari, en zayiftan en yogununa.
SINIFLAR = ("eksik", "normalin_alti", "dengeli", "normalin_ustu", "asiri")

#: Kullaniciya basilan etiketler. Sinif anahtarlari ic slug'dir; rapora
#: dogrudan basilmaz.
SINIF_ETIKETLERI = {
    "eksik": "eksik",
    "normalin_alti": "normalin altında",
    "dengeli": "dengeli",
    "normalin_ustu": "normalin üstünde",
    "asiri": "aşırı",
}


@dataclass(frozen=True)
class HucreOkuma:
    """Tablonun tek bir sayisi icin nicel okuma."""

    sayi: int
    frekans: int
    beklenen: float
    z: float
    sinif: str

    #: Yalnizca sinif == "eksik" oldugunda anlamli alanlar:
    taban_orani: float = 0.0
    siddet: str = ""               # kisisel | yaygin | kolektif
    telafi_edildi: bool = False
    telafi_kaynaklari: tuple[str, ...] = ()

    @property
    def karmik_ders_mi(self) -> bool:
        """Gercek Karmik Ders: frekans sifir VE cekirdekte telafi yok."""
        return self.sinif == "eksik" and not self.telafi_edildi

    @property
    def etiket(self) -> str:
        """Kullaniciya basilan sinif adi."""
        return SINIF_ETIKETLERI[self.sinif]

    @property
    def metin_varyanti(self) -> str:
        """Eksik hucrelerde hangi metin varyantinin okunacagi."""
        if self.sinif != "eksik":
            return "hucre"
        if self.telafi_edildi:
            return "telafili"
        return "kolektif" if self.siddet in ("kolektif", "yaygin") else "kisisel"


@dataclass(frozen=True)
class KapsamTablosu:
    ad_duz: str
    harf_sayisi: int
    frekanslar: dict[int, int]
    okumalar: dict[int, HucreOkuma]
    cekirdek: CekirdekSayilar

    #: En yuksek frekansli sayi (Gizli Tutku / passion cachee).
    gizli_tutku: int
    #: Gizli Tutku esitlik durumunda birlikte zirvede olan sayilar.
    gizli_tutku_ortaklari: tuple[int, ...]
    #: Zirvenin ne kadar baskin oldugu: "belirgin" | "paylasimli" | "duz"
    gizli_tutku_karakteri: str

    @property
    def karmik_dersler(self) -> list[int]:
        return [n for n, o in sorted(self.okumalar.items()) if o.karmik_ders_mi]

    @property
    def telafi_edilmis_dersler(self) -> list[int]:
        return [n for n, o in sorted(self.okumalar.items())
                if o.sinif == "eksik" and o.telafi_edildi]

    @property
    def asiri_sayilar(self) -> list[int]:
        return [n for n, o in sorted(self.okumalar.items()) if o.sinif == "asiri"]

    def sinif_dagilimi(self) -> dict[str, list[int]]:
        d: dict[str, list[int]] = {s: [] for s in SINIFLAR}
        for n, o in sorted(self.okumalar.items()):
            d[o.sinif].append(n)
        return d


def _sinif_belirle(frekans: int, beklenen: float, z: float, esikler: dict) -> str:
    if frekans == 0:
        return "eksik"
    if z < esikler["normalin_alti"]:
        return "normalin_alti"
    if z <= esikler["dengeli_ust"]:
        return "dengeli"
    if z <= esikler["normalin_ustu_ust"]:
        return "normalin_ustu"
    return "asiri"


def kapsam_hesapla(
    kisi: Kisi,
    hm: HarfHaritasi | None = None,
    cekirdek: CekirdekSayilar | None = None,
    ad: str | None = None,
) -> KapsamTablosu:
    """Kisi icin kapsam tablosunu uretir.

    ad : None ise kisi.dogum_adi kullanilir. Ikincil tablolar (kullanilan ad,
         evlilik soyadi) icin acikca gecilebilir; o durumda telafi/siddet
         alanlari yine dogum cekirdegi uzerinden hesaplanir.
    """
    hm = hm or HarfHaritasi.varsayilan()
    cekirdek = cekirdek or cekirdek_hesapla(kisi, hm)
    taban = yukle("taban-oranlar")
    esikler = taban["esikler"]

    duz = normalize(ad if ad is not None else kisi.dogum_adi, hm)
    if not duz:
        raise ValueError("Ad, harf haritasinda karsiligi olan hic harf icermiyor.")

    sayimlar: collections.Counter[int] = collections.Counter()
    for h in duz:
        n = hm.sayi(h)
        if n is not None:
            sayimlar[n] += 1

    L = sum(sayimlar.values())
    okumalar: dict[int, HucreOkuma] = {}

    for n in range(1, 10):
        f = sayimlar[n]
        p = taban["harf_olasiligi"][str(n)]
        beklenen = L * p
        sapma = math.sqrt(L * p * (1 - p)) or 1e-9
        z = (f - beklenen) / sapma
        sinif = _sinif_belirle(f, beklenen, z, esikler)

        if sinif == "eksik":
            kaynaklar = tuple(cekirdek.telafi_kaynaklari(n))
            okumalar[n] = HucreOkuma(
                sayi=n, frekans=f, beklenen=round(beklenen, 2), z=round(z, 2),
                sinif=sinif,
                taban_orani=taban["sifir_orani"][str(n)],
                siddet=taban["siddet_sinifi"][str(n)],
                telafi_edildi=bool(kaynaklar),
                telafi_kaynaklari=kaynaklar,
            )
        else:
            okumalar[n] = HucreOkuma(
                sayi=n, frekans=f, beklenen=round(beklenen, 2), z=round(z, 2),
                sinif=sinif,
            )

    en_yuksek = max(sayimlar.values())
    zirve = tuple(sorted(n for n, v in sayimlar.items() if v == en_yuksek))
    ikinci = sorted(sayimlar.values(), reverse=True)
    fark = en_yuksek - (ikinci[1] if len(ikinci) > 1 else 0)
    if len(zirve) > 1:
        karakter = "paylasimli"
    elif fark >= 2:
        karakter = "belirgin"
    else:
        karakter = "duz"

    return KapsamTablosu(
        ad_duz=duz,
        harf_sayisi=L,
        frekanslar={n: sayimlar[n] for n in range(1, 10)},
        okumalar=okumalar,
        cekirdek=cekirdek,
        gizli_tutku=zirve[0],
        gizli_tutku_ortaklari=zirve,
        gizli_tutku_karakteri=karakter,
    )
