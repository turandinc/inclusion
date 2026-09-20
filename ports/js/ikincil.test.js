'use strict';
// Kullanım: node ports/js/ikincil.test.js
// İkincil tablo (sonradan edinilen soyad) okumasını sınar: her etki türü
// gerçek bir örnekle tetiklenmeli ve her sayı için metin dolu gelmeli.

const assert = require('assert');
const { kapsamHesapla, ikincilOkuma, ikincilBolumNotu } = require('./numeroloji');

const ORNEKLER = [
  ['Ayşe Nur Karahasanoğlu', 'Yılmaz', '1990-03-17'],
  ['Zeynep Çelik', 'Aydın', '2001-11-29'],
  ['Sevda Ak', 'Demir', '2020-02-02'],
  ['Fatma Nur Şimşek', 'Öztürk', '1975-03-13'],
  ['Emre Koç', 'Yıldırım', '2000-01-01'],
  ['Kaan Uz', 'Şahin', '2015-05-05'],
];

const BEKLENEN_ETKILER = new Set([
  'kapanma', 'guclenme', 'yumusama', 'ayni_yonde', 'destek_yok', 'destek_yok_seyrelme',
]);

let hata = 0;
const gorulen = new Set();

for (const [ad, esSoyadi, dt] of ORNEKLER) {
  try {
    const ana = kapsamHesapla(ad, dt);
    const ikincil = kapsamHesapla(`${ad} ${esSoyadi}`, dt);
    const okumalar = ikincilOkuma(ana, ikincil);

    assert.strictEqual(okumalar.length, 9, `${ad}: 9 satır bekleniyor`);
    for (const o of okumalar) {
      assert.ok(BEKLENEN_ETKILER.has(o.etki), `${ad} → bilinmeyen etki: ${o.etki}`);
      assert.ok(o.metin && o.metin.length > 40, `${ad} → ${o.sayi} için metin yok`);
      assert.ok(!o.metin.includes('{tema}'), `${ad} → ${o.sayi}: {tema} yer tutucusu kalmış`);
      assert.ok(o.etiket, `${ad} → ${o.sayi} için etiket yok`);
      // Eksik bir sayı doluyorsa etki mutlaka "kapanma" olmalı.
      if (o.anaFrekans === 0 && o.ikincilFrekans > 0) {
        assert.strictEqual(o.etki, 'kapanma', `${ad} → ${o.sayi}: eksik doldu ama kapanma değil`);
      }
      gorulen.add(o.etki);
    }
    console.log(`  ok  ${ad} + ${esSoyadi}`);
  } catch (e) {
    hata++;
    console.error(`FAIL  ${e.message}`);
  }
}

// Bölüm notu ve kapanma metinlerinin disiplin kuralı
try {
  assert.ok(ikincilBolumNotu().length > 80, 'bölüm notu boş');
  for (let n = 1; n <= 9; n++) {
    const ana = kapsamHesapla('Ece Su', '2010-10-10');
    const ik = kapsamHesapla('Ece Su Ak', '2010-10-10');
    ikincilOkuma(ana, ik); // atmamalı
  }
} catch (e) { hata++; console.error('FAIL  ' + e.message); }

// Kapanma metinleri, dersin kalktığını ASLA söylememeli (disiplin kuralı).
try {
  const veri = require('../../data/ikincil-tablo.json');
  for (const [n, s] of Object.entries(veri.sayilar)) {
    assert.ok(/ders/i.test(s.kapanma), `${n}: kapanma metni Karmik Ders'e değinmeli`);
    assert.ok(!/ders(in)? (ortadan )?kalkar|ders biter/i.test(s.kapanma), `${n}: kapanma metni dersi kaldırıyor`);
  }
} catch (e) { hata++; console.error('FAIL  ' + e.message); }

console.log(`\n${ORNEKLER.length - hata}/${ORNEKLER.length} örnek geçti · görülen etkiler: ${[...gorulen].sort().join(', ')}`);
process.exit(hata ? 1 : 0);
