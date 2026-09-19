"""Rapor kompozisyonu: sayilari metne cevirir ve bolumleri sirayla kurar.

Bolum sirasi bir okuma karari: once tablonun butunu (Gizli Tutku, denge),
sonra tek tek hucreler, en sonda sentez. 1.0 surumunde yalnizca orta bolum
vardi ve rapor dokuz bagimsiz paragraftan olusuyordu.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .cekirdek import CekirdekSayilar, Kisi, cekirdek_hesapla
from .harf import HarfHaritasi
from .kapsam import KapsamTablosu, kapsam_hesapla
from .planlar import DengeOkuma, PlanOkuma, denge_hesapla, planlar_hesapla
from .sentez import SentezNotu, sentez_uret, tekrar_denetle
from .veri import yukle


@dataclass(frozen=True)
class Bolum:
    anahtar: str
    baslik: str
    paragraflar: tuple[str, ...]
    veri: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Rapor:
    kisi_adi: str
    tablo: KapsamTablosu
    cekirdek: CekirdekSayilar
    denge: DengeOkuma
    planlar: tuple[PlanOkuma, ...]
    sentez: tuple[SentezNotu, ...]
    bolumler: tuple[Bolum, ...]

    def duz_metin(self) -> str:
        parcalar = []
        for b in self.bolumler:
            parcalar.append(f"## {b.baslik}")
            parcalar.extend(b.paragraflar)
        return "\n\n".join(parcalar)

    def sozluk(self) -> dict:
        """JSON'a serilestirilebilir hal (uygulama katmani icin)."""
        return {
            "ad": self.kisi_adi,
            "harf_sayisi": self.tablo.harf_sayisi,
            "cekirdek": asdict(self.cekirdek) | {
                "telafi_kumesi": sorted(self.cekirdek.telafi_kumesi)},
            "frekanslar": self.tablo.frekanslar,
            "gizli_tutku": self.tablo.gizli_tutku,
            "karmik_dersler": self.tablo.karmik_dersler,
            "telafi_edilmis_dersler": self.tablo.telafi_edilmis_dersler,
            "asiri_sayilar": self.tablo.asiri_sayilar,
            "bolumler": [
                {"anahtar": b.anahtar, "baslik": b.baslik,
                 "paragraflar": list(b.paragraflar), "veri": b.veri}
                for b in self.bolumler
            ],
        }


def _gizli_tutku_bolumu(tablo: KapsamTablosu) -> Bolum:
    veri = yukle("gizli-tutku")
    n = tablo.gizli_tutku
    p = [veri["metinler"][str(n)]]

    karakter = tablo.gizli_tutku_karakteri
    if karakter == "paylasimli":
        ortaklar = ", ".join(str(x) for x in tablo.gizli_tutku_ortaklari)
        p.append(
            f"Bu tutku tek bir eksende toplanmıyor: {ortaklar} sayıları aynı "
            "zirvede duruyor. İkisi arasında bir seçim yapmadığın sürece "
            "enerjinin bir kısmı geçişlerde harcanır."
        )
        for o in tablo.gizli_tutku_ortaklari[1:]:
            p.append(veri["metinler"][str(o)])
    elif karakter == "duz":
        p.append(
            "Zirve yalnızca bir frekans farkla önde: bu tutku var ama tablonu "
            "tek başına belirlemiyor. Tablon görece dengeli dağılmış, yani "
            "baskın bir eksenden çok geniş bir taban okuyoruz."
        )

    if n in tablo.asiri_sayilar:
        p.append(
            "Bu sayı aynı zamanda 'aşırı' kayıtta: yani hem yönün hem "
            "yükün. Aşağıdaki yoğunluk notu bu yüzden ayrıca önemli."
        )
    return Bolum("gizli_tutku", f"Gizli Tutku: {n}", tuple(p),
                 {"sayi": n, "karakter": karakter,
                  "ortaklar": list(tablo.gizli_tutku_ortaklari)})


def _denge_bolumu(denge: DengeOkuma) -> Bolum:
    p = [denge.tek_cift_metni]
    for e in denge.eksenler:
        p.append(f"**{e.ad}** ({'-'.join(map(str, e.sayilar))}) — {e.metin}")
    return Bolum("denge", "Tablonun Dengesi", tuple(p),
                 {"tek_cift": denge.tek_cift_sinif,
                  "eksenler": {e.anahtar: e.sinif for e in denge.eksenler}})


