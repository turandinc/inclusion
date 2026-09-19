'use strict';
/**
 * Kapsam tablosu motoru — JavaScript (Node, CommonJS) portu.
 *
 * Sözleşme: docs/PORT-KILAVUZU.md + tests/uyumluluk-vektorleri.json.
 * Bu modül yalnızca SAYILARI ve METİN ANAHTARLARINI üretir; metinler
 * data/*.json içinden olduğu gibi okunur (bkz. metinleriSec).
 *
 * Bağımlılık yok. Veri dizini varsayılan olarak repo kökündeki data/;
 * uygulamaya gömülürken kapsamHesapla(..., { veriDizini }) ile değiştirilebilir.
 */

const fs = require('fs');
const path = require('path');

const VARSAYILAN_VERI_DIZINI = path.resolve(__dirname, '..', '..', 'data');
const USTA_SAYILAR = new Set([11, 22, 33]);
const TEK = [1, 3, 5, 7, 9];
const CIFT = [2, 4, 6, 8];
const FAZLA_SINIFLAR = new Set(['normalin_ustu', 'asiri']);

// ---------------------------------------------------------------------------
// Veri
// ---------------------------------------------------------------------------
const _onbellek = new Map();
function yukle(ad, veriDizini = VARSAYILAN_VERI_DIZINI) {
  const anahtar = `${veriDizini}::${ad}`;
  if (!_onbellek.has(anahtar)) {
    const yol = path.join(veriDizini, `${ad}.json`);
    _onbellek.set(anahtar, JSON.parse(fs.readFileSync(yol, 'utf8')));
  }
  return _onbellek.get(anahtar);
}

function harfHaritasi(veriDizini) {
  const veri = yukle('harf-haritasi', veriDizini);
  const sema = veri.semalar[veri.etkin_sema];
  // Katlama sonrası sesli kümesi (İ→I, Ö→O, Ü→U): kılavuz §1.
  const sesliler = new Set(
    veri.sesli_harfler.sesliler.map((s) => {
      const k = sema.katlama[s] ?? s;
      return k in sema.harita ? k : s;
    }),
  );
  return { harita: sema.harita, katlama: sema.katlama, sesliler, semaAdi: veri.etkin_sema };
}

// ---------------------------------------------------------------------------
// §1 Normalizasyon
// ---------------------------------------------------------------------------
function buyut(metin) {
  // Tuzak 1: genel büyütmeden ÖNCE i→İ, ı→I.
  return String(metin).replace(/i/g, 'İ').replace(/ı/g, 'I').toUpperCase();
}

function normalize(ad, hm) {
  let cikti = '';
  for (const ch of buyut(ad)) {
    if (ch in hm.katlama) { cikti += hm.katlama[ch]; continue; }
    if (ch in hm.harita) { cikti += ch; continue; }
    const taban = ch.normalize('NFD').replace(/\p{M}/gu, '');
    if (taban in hm.katlama) cikti += hm.katlama[taban];
    else if (taban in hm.harita) cikti += taban;
    // Geri kalan her şey sessizce atılır.
  }
  return cikti;
}

// ---------------------------------------------------------------------------
// §2 İndirgeme
// ---------------------------------------------------------------------------
function rakamToplami(n) {
  let t = 0;
  for (const c of String(n)) t += Number(c);
  return t;
}

function indirge(sayilar, ustaKoru = true) {
  let toplam = sayilar.reduce((a, b) => a + b, 0);
  while (toplam > 9) {
    if (ustaKoru && USTA_SAYILAR.has(toplam)) return toplam; // Tuzak 2
    toplam = rakamToplami(toplam);
  }
  return toplam;
}

// ---------------------------------------------------------------------------
// §3 Çekirdek sayılar
// ---------------------------------------------------------------------------
const CEKIRDEK_ETIKETLERI = {
  yasam_yolu: 'Yaşam Yolu',
  ifade: 'İfade (Kader)',
  ruh_arzusu: 'Ruh Arzusu',
  kisilik: 'Kişilik',
  dogum_gunu: 'Doğum Günü',
  dogum_ayi: 'Doğum Ayı',
  olgunluk: 'Olgunluk',
};

