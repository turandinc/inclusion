# -*- coding: utf-8 -*-
"""Tum test kumesi. Bagimlilik yok: python3 -m unittest discover -s tests

Testler uc seye bakar:
  1. Hesaplamanin dogrulugu (harf, cekirdek, kapsam, denge).
  2. Yorum kurallarinin uygulandigi (telafi, siddet, yogunluk kayitlari).
  3. ICERIK REGRESYONU: 1.0 surumunden kaldirilan zararli ifadelerin ve ceviri
     hatalarinin geri gelmedigi. Bu sinif, korpus elle duzenlendiginde
     kaybedilmesi en kolay kazanimi korur.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from numeroloji import Kisi, rapor_uret  # noqa: E402
from numeroloji.cekirdek import cekirdek_hesapla  # noqa: E402
from numeroloji.harf import HarfHaritasi, harf_sayilari, indirge, normalize  # noqa: E402
from numeroloji.kapsam import SINIFLAR, kapsam_hesapla  # noqa: E402
from numeroloji.planlar import denge_hesapla, planlar_hesapla  # noqa: E402
from numeroloji.sentez import sentez_uret, tekrar_denetle  # noqa: E402
from numeroloji.veri import yukle  # noqa: E402


class TestHarf(unittest.TestCase):
    def test_turkce_katlama(self):
        self.assertEqual(normalize("Ayşe"), "AYSE")
        self.assertEqual(normalize("İbrahim"), "IBRAHIM")
        self.assertEqual(normalize("Çetin Öztürk"), "CETINOZTURK")
        self.assertEqual(normalize("Karahasanoğlu"), "KARAHASANOGLU")

    def test_i_ve_noktali_i_ayni_sayiya_gider(self):
        hm = HarfHaritasi.varsayilan()
        self.assertEqual(normalize("İIıi", hm), "IIII")
        self.assertEqual(set(harf_sayilari("İIıi", hm)), {9})

    def test_asci_ve_unicode_yazim_ayni_tabloyu_verir(self):
        """Nufus kayitlarinda harf cevrimi tutarsizdir; katlama bunu esitler."""
        self.assertEqual(harf_sayilari("Ayşe Gülşen"), harf_sayilari("Ayse Gulsen"))

    def test_noktalama_ve_rakam_atilir(self):
        self.assertEqual(normalize("Al-i O'sman 3."), "ALIOSMAN")

    def test_bilesik_diakritik_ayrilir(self):
        # A + birlesen aksan (NFD) -> A
        self.assertEqual(normalize("Âli"), "ALI")

    def test_indirgeme_usta_sayilari_korur(self):
        self.assertEqual(indirge([9, 9, 2]), 2)      # 20 -> 2
        self.assertEqual(indirge([5, 6]), 11)        # usta sayi korunur
        self.assertEqual(indirge([5, 6], usta_koru=False), 2)
        self.assertEqual(indirge([4, 4, 3]), 11)

    def test_harita_tam(self):
        hm = HarfHaritasi.varsayilan()
        self.assertEqual(len(hm.harita), 26)
        self.assertEqual(set(hm.harita.values()), set(range(1, 10)))


class TestCekirdek(unittest.TestCase):
    def test_yasam_yolu(self):
        c = cekirdek_hesapla(Kisi("Ali Kaya", "1985-08-08"))
        self.assertEqual(c.yasam_yolu, indirge([1, 9, 8, 5, 0, 8, 0, 8]))

    def test_usta_sayi_indirgenerek_telafi_eder(self):
        """inclusion.md 1.0'da 2|0 satirinda kazara belirmis kural:
        '11'in varligi bu eksikligi telafi edecek'. Artik sistematik."""
        c = cekirdek_hesapla(Kisi("Ayşe Nur Karahasanoğlu", "1990-03-17"))
        self.assertEqual(c.ruh_arzusu, 22)
        self.assertTrue(c.telafi_eder_mi(4))          # 22 -> 4
        self.assertIn("usta sayı 22", " ".join(c.telafi_kaynaklari(4)))

    def test_dogum_ayi_telafi_kumesinde(self):
        """1.0'da 1|0 satirindaki 'Ocak ya da Ekim' kurali genellestirildi."""
        c = cekirdek_hesapla(Kisi("Mehmet Öztürk", "1977-01-03"))
        self.assertEqual(c.dogum_ayi, 1)
        self.assertTrue(c.telafi_eder_mi(1))