def _hucre_bolumu(tablo: KapsamTablosu) -> Bolum:
    hucreler = yukle("kapsam-hucreleri")["hucreler"]
    dersler = yukle("karmik-dersler")["dersler"]
    yogunluk = yukle("yogunluk")["metinler"]

    # Iki katmanli okumanin nasil okunacagi bir kez burada soylenir; yoksa
    # hucre metni ile yogunluk notu celisiyormus gibi gorunur.
    p: list[str] = [
        "Her sayı iki katmanda okunur. **Hücre metni** o sayının *niteliğini* "
        "anlatır: sayının, frekansının rengiyle nasıl çalıştığını. **Yoğunluk "
        "notu** ise *niceliği* anlatır: o frekansın, adının uzunluğuna göre "
        "beklenenin altında mı üstünde mi olduğunu. İkisi farklı şeyler söyler; "
        "çeliştiklerini düşündüğün yerde nicelik baskındır. "
        "(_Titreşim_ sözcüğü metinlerde bir sayının taşıdığı niteliğin karşılığı "
        "olarak kullanılır.)"
    ]
    ayrinti: dict[str, dict] = {}

    for n in range(1, 10):
        o = tablo.okumalar[n]
        basla = f"**{n} — frekans {o.frekans}** (beklenen {o.beklenen:.1f})"

        if o.sinif == "eksik":
            d = dersler[str(n)]
            varyant = o.metin_varyanti
            govde = [d[varyant]]
            if varyant == "telafili":
                govde.append("Telafi eden çekirdek sayılar: "
                             + ", ".join(o.telafi_kaynaklari) + ".")
            else:
                govde.append(d["yasam_zorlamasi"])
                govde.append("_Çalışma önerisi:_ " + d["calisma_onerisi"])
            etiket = ("Telafi edilmiş ders" if varyant == "telafili"
                      else f"Karmik Ders — {d['tema']}")
            p.append(f"{basla} · _{etiket}_\n\n" + "\n\n".join(govde))
            ayrinti[str(n)] = {"sinif": o.sinif, "varyant": varyant,
                               "telafi": list(o.telafi_kaynaklari)}
        else:
            h = hucreler.get(f"{n}|{o.frekans}")
            govde = []
            if h:
                govde.append(h["metin"])
            else:
                govde.append(
                    f"Bu frekans ({o.frekans}) için ayrı bir hücre metni yok; "
                    "Türkçe adlarda pratikte ulaşılamayan bir sayım. Aşağıdaki "
                    "yoğunluk okuması geçerlidir."
                )
            govde.append("_Yoğunluk:_ " + yogunluk[str(n)][o.sinif])
            p.append(f"{basla} · _{o.etiket}_\n\n" + "\n\n".join(govde))
            ayrinti[str(n)] = {"sinif": o.sinif, "varyant": "hucre",
                               "hucre_var": bool(h)}

    return Bolum("hucreler", "Sayı Sayı Okuma", tuple(p), {"sayilar": ayrinti})


def _sentez_bolumu(notlar: tuple[SentezNotu, ...]) -> Bolum | None:
    if not notlar:
        return None
    p = [f"**{n.ad}** — {n.metin}" for n in notlar]
    return Bolum("sentez", "Gerilimler ve Pekişmeler", tuple(p),
                 {"notlar": [{"tur": n.tur, "sayilar": list(n.sayilar)} for n in notlar]})


def _planlar_bolumu(planlar: tuple[PlanOkuma, ...]) -> Bolum | None:
    if not planlar:
        return None
    return Bolum("planlar", "İfade Planları",
                 tuple(f"**{pl.ad}** — {pl.metin}" for pl in planlar),
                 {"planlar": {pl.anahtar: pl.sinif for pl in planlar}})


def rapor_uret(
    kisi: Kisi,
    hm: HarfHaritasi | None = None,
    tekrar_denetimi: bool = True,
) -> Rapor:
    """Kisi icin tam kapsam tablosu raporu.

    tekrar_denetimi=True ise, uretilen metinde esigi asan kaliplasmis ifade
    bulunursa AssertionError atilir. Uretimde bu bir icerik bakim uyarisidir;
    istemci kapatabilir.
    """
    hm = hm or HarfHaritasi.varsayilan()
    cekirdek = cekirdek_hesapla(kisi, hm)
    tablo = kapsam_hesapla(kisi, hm, cekirdek)
    denge = denge_hesapla(tablo)
    planlar = planlar_hesapla(tablo)
    notlar = sentez_uret(tablo)

    bolumler = [
        _gizli_tutku_bolumu(tablo),
        _denge_bolumu(denge),
        _hucre_bolumu(tablo),
    ]
    for b in (_planlar_bolumu(planlar), _sentez_bolumu(notlar)):
        if b:
            bolumler.append(b)

    rapor = Rapor(
        kisi_adi=kisi.dogum_adi, tablo=tablo, cekirdek=cekirdek, denge=denge,
        planlar=planlar, sentez=notlar, bolumler=tuple(bolumler),
    )

    if tekrar_denetimi:
        asanlar = tekrar_denetle(rapor.duz_metin())
        if asanlar:
            ayrinti = "; ".join(
                f"{a['kalip']!r} {a['sayim']} kez (eşik {a['esik']})" for a in asanlar)
            raise AssertionError(f"Rapor tekrar denetiminden geçemedi: {ayrinti}")

    return rapor