function tarihCoz(dogumTarihi) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(dogumTarihi).trim());
  if (!m) throw new Error(`Geçersiz tarih (YYYY-MM-DD bekleniyor): ${dogumTarihi}`);
  return { yil: m[1], ay: m[2], gun: m[3] };
}

function cekirdekHesapla(ad, dogumTarihi, hm) {
  const t = tarihCoz(dogumTarihi);
  const duz = normalize(ad, hm);
  const deger = (h) => hm.harita[h];

  const yasam_yolu = indirge([...`${t.yil}${t.ay}${t.gun}`].map(Number));
  const ifade = indirge([...duz].map(deger));
  const ruh_arzusu = indirge([...duz].filter((h) => hm.sesliler.has(h)).map(deger));
  const kisilik = indirge([...duz].filter((h) => !hm.sesliler.has(h)).map(deger));
  const dogum_gunu = indirge([...String(Number(t.gun))].map(Number));
  const dogum_ayi = indirge([...String(Number(t.ay))].map(Number));
  const olgunluk = indirge([yasam_yolu, ifade]);

  const c = { yasam_yolu, ifade, ruh_arzusu, kisilik, dogum_gunu, dogum_ayi, olgunluk };

  const kume = new Set();
  for (const d of Object.values(c)) {
    kume.add(d);
    if (USTA_SAYILAR.has(d)) kume.add(indirge([d], false));
  }
  c.telafi_kumesi = [...kume].sort((a, b) => a - b);
  return c;
}

function telafiKaynaklari(cekirdek, sayi) {
  const bulunan = [];
  for (const [alan, etiket] of Object.entries(CEKIRDEK_ETIKETLERI)) {
    const d = cekirdek[alan];
    const usta = USTA_SAYILAR.has(d);
    if (d === sayi || (usta && indirge([d], false) === sayi)) {
      bulunan.push(usta ? `${etiket} (usta sayı ${d})` : etiket);
    }
  }
  return bulunan;
}

// ---------------------------------------------------------------------------
// §4 Frekanslar ve sınıf
// ---------------------------------------------------------------------------
function yuvarla2(x) {
  // Vektörlerde sınır değer yok (kılavuz §4); olağan yuvarlama yeterli.
  return Math.round((x + Number.EPSILON) * 100) / 100 || 0;
}

function zSkoru(gozlenen, L, p) {
  if (L === 0 || p <= 0 || p >= 1) return 0;
  return (gozlenen - L * p) / (Math.sqrt(L * p * (1 - p)) || 1e-9);
}

function sinifBelirle(frekans, z, esikler) {
  if (frekans === 0) return 'eksik'; // Tuzak 3: z'den önce
  if (z < esikler.normalin_alti) return 'normalin_alti';
  if (z <= esikler.dengeli_ust) return 'dengeli';
  if (z <= esikler.normalin_ustu_ust) return 'normalin_ustu';
  return 'asiri';
}

// §5
function metinVaryanti(sinif, telafiEdildi, siddet) {
  if (sinif !== 'eksik') return 'hucre';
  if (telafiEdildi) return 'telafili';
  return siddet === 'kolektif' || siddet === 'yaygin' ? 'kolektif' : 'kisisel';
}

// ---------------------------------------------------------------------------
// Ana hesaplama
// ---------------------------------------------------------------------------
/**
 * @param {string} ad            Doğum adı (tüm ön adlar + doğum soyadı)
 * @param {string} dogumTarihi   YYYY-MM-DD
 * @param {{veriDizini?: string}} [secenekler]
 */
