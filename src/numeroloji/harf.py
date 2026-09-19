"""Harf normalizasyonu ve harf -> sayi cevrimi.

Turkce diakritik karari data/harf-haritasi.json icinde belgelenmistir; bu modul
o karari uygular, kendi basina bir tercih dayatmaz.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Iterable

from .veri import yukle


@dataclass(frozen=True)
class HarfHaritasi:
    """Etkin harf semasi. Varsayilan olarak data dosyasindaki 'etkin_sema'."""

    harita: dict[str, int]
    katlama: dict[str, str]
    sesliler: frozenset[str]
    sema_adi: str

    @classmethod
    def varsayilan(cls, sema: str | None = None) -> "HarfHaritasi":
        veri = yukle("harf-haritasi")
        sema = sema or veri["etkin_sema"]
        if sema not in veri["semalar"]:
            raise ValueError(f"Bilinmeyen sema: {sema}")
        s = veri["semalar"][sema]
        return cls(
            harita=s["harita"],
            katlama=s["katlama"],
            sesliler=frozenset(veri["sesli_harfler"]["sesliler"]),
            sema_adi=sema,
        )

    def sayi(self, harf: str) -> int | None:
        """Tek bir (normalize edilmis) harfin sayisi; haritada yoksa None."""
        return self.harita.get(harf)


def _buyut(metin: str) -> str:
    """Turkce'ye duyarli buyutme: 'i' -> 'İ', 'ı' -> 'I'."""
    return metin.replace("i", "İ").replace("ı", "I").upper()


def normalize(ad: str, hm: HarfHaritasi | None = None) -> str:
    """Adi tablo icin kullanilabilir harf dizisine indirger.

    - Turkce'ye duyarli buyutur.
    - Tire, kesme, nokta, bosluk ve rakamlari atar.
    - Harita disi diakritikleri katlar (Ç -> C gibi).
    - Katlama sonrasi da haritada olmayan harfleri (or. baska alfabeler) atar.
    """
    hm = hm or HarfHaritasi.varsayilan()
    ad = _buyut(ad)

    cikti: list[str] = []
    for ch in ad:
        if ch in hm.katlama:
            cikti.extend(hm.katlama[ch])
            continue
        if ch in hm.harita:
            cikti.append(ch)
            continue
        # Bilesik diakritikleri (A + birlesen aksan) ayirip tabanini dene.
        ayrik = unicodedata.normalize("NFD", ch)
        taban = "".join(c for c in ayrik if not unicodedata.combining(c))
        if taban in hm.katlama:
            cikti.extend(hm.katlama[taban])
        elif taban in hm.harita:
            cikti.append(taban)
        # Geri kalan her sey (bosluk, tire, rakam, noktalama) sessizce atilir.
    return "".join(cikti)


def harf_sayilari(ad: str, hm: HarfHaritasi | None = None) -> list[int]:
    """Adin harflerinin sayi karsiliklarini sirayla dondurur."""
    hm = hm or HarfHaritasi.varsayilan()
    return [n for n in (hm.sayi(h) for h in normalize(ad, hm)) if n is not None]


def sesli_sessiz_ayir(ad: str, hm: HarfHaritasi | None = None) -> tuple[str, str]:
    """Normalize edilmis addan (sesliler, sessizler) ikilisi uretir.

    Turkce'de Y her zaman sessizdir (data/harf-haritasi.json: y_seslimi=false).
    Katlama sonrasi İ -> I oldugu icin sesli kumesi katlanmis haliyle test edilir.
    """
    hm = hm or HarfHaritasi.varsayilan()
    katlanmis_sesliler = {
        hm.katlama.get(s, s) if hm.katlama.get(s, s) in hm.harita else s
        for s in hm.sesliler
    }
    duz = normalize(ad, hm)
    sesli = "".join(h for h in duz if h in katlanmis_sesliler)
    sessiz = "".join(h for h in duz if h not in katlanmis_sesliler)
    return sesli, sessiz


def indirge(sayilar: Iterable[int], usta_koru: bool = True) -> int:
    """Toplami tek haneye indirger.

    usta_koru=True ise 11, 22 ve 33 ara toplamlari korunur (usta sayilar).
    """
    toplam = sum(sayilar)
    while toplam > 9:
        if usta_koru and toplam in (11, 22, 33):
            return toplam
        toplam = sum(int(c) for c in str(toplam))
    return toplam