class TestKapsam(unittest.TestCase):
    def test_frekans_toplami_harf_sayisina_esit(self):
        t = kapsam_hesapla(Kisi("Ayşe Nur Karahasanoğlu", "1990-03-17"))
        self.assertEqual(sum(t.frekanslar.values()), t.harf_sayisi)

    def test_tum_siniflar_gecerli(self):
        t = kapsam_hesapla(Kisi("Ayşe Nur Karahasanoğlu", "1990-03-17"))
        for o in t.okumalar.values():
            self.assertIn(o.sinif, SINIFLAR)

    def test_normalizasyon_ad_uzunluguna_duyarli(self):
        """Ayni ham frekans, kisa ve uzun adda ayni sinifa dusmemeli."""
        kisa = kapsam_hesapla(Kisi("Ali Kaya", "1990-01-01"))
        uzun = kapsam_hesapla(Kisi("Ayşe Nur Karahasanoğlu", "1990-01-01"))
        self.assertEqual(kisa.frekanslar[1], 3)
        self.assertEqual(kisa.okumalar[1].sinif, "normalin_ustu")
        # Uzun adda 3 adet 1 beklentinin altinda kalirdi:
        self.assertLess(uzun.okumalar[1].beklenen, uzun.frekanslar[1])
        self.assertGreater(uzun.okumalar[1].beklenen, kisa.okumalar[1].beklenen)

    def test_telafi_edilen_sifir_karmik_ders_degil(self):
        t = kapsam_hesapla(Kisi("Mehmet Öztürk", "1977-01-03"))
        o = t.okumalar[1]
        self.assertEqual(o.frekans, 0)
        self.assertEqual(o.sinif, "eksik")
        self.assertTrue(o.telafi_edildi)
        self.assertFalse(o.karmik_ders_mi)
        self.assertEqual(o.metin_varyanti, "telafili")
        self.assertNotIn(1, t.karmik_dersler)

    def test_yuksek_taban_oranli_eksiklik_kolektif_okunur(self):
        t = kapsam_hesapla(Kisi("Mehmet Öztürk", "1977-01-03"))
        o = t.okumalar[7]
        self.assertTrue(o.karmik_ders_mi)
        self.assertEqual(o.siddet, "kolektif")
        self.assertEqual(o.metin_varyanti, "kolektif")

    def test_gizli_tutku_en_yuksek_frekans(self):
        t = kapsam_hesapla(Kisi("Ayşe Nur Karahasanoğlu", "1990-03-17"))
        self.assertEqual(t.frekanslar[t.gizli_tutku], max(t.frekanslar.values()))
        self.assertIn(t.gizli_tutku_karakteri, ("belirgin", "duz", "paylasimli"))

    def test_bos_ad_hata_verir(self):
        with self.assertRaises(ValueError):
            kapsam_hesapla(Kisi("123 -.-", "1990-01-01"))


