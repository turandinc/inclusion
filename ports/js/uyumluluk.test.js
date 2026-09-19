'use strict';
// Kullanım: node ports/js/uyumluluk.test.js
// tests/uyumluluk-vektorleri.json içindeki her vektörü JS portuyla hesaplar
// ve "beklenen" bloğuyla alan alan karşılaştırır. Sapma varsa 1 ile çıkar.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { kapsamHesapla, metinleriSec, indirge } = require('./numeroloji');

const VEKTOR_YOLU = path.resolve(__dirname, '..', '..', 'tests', 'uyumluluk-vektorleri.json');
const { vektorler } = JSON.parse(fs.readFileSync(VEKTOR_YOLU, 'utf8'));

const numKeys = (o) => Object.fromEntries(Object.entries(o).map(([k, v]) => [String(k), v]));

function uret(v) {
  const r = kapsamHesapla(v.ad, v.dogum_tarihi);
  const alan = (a) => numKeys(Object.fromEntries(Object.values(r.okumalar).map((o) => [o.sayi, o[a]])));
  const { telafi_kumesi, ...c } = r.cekirdek;
  return {
    ad_duz: r.ad_duz,
    harf_sayisi: r.harf_sayisi,
    cekirdek: { ...c, telafi_kumesi },
    frekanslar: numKeys(r.frekanslar),
    beklenen_frekans: alan('beklenen'),
    z: alan('z'),
    siniflar: alan('sinif'),
    metin_varyantlari: alan('metin_varyanti'),
    karmik_dersler: r.karmik_dersler,
    telafi_edilmis_dersler: r.telafi_edilmis_dersler,
    asiri_sayilar: r.asiri_sayilar,
    gizli_tutku: r.gizli_tutku,
    gizli_tutku_ortaklari: r.gizli_tutku_ortaklari,
    gizli_tutku_karakteri: r.gizli_tutku_karakteri,
    tek_toplam: r.denge.tek_toplam,
    cift_toplam: r.denge.cift_toplam,
    tek_z: r.denge.tek_z,
    tek_cift_sinif: r.denge.tek_cift_sinif,
    eksenler: Object.fromEntries(Object.entries(r.denge.eksenler).map(([k, e]) =>
      [k, { toplam: e.toplam, beklenen: e.beklenen, z: e.z, sinif: e.sinif }])),
    sentez: r.sentez.map((s) => ({ tur: s.tur, sayilar: s.sayilar })),
  };
}

let hata = 0;
let gecen = 0;

// Kılavuzdaki tuzak örnekleri
try {
  assert.strictEqual(indirge([5, 6]), 11);
  assert.strictEqual(indirge([9, 9, 2]), 2);
} catch (e) { hata++; console.error('indirge:', e.message); }

for (const v of vektorler) {
  try {
    const gercek = uret(v);
    for (const k of Object.keys(v.beklenen)) {
      assert.deepStrictEqual(gercek[k], v.beklenen[k], `${v.ad} → ${k}`);
    }
    // Metin seçimi her vektörde boş olmayan metin döndürmeli (7|8 vb. hariç).
    const m = metinleriSec(kapsamHesapla(v.ad, v.dogum_tarihi));
    for (const s of m.sayilar) {
      const olasiYok = s.varyant === 'hucre' && ['7|8', '7|9', '8|9'].includes(`${s.sayi}|${s.frekans}`);
      if (!s.metin && !olasiYok) throw new Error(`${v.ad} → ${s.sayi}|${s.frekans} için metin yok`);
    }
    if (!m.gizli_tutku.metin || !m.tek_cift || m.sentez.some((s) => !s.metin)) {
      throw new Error(`${v.ad} → bütün okuması metni eksik`);
    }
    gecen++;
    console.log(`  ok  ${v.ad}`);
  } catch (e) {
    hata++;
    console.error(`FAIL  ${e.message}`);
    if (e.actual !== undefined) console.error('   gerçek  :', JSON.stringify(e.actual), '\n   beklenen:', JSON.stringify(e.expected));
  }
}

console.log(`\n${gecen}/${vektorler.length} vektör geçti${hata ? ` — ${hata} hata` : ''}`);
process.exit(hata ? 1 : 0);