function kapsamHesapla(ad, dogumTarihi, secenekler = {}) {
  const veriDizini = secenekler.veriDizini || VARSAYILAN_VERI_DIZINI;
  const hm = harfHaritasi(veriDizini);
  const taban = yukle('taban-oranlar', veriDizini);
  const p = taban.harf_olasiligi;

  const ad_duz = normalize(ad, hm);
  if (!ad_duz) throw new Error('Ad, harf haritasında karşılığı olan hiç harf içermiyor.');

  const cekirdek = cekirdekHesapla(ad, dogumTarihi, hm);
  const telafiKumesi = new Set(cekirdek.telafi_kumesi);

  const f = {};
  for (let n = 1; n <= 9; n++) f[n] = 0;
  for (const h of ad_duz) f[hm.harita[h]] += 1;
  const L = ad_duz.length;

  const okumalar = {};
  for (let n = 1; n <= 9; n++) {
    const pn = p[n];
    const beklenen = L * pn;
    const sapma = Math.sqrt(L * pn * (1 - pn)) || 1e-9;
    const z = (f[n] - beklenen) / sapma;
    const sinif = sinifBelirle(f[n], z, taban.esikler);
    const o = { sayi: n, frekans: f[n], beklenen: yuvarla2(beklenen), z: yuvarla2(z), sinif };
    if (sinif === 'eksik') {
      o.taban_orani = taban.sifir_orani[n];
      o.siddet = taban.siddet_sinifi[n];
      o.telafi_edildi = telafiKumesi.has(n);
      o.telafi_kaynaklari = telafiKaynaklari(cekirdek, n);
    } else {
      o.telafi_edildi = false;
    }
    o.karmik_ders = sinif === 'eksik' && !o.telafi_edildi;
    o.metin_varyanti = metinVaryanti(sinif, o.telafi_edildi, o.siddet);
    okumalar[n] = o;
  }

  const sayilar = [1, 2, 3, 4, 5, 6, 7, 8, 9];
  const karmik_dersler = sayilar.filter((n) => okumalar[n].karmik_ders);
  const telafi_edilmis_dersler = sayilar.filter((n) => okumalar[n].sinif === 'eksik' && okumalar[n].telafi_edildi);
  const asiri_sayilar = sayilar.filter((n) => okumalar[n].sinif === 'asiri');

  // §6 Gizli Tutku — Python'la aynı: yalnızca harfte geçen sayılar sayılır.
  const gorulen = sayilar.filter((n) => f[n] > 0);
  const enYuksek = Math.max(...gorulen.map((n) => f[n]));
  const zirve = gorulen.filter((n) => f[n] === enYuksek); // artan sıra — Tuzak 5
  const azalan = gorulen.map((n) => f[n]).sort((a, b) => b - a);
  const fark = enYuksek - (azalan.length > 1 ? azalan[1] : 0);
  const gizli_tutku_karakteri = zirve.length > 1 ? 'paylasimli' : fark >= 2 ? 'belirgin' : 'duz';

  // §7 Denge
  const denge = dengeHesapla(f, L, p, veriDizini);

  // §8 Sentez
  const sentez = sentezUret(okumalar, karmik_dersler, veriDizini);

  return {
    ad,
    dogum_tarihi: dogumTarihi,
    sema: hm.semaAdi,
    ad_duz,
    harf_sayisi: L,
    cekirdek,
    frekanslar: f,
    okumalar,
    karmik_dersler,
    telafi_edilmis_dersler,
    asiri_sayilar,
    gizli_tutku: zirve[0],
    gizli_tutku_ortaklari: zirve,
    gizli_tutku_karakteri,
    denge,
    sentez,
    // §9: ifade-planlari.json "etkin": false iken hesaplanmaz.
    ifade_planlari: yukle('ifade-planlari', veriDizini).etkin ? null : [],
  };
}

function dengeHesapla(f, L, p, veriDizini) {
  const veri = yukle('denge', veriDizini);
  const tek_toplam = TEK.reduce((a, n) => a + f[n], 0);
  const cift_toplam = CIFT.reduce((a, n) => a + f[n], 0);
  const pTek = TEK.reduce((a, n) => a + p[n], 0);
  const tekZ = zSkoru(tek_toplam, L, pTek); // Tuzak 6: ham oran değil
  const tek_cift_sinif = tekZ > 0.75 ? 'tek_agir' : tekZ < -0.75 ? 'cift_agir' : 'dengeli';

  const eksenler = {};
  for (const [anahtar, e] of Object.entries(veri.ucul_eksenler.eksenler)) {
    const toplam = e.sayilar.reduce((a, n) => a + f[n], 0);
    const pE = e.sayilar.reduce((a, n) => a + p[n], 0);
    const z = zSkoru(toplam, L, pE);
    const sinif = z < -0.75 ? 'zayif' : z <= 0.75 ? 'dengeli' : 'baskin';
    eksenler[anahtar] = { ad: e.ad, sayilar: e.sayilar, toplam, beklenen: yuvarla2(L * pE), z: yuvarla2(z), sinif };
  }

  return { tek_toplam, cift_toplam, tek_z: yuvarla2(tekZ), tek_cift_sinif, eksenler };
}