class TestDenge(unittest.TestCase):
    def test_tek_cift_beklentiye_gore_normalize(self):
        """Turkce adlarda tek sayilar dogal olarak baskin (~%78). Tipik bir ad
        bu yuzden otomatik 'tek agir' sayilmamali."""
        d = denge_hesapla(kapsam_hesapla(Kisi("Ali Kaya", "1990-01-01")))
        self.assertGreater(d.tek_toplam, d.cift_toplam)   # ham oran tek agir
        self.assertEqual(d.tek_cift_sinif, "dengeli")     # normalize sonra dengeli

    def test_uc_eksen_ve_toplam_tutarli(self):
        t = kapsam_hesapla(Kisi("Ayşe Nur Karahasanoğlu", "1990-03-17"))
        d = denge_hesapla(t)
        self.assertEqual(len(d.eksenler), 3)
        self.assertEqual(sum(e.toplam for e in d.eksenler), t.harf_sayisi)

    def test_ifade_planlari_dogrulanmadan_kapali(self):
        veri = yukle("ifade-planlari")
        self.assertFalse(veri["etkin"])
        self.assertEqual(veri["kaynak_dogrulamasi"], "ONAYLANMADI")
        self.assertEqual(planlar_hesapla(
            kapsam_hesapla(Kisi("Ali Kaya", "1990-01-01"))), ())


class TestSentez(unittest.TestCase):
    def test_celiski_iki_fazlalik_gerektirir(self):
        t = kapsam_hesapla(Kisi("Ayşe Nur Karahasanoğlu", "1990-03-17"))
        fazla = {n for n, o in t.okumalar.items()
                 if o.sinif in ("normalin_ustu", "asiri")}
        for n in sentez_uret(t):
            if n.tur == "celiski":
                self.assertTrue(set(n.sayilar) <= fazla)

    def test_pekisme_ders_ve_fazlalik_gerektirir(self):
        t = kapsam_hesapla(Kisi("Mehmet Öztürk", "1977-01-03"))
        for n in sentez_uret(t):
            if n.tur == "pekisme":
                ders, fazla = n.sayilar
                self.assertIn(ders, t.karmik_dersler)
                self.assertIn(t.okumalar[fazla].sinif, ("normalin_ustu", "asiri"))


class TestRapor(unittest.TestCase):
    ORNEKLER = [
        ("Ayşe Nur Karahasanoğlu", "1990-03-17"),
        ("Mehmet Öztürk", "1977-01-03"),
        ("Ali Kaya", "1985-08-08"),
        ("Zeynep Çelik", "2001-11-29"),
        ("İbrahim Şahin", "1963-02-04"),
    ]

    def test_dokuz_sayinin_hepsi_basiliyor(self):
        """Bolum bir giris paragrafi + dokuz sayi paragrafi icerir; her sayi
        kendi basligiyla ve bir yogunluk ya da ders notuyla gecmeli."""
        for ad, dt in self.ORNEKLER:
            r = rapor_uret(Kisi(ad, dt))
            hucre = next(b for b in r.bolumler if b.anahtar == "hucreler")
            self.assertEqual(len(hucre.paragraflar), 10, ad)
            self.assertIn("iki katmanda okunur", hucre.paragraflar[0])
            for n, par in zip(range(1, 10), hucre.paragraflar[1:]):
                self.assertIn(f"**{n} — frekans", par, f"{ad} / sayi {n}")
                self.assertTrue(
                    "_Yoğunluk:_" in par or "Karmik Ders" in par
                    or "Telafi edilmiş ders" in par, f"{ad} / sayi {n}")
            self.assertEqual(set(hucre.veri["sayilar"]),
                             {str(n) for n in range(1, 10)}, ad)

    def test_tekrar_denetimi_gecer(self):
        for ad, dt in self.ORNEKLER:
            r = rapor_uret(Kisi(ad, dt))          # denetim acik; gecmezse atar
            self.assertEqual(tekrar_denetle(r.duz_metin()), [], ad)

    def test_tekrar_denetimi_gercekten_yakalar(self):
        """Denetim canli olmali: uydurma bir metin esigi asmali."""
        self.assertTrue(tekrar_denetle("kendinizi ifade edersiniz " * 5))

    def test_eksik_hucre_rapor_kirmiyor(self):
        """7|8, 7|9 ve 8|9 hucreleri yok (o frekanslara pratikte ulasilamaz).
        Motor bunu zarif karsilamali."""
        hucreler = yukle("kapsam-hucreleri")["hucreler"]
        for eksik in ("7|8", "7|9", "8|9"):
            self.assertNotIn(eksik, hucreler)
        r = rapor_uret(Kisi("Ali Kaya", "1990-01-01"))
        self.assertTrue(r.duz_metin())

    def test_sozluk_serilestirilebilir(self):
        r = rapor_uret(Kisi("Ali Kaya", "1985-08-08"))
        json.dumps(r.sozluk(), ensure_ascii=False)   # atmamali


