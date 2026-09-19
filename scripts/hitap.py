#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hitap donusumu: 2. cogul (siz) -> 2. tekil (sen).

Korpus 2.0 tek bir seste yazildi (siz). Uretimdeki numeroloji raporu ise bastan
sona 'sen' ile konusuyor; kapsam tablosu o rapora gomulecegi icin ses rapora
uydurulur. Tek ses ilkesi korunur, yalnizca secilen ses degisir (bkz.
docs/METODOLOJI.md, ses karari).

Kural cekirdegi: Turkce'de 2. cogul iyelik ve kisi ekleri 'n + unlu + z'
biciminde (-niz/-niz/-nuz/-nuz, -siniz, -seniz, -diniz ...). 'z' ile onundeki
unlu duser, tekil bicim kalir:
    alirsiniz -> alirsin     tablonuzda -> tablonda     adiniza -> adina
Kurala uymayanlar asagida ACIKCA listelenir: zamirler, emir kipi ve kokunde
tesadufen 'niz' gecen kelimeler.

Kullanim:
    python3 scripts/hitap.py            data/*.json icindeki metinleri donusturur
    python3 scripts/hitap.py --kontrol  donusturulmemis 'siz' bicimi varsa 1 doner
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]

#: Zamirler (kelimenin tamami).
ZAMIRLER = {
    "siz": "sen", "size": "sana", "sizi": "seni", "sizin": "senin",
    "sizde": "sende", "sizden": "senden", "sizce": "sence",
    "sizinle": "seninle", "sizler": "sen", "sizlere": "sana",
}

#: 2. cogul emir kipi -> tekil emir (kelimenin tamami). Emir kipi -in/-yin ile
#: biter ve iyelik/tamlayan ekleriyle bicimce karisir; bu yuzden kurala
#: birakilmaz, tek tek listelenir.
EMIRLER = {
    "almayın": "alma", "büyütmeyin": "büyütme", "deneyin": "dene",
    "gelmeyin": "gelme", "olmayın": "olma", "reddetmeyin": "reddetme",
    "araştırın": "araştır", "ayırın": "ayır", "bitirin": "bitir",
    "edin": "et", "götürün": "götür", "karşılaştırın": "karşılaştır",
    "kaydedin": "kaydet", "kullanın": "kullan", "olun": "ol", "sayın": "say",
    "seçin": "seç", "tutun": "tut", "yapın": "yap", "yazın": "yaz",
    "öğrenin": "öğren", "üstlenin": "üstlen",
}

#: Kokunde 'n + unlu + z' gecen ama 2. cogul olmayan kelimeler. Kucuk harfle,
#: kelime basi eslesmesi (yalniz -> yalnizca, yalnizlik ...).
ISTISNA_KOKLER = ("yalnız", "henüz", "organiz", "deniz", "semiz", "kaniz")

_CEKIRDEK = re.compile(r"n[ıiuü]z")
#: Olumsuz cogul emir (-mayin/-meyin) bicimce belirsiz degildir: her zaman
#: emirdir ('yapmayin' -> 'yapma'). 'mayin' (mayin tarlasi) gibi kisa
#: kelimeler disarida kalsin diye kok en az iki harf olmali.
_SEN_DIR = re.compile(r"(s[ıiuü]n)d[ıiuü]r$")
_OLUMSUZ_EMIR = re.compile(r"^(.{2,}m[ae])y[ıi]n$")
_KELIME = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüâîûÂÎÛ]+")


def _kucuk(k: str) -> str:
    return k.replace("I", "ı").replace("İ", "i").lower()


def _harf_uydur(ornek: str, yeni: str) -> str:
    if ornek[:1].isupper():
        ilk = yeni[:1]
        ilk = {"i": "İ", "ı": "I"}.get(ilk, ilk.upper())
        return ilk + yeni[1:]
    return yeni


def kelime_cevir(k: str) -> str:
    kk = _kucuk(k)
    if kk in ZAMIRLER:
        return _harf_uydur(k, ZAMIRLER[kk])
    if kk in EMIRLER:
        return _harf_uydur(k, EMIRLER[kk])
    if kk.startswith(ISTISNA_KOKLER):
        return k
    m = _OLUMSUZ_EMIR.match(k)
    if m:
        return m.group(1)
    # 'z' ve onundeki unluyu at; 'n' kalir. Bir kelimede en fazla bir kez
    # gecer (iyelik + kisi eki birlikte gelmez), yine de hepsini degistir.
    yeni = _CEKIRDEK.sub("n", k)
    # 'zorundasinizdir' -> 'zorundasindir' dogru ama 'sen' hitabinda yapay
    # durur; tekilde kesinlik eki dusurulur: 'zorundasin'.
    if yeni != k:
        yeni = _SEN_DIR.sub(r"\1", yeni)
    return yeni


def cevir(metin: str) -> str:
    return _KELIME.sub(lambda m: kelime_cevir(m.group(0)), metin)


def kalan_cogul(metin: str) -> list[str]:
    """Donusumden sonra hala 2. cogul gorunen kelimeler (bos = temiz)."""
    kalan = []
    for m in _KELIME.finditer(metin):
        k = m.group(0)
        kk = _kucuk(k)
        if kk in ZAMIRLER or kk in EMIRLER or _OLUMSUZ_EMIR.match(kk):
            kalan.append(k)
        elif _CEKIRDEK.search(kk) and not kk.startswith(ISTISNA_KOKLER):
            kalan.append(k)
    return kalan


# ---------------------------------------------------------------------------
# data/*.json uzerinde uygulama
# ---------------------------------------------------------------------------

#: Musteri metni olmayan, belgeleme amacli alanlar: dokunulmaz.
META_ALANLAR = {
    "aciklama", "revizyon_notu", "not", "gerekce", "tanim_notu", "kaynak", "uyari",
    "kutup_turetme_notu", "uretim", "varyantlar", "tetikleme", "ad_kaynagi",
    "kaynak_dogrulamasi", "surum", "temalar", "anahtar", "kutup", "tanim",
}

#: harf-haritasi ve taban-oranlar metin tasimaz.
METIN_DOSYALARI = (
    "kapsam-hucreleri", "karmik-dersler", "yogunluk", "gizli-tutku",
    "denge", "sentez", "ifade-planlari",
)


def _gez(o, fn, alan=None):
    if isinstance(o, dict):
        return {k: (v if k in META_ALANLAR else _gez(v, fn, k)) for k, v in o.items()}
    if isinstance(o, list):
        return [_gez(v, fn, alan) for v in o]
    if isinstance(o, str):
        return fn(o)
    return o


def dosya_cevir(veri: dict) -> dict:
    return _gez(veri, cevir)


def dosya_kalan(veri: dict) -> list[str]:
    kalan: list[str] = []
    _gez(veri, lambda s: kalan.extend(kalan_cogul(s)) or s)
    return kalan


_JSON_DIZE = re.compile(r'"(?:[^"\\]|\\.)*"')


def ham_cevir(kaynak: str) -> str:
    """JSON metnini BICIMINI KORUYARAK donusturur: yalnizca meta olmayan
    alanlardaki dize degerleri degisir; girinti, satir kirilimi ve anahtar
    sirasi aynen kalir (elle bakilan dosyalarda diff okunur kalsin diye).

    Kucuk bir tarayici: her dize icin, onu kapsayan anahtar zincirini izler.
    """
    cikti: list[str] = []
    yigin: list[str | None] = []   # her acik { / [ icin onu acan anahtar
    son_anahtar: str | None = None
    i = 0
    while i < len(kaynak):
        ch = kaynak[i]
        if ch == '"':
            m = _JSON_DIZE.match(kaynak, i)
            ham = m.group(0)
            j = m.end()
            k = j
            while k < len(kaynak) and kaynak[k] in " \t\r\n":
                k += 1
            if k < len(kaynak) and kaynak[k] == ":":
                son_anahtar = json.loads(ham)          # anahtar
                cikti.append(ham)
            else:
                # Nesnede deger -> son anahtar; dizide son_anahtar None'dir
                # ('[' acilinca sifirlanir), zincir yigindan gelir.
                zincir = [a for a in yigin if a] + ([son_anahtar] if son_anahtar else [])
                if any(a in META_ALANLAR for a in zincir):
                    cikti.append(ham)
                else:
                    yeni = cevir(json.loads(ham))
                    cikti.append(ham if yeni == json.loads(ham)
                                 else json.dumps(yeni, ensure_ascii=False))
            i = j
            continue
        if ch in "{[":
            yigin.append(son_anahtar)
            son_anahtar = None
        elif ch in "}]":
            yigin.pop()
            son_anahtar = None
        cikti.append(ch)
        i += 1
    return "".join(cikti)


def main(argv: list[str]) -> int:
    kontrol = "--kontrol" in argv
    hata = 0
    for ad in METIN_DOSYALARI:
        yol = KOK / "data" / f"{ad}.json"
        ham = yol.read_text(encoding="utf-8")
        veri = json.loads(ham)
        if kontrol:
            kalan = dosya_kalan(veri)
            if kalan:
                hata += 1
                print(f"{ad}: {len(kalan)} cogul bicim: {sorted(set(kalan))[:20]}")
            continue
        yeni_ham = ham_cevir(ham)
        # Guvenlik: bicim koruyan yol, agac yoluyla ayni veriyi uretmeli.
        if json.loads(yeni_ham) != dosya_cevir(veri):
            print(f"HATA: {ad} icin iki yol farkli sonuc verdi", file=sys.stderr)
            return 2
        yol.write_text(yeni_ham, encoding="utf-8")
        print(f"donusturuldu: {yol.name}")
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