function sentezUret(okumalar, karmikDersler, veriDizini) {
  const veri = yukle('sentez', veriDizini);
  const fazla = new Set(Object.values(okumalar).filter((o) => FAZLA_SINIFLAR.has(o.sinif)).map((o) => o.sayi));
  const dersler = new Set(karmikDersler);
  const notlar = [];
  for (const c of veri.celiskiler) {
    const [a, b] = c.cift;
    if (fazla.has(a) && fazla.has(b)) notlar.push({ tur: 'celiski', ad: c.ad, sayilar: [a, b] });
  }
  for (const k of veri.pekismeler) {
    if (dersler.has(k.ders) && fazla.has(k.fazla)) {
      notlar.push({ tur: 'pekisme', ad: `Karmik Ders ${k.ders} ile ${k.fazla} fazlalığı`, sayilar: [k.ders, k.fazla] });
    }
  }
  return notlar;
}

// ---------------------------------------------------------------------------
// Metin seçimi (§5–§8) — anahtarlardan metinleri toplar
// ---------------------------------------------------------------------------
function metinleriSec(sonuc, secenekler = {}) {
  const veriDizini = secenekler.veriDizini || VARSAYILAN_VERI_DIZINI;
  const hucreler = yukle('kapsam-hucreleri', veriDizini).hucreler;
  const yogunluk = yukle('yogunluk', veriDizini).metinler;
  const karmik = yukle('karmik-dersler', veriDizini).dersler;
  const gizli = yukle('gizli-tutku', veriDizini);
  const denge = yukle('denge', veriDizini);
  const sentez = yukle('sentez', veriDizini);

  const sayilar = Object.values(sonuc.okumalar).map((o) => {
    if (o.metin_varyanti === 'hucre') {
      const h = hucreler[`${o.sayi}|${o.frekans}`];
      return {
        sayi: o.sayi, frekans: o.frekans, sinif: o.sinif, varyant: 'hucre',
        metin: h ? h.metin : null, // 7|8, 7|9, 8|9 bilerek yok (kılavuz §5)
        yogunluk: yogunluk[o.sayi]?.[o.sinif] ?? null,
      };
    }
    const d = karmik[o.sayi];
    return {
      sayi: o.sayi, frekans: 0, sinif: 'eksik', varyant: o.metin_varyanti,
      metin: d[o.metin_varyanti],
      telafi_kaynaklari: o.telafi_kaynaklari,
      yasam_zorlamasi: o.metin_varyanti === 'telafili' ? null : d.yasam_zorlamasi ?? null,
      calisma_onerisi: o.metin_varyanti === 'telafili' ? null : d.calisma_onerisi ?? null,
    };
  });

  return {
    gizli_tutku: {
      sayi: sonuc.gizli_tutku,
      karakter: sonuc.gizli_tutku_karakteri,
      metin: gizli.metinler[sonuc.gizli_tutku],
      karakter_notu: gizli.karakter_notu[sonuc.gizli_tutku_karakteri],
    },
    tek_cift: denge.tek_cift.metinler[sonuc.denge.tek_cift_sinif],
    eksenler: Object.entries(sonuc.denge.eksenler).map(([k, e]) => ({
      anahtar: k, ad: e.ad, sinif: e.sinif, metin: denge.ucul_eksenler.eksenler[k][e.sinif],
    })),
    sayilar,
    sentez: sonuc.sentez.map((s) => {
      const kaynak = s.tur === 'celiski'
        ? sentez.celiskiler.find((c) => c.cift[0] === s.sayilar[0] && c.cift[1] === s.sayilar[1])
        : sentez.pekismeler.find((k) => k.ders === s.sayilar[0] && k.fazla === s.sayilar[1]);
      return { ...s, metin: kaynak.metin };
    }),
  };
}

module.exports = {
  kapsamHesapla,
  metinleriSec,
  normalize: (ad, veriDizini) => normalize(ad, harfHaritasi(veriDizini || VARSAYILAN_VERI_DIZINI)),
  indirge,
};
