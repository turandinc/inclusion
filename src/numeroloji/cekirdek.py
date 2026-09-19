"""Cekirdek sayilar: Kapsam tablosunun telafi kuralinin dayandigi sayilar.

Karmik Ders okumasi tek basina tablodan yapilamaz. Disiplinde bir sayinin tabloda
sifir olmasi Karmik Ders'tir ANCAK o sayi cekirdek sayilarda yoksa. Cekirdekte
varsa ders zaten calisilmaktadir ve okuma belirgin sekilde yumusar.

Bu modul telafi kumesini uretir. inclusion.md korpusunun kendi icinde iki yerde
kazara belirmis olan bu kurali (2|0 satirindaki "11'in varligi bu eksikligi
telafi edecek" ve 1|0 satirindaki "Ocak ya da Ekim aylarinda dogduysan")
sistematik hale getirir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .harf import HarfHaritasi, harf_sayilari, indirge, sesli_sessiz_ayir

USTA_SAYILAR = (11, 22, 33)


def _tarih_coz(dogum_tarihi: str | date) -> date:
    if isinstance(dogum_tarihi, date):
        return dogum_tarihi
    return date.fromisoformat(dogum_tarihi.strip())


@dataclass(frozen=True)
class Kisi:
    """Hesaplamanin girdisi.

    dogum_adi : nufus kaydindaki tam ad (tum on adlar + dogum soyadi).
    dogum_tarihi : ISO 8601 (YYYY-MM-DD) ya da datetime.date.
    kullanilan_ad : varsa gunluk hayatta kullanilan ad (ikincil tablo icin).
    """

    dogum_adi: str
    dogum_tarihi: str | date
    kullanilan_ad: str | None = None

    @property
    def tarih(self) -> date:
        return _tarih_coz(self.dogum_tarihi)


@dataclass(frozen=True)
class CekirdekSayilar:
    yasam_yolu: int
    ifade: int
    ruh_arzusu: int
    kisilik: int
    dogum_gunu: int
    dogum_ayi: int
    olgunluk: int

    #: Telafi testinde kullanilan, usta sayilar indirgenmis kume.
    telafi_kumesi: frozenset[int] = field(default_factory=frozenset)

    def telafi_eder_mi(self, sayi: int) -> bool:
        """`sayi` cekirdekte (dogrudan ya da usta sayi indirgemesiyle) var mi?"""
        return sayi in self.telafi_kumesi

    def telafi_kaynaklari(self, sayi: int) -> list[str]:
        """`sayi`yi telafi eden cekirdek sayilarin okunabilir adlari."""
        etiketler = {
            "yasam_yolu": "Yaşam Yolu",
            "ifade": "İfade (Kader)",
            "ruh_arzusu": "Ruh Arzusu",
            "kisilik": "Kişilik",
            "dogum_gunu": "Doğum Günü",
            "dogum_ayi": "Doğum Ayı",
            "olgunluk": "Olgunluk",
        }
        bulunan = []
        for alan, etiket in etiketler.items():
            deger = getattr(self, alan)
            if deger == sayi or (deger in USTA_SAYILAR and indirge([deger], usta_koru=False) == sayi):
                usta = " (usta sayı %d)" % deger if deger in USTA_SAYILAR else ""
                bulunan.append(f"{etiket}{usta}")
        return bulunan


def cekirdek_hesapla(kisi: Kisi, hm: HarfHaritasi | None = None) -> CekirdekSayilar:
    hm = hm or HarfHaritasi.varsayilan()
    t = kisi.tarih

    yasam_yolu = indirge([int(c) for c in f"{t.year:04d}{t.month:02d}{t.day:02d}"])
    ifade = indirge(harf_sayilari(kisi.dogum_adi, hm))

    sesli, sessiz = sesli_sessiz_ayir(kisi.dogum_adi, hm)
    ruh_arzusu = indirge([hm.sayi(h) for h in sesli if hm.sayi(h)])
    kisilik = indirge([hm.sayi(h) for h in sessiz if hm.sayi(h)])

    dogum_gunu = indirge([int(c) for c in str(t.day)])
    dogum_ayi = indirge([int(c) for c in str(t.month)])
    olgunluk = indirge([yasam_yolu, ifade])

    hepsi = [yasam_yolu, ifade, ruh_arzusu, kisilik, dogum_gunu, dogum_ayi, olgunluk]
    telafi: set[int] = set()
    for d in hepsi:
        telafi.add(d)
        if d in USTA_SAYILAR:
            telafi.add(indirge([d], usta_koru=False))

    return CekirdekSayilar(
        yasam_yolu=yasam_yolu,
        ifade=ifade,
        ruh_arzusu=ruh_arzusu,
        kisilik=kisilik,
        dogum_gunu=dogum_gunu,
        dogum_ayi=dogum_ayi,
        olgunluk=olgunluk,
        telafi_kumesi=frozenset(telafi),
    )