class TestIcerikRegresyonu(unittest.TestCase):
    """1.0 surumunden kaldirilan ifadeler geri gelmemeli."""

    #: Kullaniciya BASILAN alanlar. Bakim notlari (revizyon_notu, cerceve_notu,
    #: aciklama) taranmaz: onlar kaldirilan ifadeyi adiyla anmak zorundadir.
    @staticmethod
    def kullanici_metinleri() -> list[str]:
        cikti: list[str] = []
        for d in yukle("karmik-dersler")["dersler"].values():
            cikti += [d[a] for a in ("tema", "kisisel", "kolektif", "telafili",
                                     "yasam_zorlamasi", "calisma_onerisi",
                                     "cocukluk_notu")]
        cikti += [h["metin"] for h in yukle("kapsam-hucreleri")["hucreler"].values()]
        for v in yukle("yogunluk")["metinler"].values():
            cikti += list(v.values())
        cikti += list(yukle("gizli-tutku")["metinler"].values())
        denge = yukle("denge")
        cikti += list(denge["tek_cift"]["metinler"].values())
        for e in denge["ucul_eksenler"]["eksenler"].values():
            cikti += [e["ad"], e["aciklama"], e["zayif"], e["dengeli"], e["baskin"]]
        sentez = yukle("sentez")
        cikti += [c["ad"] for c in sentez["celiskiler"]]
        cikti += [c["metin"] for c in sentez["celiskiler"]]
        cikti += [x["metin"] for x in sentez["pekismeler"]]
        return cikti

    @classmethod
    def setUpClass(cls):
        cls.metinler = cls.kullanici_metinleri()
        cls.korpus = "\n".join(cls.metinler).lower()

    def test_kaderci_ve_zararli_ifadeler_yok(self):
        yasakli = [
            "kleptoman",            # klinik iddia
            "boşanma",              # evlilik ongorusu
            "yuvarlak omuz",        # beden yorumu
            "psikolojik bir çöküntü",
            "muhakemen zayıf",
            "kendini mahvet",
            "fakirlik",
            "ızdırap",
            "şanssızlık",
            "evlat edin",
        ]
        for y in yasakli:
            self.assertNotIn(y, self.korpus, f"kaldirilan ifade geri gelmis: {y!r}")

    def test_cevrilmemis_kelimeler_yok(self):
        for y in ["brutal", "rigor", "doğal rezerv", "büyük bey",
                  "cesaret edersiniz", "bölgenizi kontrol",
                  "estetizm", "naziklik", "spontanl", "altruizm",
                  "harmonik", "durugörü", "aktivitelerde", "sektörler",
                  "stabil", "manuel yetenek", "insan merkezci"]:
            self.assertNotIn(y, self.korpus, f"ceviri hatasi geri gelmis: {y!r}")

    def test_birinci_cogul_cekim_hatasi_yok(self):
        """Fransizca 'on aime' kalibinin 'severiz' cevirisi."""
        for y in ["severiz", "sever,"]:
            self.assertNotIn(y, self.korpus, f"cekim hatasi geri gelmis: {y!r}")

    def test_yazim_hatasi_yok(self):
        self.assertNotIn("yardımserver", self.korpus)

    def test_kahin_sesi_yok(self):
        """1.0'da Karmik Ders metinleri 1. tekil 'goruyorum' sesi tasiyordu."""
        dersler = yukle("karmik-dersler")["dersler"]
        for n, d in dersler.items():
            for alan in ("kisisel", "kolektif", "telafili"):
                self.assertNotIn("görüyorum", d[alan], f"{n}|{alan}")
                self.assertNotIn("zorundasın", d[alan], f"{n}|{alan}")

    #: 1.0'da frekans=0 satirlarinda gecen gercek 2. tekil fiil bicimleri.
    #: scripts ile inclusion.md'den cikarildi; iyelik ekleri (hayatin, kendin,
    #: zarafetin gibi) elle ayiklandi.
    IKINCI_TEKIL = (
        "alınmamalısın", "bağdaştırıyorsun", "başladın", "başlayacaksın",
        "bitiremedin", "bulacaksın", "düşünüyorsun", "gerçekleştirdin",
        "geçireceksin", "göreceksin", "hissediyorsun", "hissetmiyorsun",
        "kalacaksın", "karşılaşacaksın", "karşılaştın", "kaçınıyorsun",
        "keşfedeceksin", "takınacaksın", "taşıyorsun", "vermelisin",
        "vurguluyorsun", "zorlanacaksın", "zorlanıyorsun", "zorundasın",
        "öğreneceksin", "üstlendin", "üstleneceksin",
    )

    def test_ikinci_tekil_ses_kalmadi(self):
        """1.0'da frekans=0 satirlari 2. tekil, digerleri 2. coguldu; rapor iki
        farkli kisi tarafindan konusuyor gibi okunuyordu. Ses birlestirildi.

        Kelime sinirina demirlenmis arama sart: 2. cogul bicimler 2. tekil
        bicimlerin ustkumesidir ('tasiyorsun' <- 'tasiyorsunuz'), duz substring
        aramasi dogru metni hatali bulur.
        """
        for bicim in self.IKINCI_TEKIL:
            bulunan = re.search(rf"\b{re.escape(bicim)}\b", self.korpus)
            self.assertIsNone(
                bulunan, f"2. tekil bicim geri gelmis: {bicim!r}")

    def test_ikinci_tekil_listesi_kaynakta_gercekten_vardi(self):
        """Testin kendisi curumesin: bu bicimler 1.0 kaynaginda bulunmali."""
        ham = (KOK / "inclusion.md").read_text(encoding="utf-8").lower()
        for bicim in self.IKINCI_TEKIL:
            self.assertRegex(ham, rf"\b{re.escape(bicim)}\b",
                             f"{bicim!r} 1.0 kaynaginda yok")

    def test_tum_metinler_turkce_imlali(self):
        """Diakritiksiz metin Turkce bir urunde kabul edilemez."""
        tr = set("çğıöşüÇĞİÖŞÜ")
        dersler = yukle("karmik-dersler")["dersler"]
        for n, d in dersler.items():
            for alan in ("kisisel", "kolektif", "telafili"):
                self.assertTrue(tr & set(d[alan]), f"{n}|{alan} diakritiksiz")
        for k, h in yukle("kapsam-hucreleri")["hucreler"].items():
            self.assertTrue(tr & set(h["metin"]), f"hucre {k} diakritiksiz")


