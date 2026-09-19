#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/taban-oranlar.json uretir.

Iki seyi olcer:

1. BEKLENEN FREKANS TEMELI. Bir sayinin tabloda kac kez cikmasinin "normal"
   oldugu, ad uzunlugundan bagimsiz degildir. Turkce ad korpusundaki harf
   dagilimindan her sayi icin p(n) olasiligi cikarilir; L harfli bir ad icin
   beklenti L*p(n) olur. Boylece Anglo-Sakson ekolunun 15 harflik ada gore
   sabitlenmis beklenti tablosu ithal edilmez, Turkce'nin kendi dagilimi
   kullanilir.

2. TABAN ORAN (base rate). Bir sayinin Turkce adlarda hic cikmama olasiligi.
   Karmik Ders'in siddeti buna gore olceklenir: neredeyse herkeste olan bir
   eksiklik kisisel bir ders degil, kusaksal bir temadir.

Kullanim:  python3 scripts/taban_oran_uret.py
"""

from __future__ import annotations

import collections
import itertools
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from numeroloji.harf import HarfHaritasi, normalize  # noqa: E402

ON_ADLAR = """
MEHMET MUSTAFA AHMET ALİ HÜSEYİN HASAN İBRAHİM İSMAİL OSMAN YUSUF MURAT ÖMER
RAMAZAN SÜLEYMAN ABDULLAH RECEP FATİH MAHMUT HALİL İSMET KADİR BEKİR YAŞAR
SERKAN EMRE BURAK ONUR VOLKAN OKAN KEMAL CEMAL ORHAN ERKAN ERDAL ERHAN ERSİN
TOLGA TUNCAY UĞUR ÜMİT YAVUZ ZEKİ SİNAN SELİM SAMET OKTAY NURİ NECATİ MESUT
LEVENT KÜRŞAT KORAY KAAN İLKER HAKAN GÖKHAN FURKAN FERHAT ENES CAN CEM BARIŞ
ARDA ALPER ADEM TAYFUN SEFA RAİF POLAT NİHAT METİN MERT KUTAY İLHAN HÜSNÜ
GÜRKAN GÖKSEL FIRAT ERGÜN DOĞAN DENİZ CÜNEYT BÜLENT ATİLLA ASLAN ARİF
FATMA AYŞE EMİNE HATİCE ZEYNEP ELİF MERYEM ŞERİFE SULTAN HAVVA ASİYE ZEHRA
YASEMİN ÖZLEM SEVGİ SEHER SEDA SEVİM NURTEN NURAY MELEK MERVE LEYLA KADRİYE
HÜLYA HÜSNİYE GÜLSÜM GÜLTEN GÜLNAZ FİLİZ FADİME ESRA DERYA CANAN BETÜL BAHAR
AYTEN AYNUR AYLA ARZU AYBÜKE AZRA BEYZA BUSE CEREN CEMİLE DİLEK DUYGU EBRU
ECE EDA ELA EMEL ESMA EYLÜL FEYZA GAMZE GİZEM GÖNÜL GÜLAY HANDE HİLAL İKRA
İREM KEZBAN LALE MELİKE NAZLI NESLİHAN NİLÜFER PELİN PINAR RABİA RUKİYE SELİN
SEMA SİBEL SONGÜL ŞENGÜL TUĞBA TÜLAY ÜMMÜ YAĞMUR YELİZ ZAHİDE ZÜBEYDE
""".split()

IKINCI_ADLAR = ["", "", "", "NUR", "CAN", "EMRE", "GÜL", "HAN", "BETÜL", "KEREM",
                "ALİ", "AYŞE", "EDA", "SU", "NAZ", "DENİZ", "ÖZ", "SENA"]

SOYADLAR = """
YILMAZ KAYA DEMİR ŞAHİN ÇELİK YILDIZ YILDIRIM ÖZTÜRK AYDIN ÖZDEMİR ARSLAN DOĞAN
KILIÇ ASLAN ÇETİN KARA KOÇ KURT ÖZKAN ŞİMŞEK POLAT ÖZCAN KORKMAZ ERDOĞAN
AKSOY GÜLER BOZKURT ÇAKIR TÜRK AVCI KOCA ERDEM GÜNEŞ YAVUZ ÖZER DURSUN ATEŞ
BULUT KESKİN AKTAŞ KAPLAN ALTUN ERGÜN SOYSAL TOPAL ÜNAL USTA UYSAL YÜCEL
ZENGİN ÇOBAN DEMİRCİ EKİNCİ ERİŞ FİDAN GÜMÜŞ HATİPOĞLU IŞIK KAHRAMAN LALE
MUTLU NALBANT ORHAN PEKER SARI TAŞ ULUSOY VAROL YEŞİL AKIN BAYRAM CEYLAN
DİNÇER EROL GENÇ HAKSEVER İNCE KARAHASANOĞLU ABDÜLKADİROĞLU ÖZDEMİRCİOĞLU
SERTKAYA TOPRAK UÇAR VURAL YALÇIN ŞENGÜL ÇALIŞKAN GÜRBÜZ KOŞAR MENTEŞE
NARİN OKUR PARLAK SAĞLAM TUNÇ UZUN YENER ALKAN BİLGİN CİVAN DALKILIÇ
EFE FERİDUN GÖKÇE HANÇER İLHAN KAVAK LİMAN MERCAN NAZLI OĞUZ PAMUK
""".split()


def uret() -> dict:
    hm = HarfHaritasi.varsayilan()
    harf_sayaci: collections.Counter[int] = collections.Counter()
    toplam_harf = 0
    sifir: collections.Counter[int] = collections.Counter()
    gizli_tutku: collections.Counter[int] = collections.Counter()
    ad_uzunluklari: list[int] = []
    ornek = 0

    for on, iki, soy in itertools.product(ON_ADLAR, IKINCI_ADLAR, SOYADLAR):
        duz = normalize(f"{on}{iki}{soy}", hm)
        if not duz:
            continue
        f: collections.Counter[int] = collections.Counter()
        for h in duz:
            n = hm.sayi(h)
            if n is not None:
                f[n] += 1
                harf_sayaci[n] += 1
                toplam_harf += 1
        ornek += 1
        ad_uzunluklari.append(len(duz))
        for n in range(1, 10):
            if f[n] == 0:
                sifir[n] += 1
        # Gizli Tutku: en yuksek frekans; esitlikte kucuk sayi kazanir (gelenek).
        en = max(f.values())
        gizli_tutku[min(k for k, v in f.items() if v == en)] += 1

    olasilik = {str(n): harf_sayaci[n] / toplam_harf for n in range(1, 10)}
    taban = {str(n): sifir[n] / ornek for n in range(1, 10)}
    ort_uzunluk = sum(ad_uzunluklari) / len(ad_uzunluklari)

    # Siddet etiketi: taban oran yuksekse eksiklik kisisel degil kusaksaldir.
    def siddet(oran: float) -> str:
        if oran >= 0.35:
            return "kolektif"
        if oran >= 0.18:
            return "yaygin"
        return "kisisel"

    return {
        "surum": "1.0",
        "uretim": {
            "betik": "scripts/taban_oran_uret.py",
            "sema": hm.sema_adi,
            "ornek_sayisi": ornek,
            "on_ad": len(ON_ADLAR),
            "soyad": len(SOYADLAR),
            "ortalama_ad_uzunlugu": round(ort_uzunluk, 2),
            "not": "Korpus yaygin Turk on ad ve soyadlarinin capraz carpimidir; nufus dagilimina gore agirliklandirilmamistir. Oranlar buyukluk mertebesi icin kullanilir, nufus istatistigi olarak sunulmaz.",
        },
        "harf_olasiligi": {k: round(v, 5) for k, v in olasilik.items()},
        "sifir_orani": {k: round(v, 4) for k, v in taban.items()},
        "siddet_sinifi": {str(n): siddet(taban[str(n)]) for n in range(1, 10)},
        "gizli_tutku_dagilimi": {
            str(n): round(gizli_tutku[n] / ornek, 4) for n in range(1, 10)
        },
        "esikler": {
            "aciklama": "Frekans sinifi, sayimin Binom(L, p_n) beklentisinden z-skoru ile belirlenir.",
            "normalin_alti": -0.75,
            "dengeli_ust": 0.75,
            "normalin_ustu_ust": 1.75,
        },
    }


if __name__ == "__main__":
    veri = uret()
    hedef = KOK / "data" / "taban-oranlar.json"
    hedef.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"yazildi: {hedef}  ({veri['uretim']['ornek_sayisi']} ornek)")
    print("\nsayi  p(harf)  sifir orani  siddet     gizli tutku")
    for n in map(str, range(1, 10)):
        print(f"  {n}    {veri['harf_olasiligi'][n]:.3f}      {veri['sifir_orani'][n]:6.1%}   "
              f"{veri['siddet_sinifi'][n]:<10} {veri['gizli_tutku_dagilimi'][n]:6.1%}")
