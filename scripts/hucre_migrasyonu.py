#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kaynak/uretim-metinleri.json (+ inclusion.md) -> data/kapsam-hucreleri.json

METIN KAYNAGI (20 Eyl 2026, kullanici geri bildirimi): frekans >= 1 hucrelerinin
metni, uretimdeki numeroloji uygulamasinin CANLI metinlerinden alinir
(kaynak/uretim-metinleri.json). 2.0 once inclusion.md'yi (ham ceviri) temel
almisti; oysa canli metinler yillar icinde daha sade ve sicak bir Turkceye
cevrilmisti ve 2.0 o sicakligi kaybediyordu ("jest", "iliskisel yetenekleriyle
yasar" gibi ceviri kokan ifadeler). inclusion.md hala okunur: hangi ikame
kuralinin hangi kaynaktan geldigini denetlemek icin.

Uc is yapar:

1. MEKANIK DUZELTME (IKAME tablosu). Ceviri ve cekim hatalari. Her ikame
   denetlenebilir olsun diye burada listelenir; betik hangi ikamenin kac kez
   uygulandigini raporlar. Uygulanmayan bir ikame hata olarak bildirilir
   (kaynak metin degismisse fark etmek icin).

2. ELLE YENIDEN YAZIM (YENI_METIN tablosu). Anlami bozulmus ya da fazla ince
   kalmis hucreler. Ozellikle 1|N ve 5|N satirlari derinlestirilmistir: bunlar
   Turkce adlarda en sik basilan, 1.0'da ise en kisa metinlerdi.

3. METADATA. Her hucreye temalar / anahtar / kutup eklenir. Kutup, metindeki
   cekince yan cumlelerinden turetilir (asagidaki CEKINCE_ISARETLERI).

4. HITAP. Metinler 'siz' ile yazilir, en son 'sen'e cevrilir (scripts/hitap.py).
   Kutup, isaretler 'siz' bicimleriyle tanimli oldugu icin cevirmeden ONCE
   belirlenir.

Kullanim:  python3 scripts/hucre_migrasyonu.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import hitap  # noqa: E402

# --------------------------------------------------------------------------
# Basamak alanlari. Hucre temalari = alan(sayi) + alan(frekans).
# --------------------------------------------------------------------------
ALANLAR = {
    1: ["karar", "girişim", "bağımsızlık", "öncülük"],
    2: ["işbirliği", "duyarlılık", "sezgi", "diplomasi"],
    3: ["ifade", "yaratıcılık", "iletişim", "neşe"],
    4: ["emek", "düzen", "somutluk", "istikrar"],
    5: ["özgürlük", "değişim", "çeşitlilik", "merak"],
    6: ["sorumluluk", "aile", "uyum", "estetik"],
    7: ["analiz", "derinlik", "bilgi", "iç hayat"],
    8: ["güç", "başarı", "maddi dünya", "strateji"],
    9: ["idealler", "insanlık", "şefkat", "evrensellik"],
}

CEKINCE_ISARETLERI = (
    "ancak", "fakat", "oysa", "dikkat", "risk", "tuzak", "aşırı", "engelleyebilir",
    "zorluk", "zorlan", "tereddüt", "dağıt", "dağılma", "çelişk", "gerilim",
    "kaçının", "kaçınmaya", "unutmamanız", "zarar", "bozabilir", "sakının",
)

# --------------------------------------------------------------------------
# 1. MEKANIK IKAMELER  (eski -> yeni, gerekce)
# --------------------------------------------------------------------------
IKAMELER: list[tuple[str, str, str]] = [
    # -- Fransizca "on aime" kalibi: 1. cogul -> 2. cogul --------------------
    ("Yalnız çalışmayı sever, yeteneklerinize",
     "Yalnız çalışmayı seversiniz, yeteneklerinize",
     "4|1 cekim: 'sever' -> 'seversiniz' (cumle ortasinda anlatici degisiyordu)"),
    ("Sıkı, ciddi çalışmayı severiz (ancak biraz yavaş olabilir).",
     "Sıkı ve ciddi çalışmayı seversiniz (temponuz biraz yavaş olabilir).",
     "4|4 cekim + parantez ici ozne belirsizligi"),
    ("Hızlı çalışmayı severiz.", "Hızlı çalışmayı seversiniz.", "4|5 cekim"),
    ("Yardım sektörlerinde çalışmayı severiz.",
     "Yardım alanlarında çalışmayı seversiniz.", "4|6 cekim + 'sektor' yerine 'alan'"),
    ("Şüphesiz entelektüel sektörlerde çalışmayı severiz.",
     "Büyük olasılıkla entelektüel alanlarda çalışmayı seversiniz.",
     "4|7 cekim + 'supheiz' asiri kesinlik + 'sektor'"),
    ("Yüksek kalibreli projelerde enerjik bir şekilde çalışmayı severiz.",
     "Yüksek ölçekli projelerde enerjik biçimde çalışmayı seversiniz.",
     "4|8 cekim + 'kalibre' -> 'olcek'"),
    ("Somut yeteneklerinizi, yenilenebilir ve çeşitlilik sunan girişimler veya aktivitelerde göstermeyi severiz.",
     "Somut yeteneklerinizi, yenilenen ve çeşitlilik sunan girişimlerde göstermeyi seversiniz.",
     "4|5 cekim + 'aktivite' sadelestirme"),
    ("Yaratırken, bunu bağımsız olarak yapmayı severiz.",
     "Yaratırken bunu bağımsız olarak yapmayı seversiniz.", "3|1 cekim"),
    ("kullanmayı severiz", "kullanmayı seversiniz", "5|8 cekim (iki kez)"),
    ("başkalarını kavramların yolunda rehberlik etme fırsatını da severiz",
     "başkalarına kavramlar alanında yol gösterme fırsatını da seversiniz",
     "7|1 cekim + 'rehberlik etme firsati' devrik yapisi"),

    # -- Yazim hatalari -----------------------------------------------------
    ("yardımserverliğiniz", "yardımseverliğiniz", "yazim hatasi (2 kez)"),

    # -- Cevrilmemis / yanlis cevrilmis kelimeler ---------------------------
    ("brutal bir enerjiniz", "sert bir enerjiniz", "6|8 'brutal' cevrilmemis"),
    ("steril bir entelektüel rigora kapatmamaya",
     "kısır bir entelektüel katılığa kapatmamaya", "7|4 'rigor' cevrilmemis"),
    ("Bu plan üzerinde rahatladığınızda",
     "Bu düzlemde rahatladığınızda", "2|7 FR 'sur ce plan' -> 'plan' yanlis cevirisi"),

    # -- 'reserve' (cekingenlik) 'ayricalik' (privilege) diye cevrilmis ------
    ("Bu sayı 2 titreşimine bağlı doğal ayrıcalık, iyi iletişim kurma ve dışa vurum yeteneğiniz nedeniyle büyük bir rol oynamayacaktır.",
     "2 titreşimine bağlı doğal çekingenlik, iyi iletişim kurma ve kendinizi dışa vurma yeteneğiniz sayesinde büyük bir rol oynamayacaktır.",
     "2|3 FR 'reserve' -> 'ayricalik' anlam tersleme"),
    ("2'nin ayrıcalığı ve doğal rezervi, somut ve güvenilir bir arayışla vurgulanır",
     "2'nin çekingenliği ve doğal ihtiyatı, somut ve güvenilir olana duyulan ihtiyaçla pekişir",
     "2|4 FR 'reserve' + cevrilmemis 'rezerv'"),
    ("2 için doğal olan sezgi, somut kanıt ihtiyacının aşırı olması nedeniyle gizlenebilir",
     "2 için doğal olan sezgi, somut kanıt ihtiyacı fazla ağır bastığında gölgede kalabilir",
     "2|4 akicilik"),

    # -- Fransizca kalip cevrileri ------------------------------------------
    ("Bölgenizi kontrol etme yeteneğiniz",
     "Kendi alanınızı koruma ve yönetme yeteneğiniz", "1|8 FR 'territoire'"),
    ("Kolaylıkla \"cesaret edersiniz\".",
     "Girişmek ve risk almak size kolay gelir.", "1|1 FR 'vous osez facilement' birebir ceviri"),
    ("şeylere bakış açınız geneldir", "olaylara bakış açınız geneldir", "1|9 FR 'les choses'"),
    ("Şeyleri basitleştirin ve dramatize etmeyin.",
     "Meseleleri olduğundan büyütmeyin, basit tutun.", "6|6 FR 'les choses' + 'dramatize'"),
    ("Durmadan ilerleyen ve aynı zamanda \"büyük bey\"siniz.",
     "Hem durmadan ilerleyen hem de geniş tavırlı, cömert bir kişiliksiniz.",
     "9|8 FR 'grand seigneur' birebir ceviri"),
    ("Her neyse, bu sosyal rekabette yaklaşımınızdır.",
     "Her durumda, toplumsal rekabete yaklaşımınız budur.", "8|6 bozuk cumle"),
    ("Bu yüzden siz değerli bir sağ kolu (asistan) yaparsınız.",
     "Bu yönünüz sizi çok değerli bir sağ kol yapar.", "7|2 bozuk cumle"),
    ("Geçici yorumlara (sizi incitebilecek olanlara) çok duyarlı olmayın, bu tür küçük şeyler için kendinizi sorgulamayın çünkü bu başarılarınızı engelleyecektir.",
     "Gelip geçici sözlere karşı fazla duyarlı olmayın; bu ölçekteki şeyler için kendinizi sorgulamak ilerlemenizi gereksiz yere yavaşlatır.",
     "7|2 akicilik + 'engelleyecektir' asiri kesinlik"),
    ("(daha çok kavramsal olmak üzere kesinlikle materyal)",
     "(kavramsaldan çok elle tutulur biçimde)", "6|3 bozuk parantez ici"),
    ("pasif bir şekilde aktif olmaktan daha çok kendini gösterecektir",
     "kendini aktif olmaktan çok alıcı bir biçimde gösterecektir", "2|2 bozuk sozdizimi"),
    ("İşbirliği zihninizi, öncelikle somut alanda gösterir",
     "İşbirliği zihniniz kendini öncelikle somut alanda gösterir", "2|8 ozne-yuklem uyumsuzlugu"),
    ("Kendinizi duygusal olarak boğulmuş hissetmeyin. Daha yükseğe çıkmayı deneyin.",
     "Kendinizi duygusal olarak kuşatılmış hissetmemeye dikkat edin; zaman zaman bir adım geri çekilip bütüne bakmak iyi gelir.",
     "6|4 emir kipiyle kurulmus anlamsiz oneri"),
    ("Ciddi ve kesin bir hedefin olmaması, girişimlerinizi engelleyebilir.",
     "Ciddi ve net bir hedefinizin olmaması girişimlerinizi yavaşlatabilir.",
     "1|4 tekil/cogul karismasi + 'engelleyebilir' yumusatma"),
    ("kendinizi biraz ince yayma eğiliminde olabilirsiniz",
     "kendinizi fazla dağıtma eğiliminde olabilirsiniz", "8|3 FR 'se disperser'"),
    ("Kendinizi fazla yayma eğilimi.", "Kendinizi fazla dağıtma eğilimi.", "9|3 FR 'se disperser'"),
    ("Hayatın diğer değerlerini unutmamanız gerektiğine dikkat edin",
     "Hayatın diğer değerlerini gözden kaçırmamaya dikkat edin.", "8|4 eksik nokta + akicilik"),
    ("Etkiniz ve yardımseverliğiniz oldukça belirgin.",
     "Etki alanınız ve yardımseverliğiniz oldukça belirgin.", "9|1 FR 'rayonnement'"),
    ("Etkiniz ve yardımseverliğiniz ,",
     "Etki alanınız ve yardımseverliğiniz,", "9|2 FR 'rayonnement' + bosluk hatasi"),
    ("Yardımseverliğiniz, etkiniz ve açık fikirliliğiniz",
     "Yardımseverliğiniz, etki alanınız ve açık fikirliliğiniz", "9|3 FR 'rayonnement'"),
    ("etkiniz belirli bir şekilde saklıdır",
     "etki alanınız gösterişsiz ve ölçülü kalır", "9|4 FR 'rayonnement' + akicilik"),
    ("Büyük etki ama aynı zamanda dağılma ve yanılsamalar riski.",
     "Geniş bir etki alanı, ama aynı zamanda dağılma ve yanılsama riski.", "9|5 FR 'rayonnement'"),
    ("bu iki titreşime özgü karakteristik dalgalanmalar da gözlemlenir",
     "bu iki titreşime özgü dalgalanmalar da görülür", "3|8 'karakteristik' fazlaligi"),
    ("Kararlarınız spontaneliğiyle karakterize edilir.",
     "Kararlarınız kendiliğindenliğiyle öne çıkar.", "1|3 'karakterize edilir' edilgen kalibi"),
    ("Canlı zeka, spontanlık ve merak sizi karakterize eder",
     "Canlı zekâ, kendiliğindenlik ve merak sizi tanımlar", "3|3 ayni kalip"),
    ("Büyük bir açık fikirliliğiniz, canlı zekanız ve merakınızla karakterize edilirsiniz.",
     "Geniş bir açık fikirlilik, canlı bir zekâ ve güçlü bir merak sizi tanımlar.", "7|5 ayni kalip"),
    ("İçgüdüsellik ve risk ve genişleme isteği sizi karakterize eder.",
     "İçgüdüsel davranma, risk alma ve genişleme isteği sizi tanımlar.", "8|5 ayni kalip + tekrarli 've'"),
    ("Özgün fikirlerinizle karakterize edilirsiniz.",
     "Özgün fikirleriniz sizi öne çıkarır.", "7|1 ayni kalip"),
    # -- Sablon tekrari kirma: "girisimde bulunursunuz" alti hucrede geciyordu
    #    ve tek raporda esigi asiyordu (bkz. sentez.tekrar_denetle) -----------
    ("Arkadaşlık kurmak, işbirliği yapmak, başkalarına karşı nazik olmak için girişimde bulunursunuz.",
     "Arkadaşlık kurmak, işbirliği yapmak ve nazik davranmak için ilk adımı siz atarsınız.",
     "2|1 sablon tekrari"),
    ("Dışa dönük olmak için her zaman girişimde bulunmazsınız",
     "Dışa dönük olmak için her zaman ilk hamleyi yapmazsınız", "3|2 sablon tekrari"),
    ("çatışmaları yatıştırmak veya yeni fikirleri teşvik etmek için girişimde bulunursunuz",
     "çatışmaları yatıştırmak ya da yeni fikirleri desteklemek için harekete geçersiniz",
     "6|1 sablon tekrari"),
    ("etrafınızdaki insanlara yardımcı olmak için girişimde bulunursunuz",
     "etrafınızdaki insanlara yardımcı olmak için önayak olursunuz", "9|1 sablon tekrari"),
    ("diğerlerine yardım etmek için girişimde bulunmanız gerekmez",
     "yardıma önce sizin davranmanız gerekmez", "9|2 sablon tekrari"),
    ("onlara yaratıcılığınızı sunmak için girişimde bulunursunuz",
     "onlara yaratıcılığınızı sunmak için kendiliğinizden öne çıkarsınız", "9|3 sablon tekrari"),
    # -- Fransizca kalintilari: urun dilinde yerlesmemis odunc kelimeler ------
    ("estetizm beğeniniz", "estetik beğeniniz", "6|1 'esthetisme' kalkasi"),
    ("estetizm, konfor", "estetik, konfor", "8|6 ayni"),
    ("uyum, estetizm", "uyum, estetik", "4|6, 6|5 ayni"),
    ("estetizm beğenisi", "estetik beğeni", "6|9 ayni"),
    ("rafine ve dengeli bir şekilde", "incelikli ve dengeli biçimde", "3|6 'raffine'"),
    ("beceri ve rafine bir şekilde", "beceriyle ve incelikle", "2|6 ayni"),
    ("çok rafine bir duyarlılık", "çok incelikli bir duyarlılık", "6|9 ayni"),
    ("Büyük iç rafine", "Büyük bir iç incelik", "7|3 ayni"),
    ("Spontanlık, daha çok", "Kendiliğindenlik daha çok", "3|7 'spontaneite'"),
    ("Spontanlığı seçin.", "Zaman zaman kendiliğinden davranmayı seçin.", "6|7 ayni"),
    ("spontanlık imajınızı", "kendiliğindenlik izleniminizi", "3|4 ayni"),
    ("spontan bir şekilde kullanılır", "kendiliğinden kullanılır", "9|3 ayni"),
    ("dokunma ile ilgili aktivitelerde", "dokunmayla ilgili işlerde", "2|6 'activite'"),
    ("somut ve ciddi aktivitelerde", "somut ve ciddi işlerde", "3|4 ayni"),
    ("6'nın aktivitelerine (estetizm, uyum",
     "6'nın alanlarına (estetik, uyum", "6|5 'activite' + 'esthetisme'"),
    ("ayrıcalıklı hale getirmenize", "öncelikli kılmanıza", "6|4 'privilegier'"),
    ("ayrıcalıklı 9 alanlarına", "9'un ayrıcalık tanıdığı alanlara", "9|8 ayni"),
    ("materyal konularında", "maddi konularda", "7|4 'materiel'"),
    ("materyalizmde olası aşırılıklar", "maddiyata fazla bağlanmada olası aşırılıklar", "8|4 ayni"),
    ("altruizm, adanmışlık", "özgeciliğe, adanmışlığa", "2|9 'altruisme'"),
    ("harmonik bir atmosfer", "uyumlu bir ortam", "3|6 'harmonique'"),
    ("Yüksek teknoloji sektörlerine", "Yüksek teknoloji alanlarına", "3|9 'secteur'"),
    ("naziklik ve incelikle", "nezaket ve incelikle", "4|2 'naziklik' yanlis turetme"),
    ("somut, stabil ve dürüsttür", "somut, sağlam ve dürüsttür", "4|4 'stable'"),
    ("titizliği veya sertliği abartma", "titizliği ya da sertliği abartma", "4|4 akicilik"),
    ("büyük bir manuel yetenek", "elle iş yapmada büyük bir yetenek", "6|4 'manuel'"),
    ("belirli bir durugörü yeteneği", "belirli bir sezme keskinliği", "7|3 'clairvoyance'"),
    ("\"insan merkezcilikte\" veya \"yardımseverlikte\"",
     "insana dönük işlerde ya da yardım alanlarında", "1|9 tirnakli birebir ceviri"),
    ("\"ideallere\" ve \"yardımseverliğe\"", "ideallere ve yardımseverliğe", "4|9 gereksiz tirnak"),

    # -- canli metindeki (kaynak/uretim-metinleri.json) iki ceviri kalintisi --
    ("doğal spontanlığın", "doğallığın", "3|3 'spontanlık' Turkcelesmemis"),
    ("yardım eden sektörlerde", "yardım edilen alanlarda", "4|6 'sektor' is jargonu"),
]

# --------------------------------------------------------------------------
# 2. ELLE YENIDEN YAZILAN HUCRELER
#    1|N ve 5|N satirlari derinlestirildi (en sik basilan, en ince metinler).
#    Ayrica sablon acilisi ("... ile kendinizi ifade edersiniz") kirildi.
# --------------------------------------------------------------------------
YENI_METIN: dict[str, str] = {
    # 1|N ve 5|N: canli metinde en kisa kalan satirlar (cogu iki cumle).
    # 2.0 bunlari derinlestirmisti; 20 Eyl 2026'da derinlik korunup dil
    # sadelestirildi (kullanici geri bildirimi: "akademik degil, sade").
    "1|1": "Enerjik ve yenilikçi bir yanın var; bunu saklamadan, olduğu gibi gösterirsin. Bir işe girişmek, risk almak sana kolay gelir — ortamın hazır olmasını beklemezsin. Yeni şeylere ilgin meraktan çok “kendime ait olsun” isteğinden gelir. Tek bir 1'in sınırı şu: başlatma gücün, sürdürme gücünden fazla. Bu yüzden başladığın işi taşıyacak bir düzene ya da bir ortağa ihtiyacın olur.",
    "1|2": "Karar verirken ve kendini gösterirken ölçülüsün. Sesini yükseltmeden ilerlemeyi seversin; daha çekingen ve daha hassassın. Buna karşılık dostluğun, ikna gücün, birlikte çalışma becerin, sezgilerin ve verdiğin yerinde tavsiyelerle kendini kabul ettirirsin. Burada 1'in doğrudanlığı 2'nin yumuşak yoluna dönüşür: istediğini kavga ederek değil, ikna ederek alırsın.",
    "1|3": "Girişkenliğin yaratıcılık, anlatım gücü ve coşku üzerinden çalışır. Kararların anlıktır; uzun hesap yapmadan atlarsın ve bu çoğu zaman işine yarar. Öne çıkma isteğin yaratıcılığını harekete geçirir — bazen gereğinden fazla. Dikkat edilecek yer şu: bir fikri anlatmakla onu bitirmek aynı şey değil. Anlatma kolaylığın, işi tamamlama disiplininin önüne geçebilir.",
    "1|4": "Girişkenliğin ciddiyet, düzen ve sabırla çalışır; ortaya elle tutulur işler çıkarırsın. Bir işe başlarken temelini de düşünürsün — bu, 1'in aceleciliğini dengeleyen ender bir birleşim. Net bir hedefin yoksa işler yavaşlar: 1 ile 4 birlikte yön ister, yön olmayınca enerji düzene değil oyalanmaya gider.",
    "1|5": "Girişkenliğin çeşitlilik, özgürlük ve yeni fikirler üzerinden ilerler. Bir kapı kapanırsa üç kapıyı birden denersin; bu esneklik en güçlü yanın. Çok fazla kural ve durağan bir ortam hem isteğini hem girişimini söndürür — seni sıkan şey yavaşlık değil, hep aynı şeyi yapmak. Aynı esnekliğin bedeli de var: uzun süren işlerde ilk zorlukta ilgin başka yöne kayabilir.",
    "1|6": "Girişkenliğin uyum alanındaki birikiminle çalışır: sanat, zevk, insan ilişkileri. Uzlaşma becerin ve sorumluluk alman seni çevrende güvenilir kılar. Tek şartın var: attığın adım mevcut dengeyi bozmasın. 1 öne çıkmak ister, 6 kimseyi kırmak istemez. Bunu iyi yönetirsen ikna edici bir liderlik çıkar; yönetemezsen hiç atılmayan adımlar.",
    "1|7": "Girişkenliğin gözlem ve düşünme üzerinden ilerler. Bağımsızlığın daha çok fikirlerinde görünür; kalabalığın gittiği yere gitmemek senin için bir gösteri değil, doğal bir eğilim. Kararlarında değerlerin ve vicdanın ağır basar — bir işin sana uygun olması, kazançlı olmasından önce gelir. Fazlası şu: harekete geçmeden önce çok uzun düşünmek.",
    "1|8": "Kendi alanını koruma ve yönetme becerin güçlü; düştükten sonra toparlanman da hızlı. Bağımsızlığın soyut değil, gösterilebilir olsun istersin: işte, toplum içinde ya da sporda görünen bir başarı. Bu birleşim sana az rastlanan bir dayanıklılık verir. Karşılığında gücü ölçmeyi öğrenmek gerekir; 1 ile 8 birlikte kolayca fazla ileri gider.",
    "1|9": "Girişkenliğin önce ideallerinden ve yüksek duyarlılığından beslenir. Enerjin yaratıcılıkta, bilgi arayışında, insana dokunan ya da yardım eden işlerde serbest kalır. Bir işe girişirken bencil bir yerden değil, herkes için iyi olandan bakarsın. Riskin de burada: büyük resmi görürken önündeki küçük adımı atlayabilirsin.",
    "5|1": "Çok yönlülüğün, canlı zekân, uyum becerin ve özgürlük ihtiyacın kendini anlık, hareketli, özgün, bazen de meydan okuyan biçimde gösterir. Tek bir 1 ile birleşen 5, hızlı karar veren ve hızlı yön değiştiren birini anlatır. Sınırı açık: iş uzun ve zorsa isteğin sonuna kadar sürmeyebilir. Bu tabloyu iyi kullanmanın yolu, uzun işleri kısa parçalara bölmek.",
    "5|2": "Merakın, açık fikirliliğin ve uyum becerin bir iletişim, bir ilişki ya da bir alışveriş kurmak için çalışır. İnsanla temas senin için bir araç değil, enerjinin kendisi. Ama kurduğun ortaklık fazla müdahaleci ya da fazla ağır olmamalı; öyle olunca 5'in özgürlük ihtiyacıyla çatışır ve gerilim başlar. Bu tabloda ilişkiler, nefes payı bırakıldığı sürece iyi gider.",
    "5|3": "Canlılığın, açık fikirliliğin, zekân ve çok yönlülüğün sağlam bir zemin kuruyor. Yeteneklerin daha çok kendini anlatmak, iletişim kurmak ve üretmek için çalışır — anlatmak, senin düşünme biçiminin bir parçası. Coşkulusun; merakın, insanlarla daha iyi iletişim kurmak için öğrenme isteği getirir. 5 ile 3 birlikte hızlı ve parlak bir zihin kurar; eksik kalan, o parlaklığı tek bir konuda derinleştirecek sabır.",
    "5|4": "Açık fikirliliğin, canlılığın ve çok yönlülüğün somut işlere yönelir; sonuç almak ve ilerlemek istersin. Bu, 5'in en verimli birleşimlerinden biri — özgürlük ihtiyacı bir üretim biçimine dönüşür. Ama çalışma hayatı, senin için hayati olan hareket serbestliğini her zaman vermez. Burada asıl mesele işin kendisi değil, işin içindeki serbestlik payı.",
    "5|5": "Enerjin, tutkun, canlı zekân ve her duruma uyum sağlama becerin açıkça öne çıkıyor; çoğu zaman yeni olanın, macera olanın peşinden gidersin. Bu, tablonun tam ortasına oturan bir denge: 5 beklenen düzeyde. Kendi kendini besleyen bir hareketliliğin var, dışarıdan dürtülmeye ihtiyacın az. Buna karşılık kendi hareketini durdurmayı öğrenmek, bu tabloda kimsenin sana öğretmediği tek beceri.",
    "5|6": "Açık fikirliliğin, canlılığın ve uyumun çoğunlukla ailede yaşanır: sıcaklık, sevgi, tutku ve duygusallık üzerinden. Yakınlarına kapalı bir düzen değil, hareketli ve misafir seven bir ortam kurarsın. Aile sorumlulukları seni kısıtlamaya başladığında dengeyi korumak zorlaşabilir. Bu yanının başka çıkış yolları da var: yaratıcılık ve güzellik duygusu.",
    "5|7": "Açık fikirliliğin ve uyum becerin fikirlere yönelir. Merakın bilgi arayışına dönüşür; gözlem gücün ve sezgin kuvvetli. 5'in dışa dönük enerjisi burada içe kıvrılır — dünyayı gezmek yerine bir konunun içinde gezersin. Bunun bedeli dışarıda görünen başarıda çıkar: sen fikri olgunlaştırırken fırsat geçip gidebilir.",
    "5|8": "Açık zihnini, uyum becerini, canlılığını ve çok yönlülüğünü iş dünyasında ve rekabette kullanmayı seversin. Hırsın, risk alma isteğin ve geniş bir alana duyduğun ihtiyaç tavrından belli olur. Büyük enerjini büyük işlere vermek hoşuna gider, ama bu ciddi bir denge ister: 5 ile 8 birlikte hem hızı hem riski aynı anda yükseltir.",
    "5|9": "Açık zihnin ve keşfetme isteğin öne çıkıyor. Bu merakı bilgiye, dünyaya ve insanlara açılmak için kullanırsın. Özgürlüğe, yolculuğa, yeni insanlara ve geniş bir alana ihtiyacın var; hoşgörün de geniş. 5 ile 9 birlikte ufku genişletir ama merkezi zayıflatır: her yere ait olmak, hiçbir yere yerleşememek anlamına gelebilir.",
}


def canli_metinler() -> dict[str, str]:
    """Uretimdeki uygulamanin kapsam metinleri: {"<sayi>|<frekans>": metin}."""
    yol = KOK / "kaynak" / "uretim-metinleri.json"
    ham = json.loads(yol.read_text(encoding="utf-8"))
    cikti = {}
    for satir in ham:
        anahtar = str(satir.get("key", ""))
        if "-" in anahtar and satir.get("yorum"):
            cikti[anahtar.replace("-", "|")] = str(satir["yorum"]).strip()
    return cikti


def satirlari_oku() -> list[tuple[int, int, str]]:
    kaynak = (KOK / "inclusion.md").read_text(encoding="utf-8")
    satirlar = []
    for ham in kaynak.splitlines():
        if not ham.startswith("|"):
            continue
        p = [x.strip() for x in ham.strip().strip("|").split("|")]
        if len(p) != 3 or not p[0].isdigit():
            continue
        satirlar.append((int(p[0]), int(p[1]), p[2]))
    return satirlar


def kutup_belirle(metin: str) -> list[str]:
    alt = metin.lower()
    kutuplar = ["güç"]
    if any(i in alt for i in CEKINCE_ISARETLERI):
        kutuplar.append("gerilim")
    return kutuplar


def main() -> int:
    satirlar = satirlari_oku()
    canli = canli_metinler()
    sayaclar = {eski: 0 for eski, _, _ in IKAMELER}

    hucreler: dict[str, dict] = {}
    elle_yazilan = 0
    orijinaller: dict[str, str] = {}

    for sayi, frekans, metin in satirlar:
        if frekans == 0:
            continue  # Karmik Dersler ayri dosyada (data/karmik-dersler.json)
        anahtar_hucre = f"{sayi}|{frekans}"
        orijinaller[anahtar_hucre] = metin

        if anahtar_hucre in YENI_METIN:
            yeni = YENI_METIN[anahtar_hucre]
            kaynak_tipi = "elle_yazildi"
            elle_yazilan += 1
        else:
            # Taban metin: canli uygulama; yoksa inclusion.md satiri.
            yeni = canli.get(anahtar_hucre, metin)
            taban_canli = anahtar_hucre in canli
            for eski, yerine, _ in IKAMELER:
                if eski in yeni:
                    sayaclar[eski] += yeni.count(eski)
                    yeni = yeni.replace(eski, yerine)
            taban = canli.get(anahtar_hucre, metin)
            kaynak_tipi = ("duzeltildi" if yeni != taban
                           else ("canli_metin" if taban_canli else "degismedi"))

        temalar = list(dict.fromkeys(ALANLAR[sayi] + ALANLAR[frekans]))
        hucreler[anahtar_hucre] = {
            "sayi": sayi,
            "frekans": frekans,
            "metin": hitap.cevir(yeni),
            "temalar": temalar,
            "kutup": kutup_belirle(yeni),
            "kaynak": kaynak_tipi,
        }

    # Bir kural uygulanmadiysa uc olasilik var:
    #  (a) hedef hucre elle yeniden yazildi -> kural gereksiz, hata degil;
    #  (b) kural inclusion.md'ye aitti, taban artik canli metin -> bilgi;
    #  (c) hicbir kaynakta karsiligi yok -> kural curumus, hata.
    gereksiz: list[tuple[str, str]] = []
    canliya_gecti: list[tuple[str, str]] = []
    kacirilan: list[tuple[str, str]] = []
    md_tum = chr(10).join(orijinaller.values())
    for eski, _, gerekce in IKAMELER:
        if sayaclar[eski]:
            continue
        if any(eski in orijinaller.get(h, "") for h in YENI_METIN):
            gereksiz.append((eski, gerekce))
        elif eski in md_tum:
            canliya_gecti.append((eski, gerekce))
        else:
            kacirilan.append((eski, gerekce))

    cikti = {
        "surum": "2.0",
        "aciklama": "Kapsam tablosunun frekans >= 1 hucreleri. Metin, sayi ile frekansin karisimini (blend) anlatir; frekansin NICELIGI ayri bir katmanda okunur (data/yogunluk.json). Bu ayrim 1.0'da karismis durumdaydi.",
        "uretim": {
            "betik": "scripts/hucre_migrasyonu.py",
            "kaynak": "kaynak/uretim-metinleri.json (canli metinler) + inclusion.md",
            "hucre_sayisi": len(hucreler),
            "elle_yazilan": elle_yazilan,
            "mekanik_duzeltme_sayisi": sum(sayaclar.values()),
            "yeniden_yazimla_kapsanan_kural": len(gereksiz),
        },
        "kutup_turetme_notu": "kutup alanindaki 'gerilim' etiketi, metinde cekince yan cumlesi bulunmasindan turetilir; elle atanmamistir.",
        "hucreler": hucreler,
    }

    hedef = KOK / "data" / "kapsam-hucreleri.json"
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"yazildi: {hedef}")
    print(f"  hucre            : {len(hucreler)}")
    print(f"  elle yazilan     : {elle_yazilan}")
    print(f"  mekanik duzeltme : {sum(sayaclar.values())} uygulama, "
          f"{sum(1 for v in sayaclar.values() if v)} / {len(IKAMELER)} kural")
    if gereksiz:
        print(f"\n  bilgi - yeniden yazimla kapsandigi icin uygulanmayan "
              f"{len(gereksiz)} kural:")
        for _, g in gereksiz:
            print(f"    . {g}")
    if canliya_gecti:
        print(f"\n  bilgi - taban metin canliya gectigi icin uygulanmayan "
              f"{len(canliya_gecti)} kural (ilgili ifade canli metinde zaten yok):")
        for _, g in canliya_gecti:
            print(f"    . {g}")
    if kacirilan:
        print("\n  HATA - hedefini bulamayan ikame kurallari "
              "(kaynak metin beklendigi gibi degil):")
        for e, g in kacirilan:
            print(f"    - {g}\n      arandi: {e[:70]!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