class TestKorpusButunlugu(unittest.TestCase):
    def test_hucre_kapsami(self):
        h = yukle("kapsam-hucreleri")["hucreler"]
        self.assertEqual(len(h), 78)
        for sayi in range(1, 10):
            ust = {7: 7, 8: 8}.get(sayi, 9)
            for f in range(1, ust + 1):
                self.assertIn(f"{sayi}|{f}", h)

    def test_her_hucrede_metadata(self):
        for k, h in yukle("kapsam-hucreleri")["hucreler"].items():
            self.assertTrue(h["temalar"], k)
            self.assertIn("güç", h["kutup"], k)

    def test_yogunluk_tam(self):
        y = yukle("yogunluk")["metinler"]
        self.assertEqual(len(y), 9)
        for n, v in y.items():
            self.assertEqual(set(v), {"normalin_alti", "dengeli",
                                      "normalin_ustu", "asiri"}, n)

    def test_karmik_dersler_tam(self):
        d = yukle("karmik-dersler")["dersler"]
        self.assertEqual(len(d), 9)
        for n, v in d.items():
            for alan in ("kisisel", "kolektif", "telafili", "yasam_zorlamasi",
                         "calisma_onerisi", "cocukluk_notu", "tema"):
                self.assertIn(alan, v, f"{n} -> {alan}")

    def test_taban_oranlari_tutarli(self):
        t = yukle("taban-oranlar")
        self.assertAlmostEqual(sum(t["harf_olasiligi"].values()), 1.0, places=3)
        for n in map(str, range(1, 10)):
            self.assertIn(t["siddet_sinifi"][n], ("kisisel", "yaygin", "kolektif"))

    def test_gizli_tutku_metinleri_tam(self):
        self.assertEqual(len(yukle("gizli-tutku")["metinler"]), 9)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestUyumlulukVektorleri(unittest.TestCase):
    """Port dogrulama vektorleri motorla uyumlu kalmali.

    Bu testin isi iki yonlu: hem vektorlerin cürümesini engeller, hem de
    hesaplamayi degistiren bir PR'in sessizce gecmesini imkansiz kilar.
    Davranis bilincli degistiyse vektorler yeniden uretilir:
        python3 scripts/vektor_uret.py
    """

    @classmethod
    def setUpClass(cls):
        yol = KOK / "tests" / "uyumluluk-vektorleri.json"
        cls.veri = json.loads(yol.read_text(encoding="utf-8"))

    def test_vektor_kapsami(self):
        self.assertGreaterEqual(len(self.veri["vektorler"]), 20)
        for v in self.veri["vektorler"]:
            self.assertTrue(v["sinar"], v["ad"])       # her vektor ne sinadigini yazar

    def test_motor_vektorlerle_uyumlu(self):
        sys.path.insert(0, str(KOK / "scripts"))
        from vektor_uret import vektor  # noqa: E402

        for v in self.veri["vektorler"]:
            uretilen = vektor(v["ad"], v["dogum_tarihi"], v["sinar"])
            self.assertEqual(uretilen["beklenen"], v["beklenen"],
                             f"{v['ad']} vektoru sapti ({v['sinar']})")

    def test_sinir_durumlari_gercekten_kapsaniyor(self):
        """Vektor kumesi, kilavuzun sozunu verdigi tuzaklari icermeli."""
        b = {v["ad"]: v["beklenen"] for v in self.veri["vektorler"]}
        # noktasiz i / noktali I ayrimi
        self.assertEqual(b["Ilgın Işık"]["ad_duz"], "ILGINISIK")
        # tire ve kesme atilir, harfler birlestirilmez
        self.assertEqual(b["Al-i Osman Bey"]["ad_duz"], "ALIOSMANBEY")
        self.assertEqual(b["D'Artagnan Kaya"]["ad_duz"], "DARTAGNANKAYA")
        # usta sayi cekirdekte ve telafi kumesinde indirgenmis haliyle
        self.assertEqual(b["Ayşe Nur Karahasanoğlu"]["cekirdek"]["ruh_arzusu"], 22)
        self.assertIn(4, b["Ayşe Nur Karahasanoğlu"]["cekirdek"]["telafi_kumesi"])
        # Dogum Ayi telafisi
        self.assertEqual(b["Mehmet Öztürk"]["metin_varyantlari"]["1"], "telafili")
        # kolektif siddet varyanti
        self.assertEqual(b["Mehmet Öztürk"]["metin_varyantlari"]["7"], "kolektif")
        # en az bir vektorde celiski tetiklenmis olmali
        self.assertTrue(any(v["beklenen"]["sentez"] for v in self.veri["vektorler"]))
