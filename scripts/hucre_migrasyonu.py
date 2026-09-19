#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inclusion.md (surum 1.0) -> data/kapsam-hucreleri.json (surum 2.0)

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
]

# --------------------------------------------------------------------------
# 2. ELLE YENIDEN YAZILAN HUCRELER
#    1|N ve 5|N satirlari derinlestirildi (en sik basilan, en ince metinler).
#    Ayrica sablon acilisi ("... ile kendinizi ifade edersiniz") kirildi.
# --------------------------------------------------------------------------
YENI_METIN: dict[str, str] = {
    "1|1": "Bireyselliğiniz tek bir 1 üzerinden çalışır: net, dolambaçsız ve fazla süslenmeden. Girişmek ve risk almak size kolay gelir; bir işi başlatmak için ortamın hazır olmasını beklemezsiniz. Yeniliğe duyduğunuz ilgi meraktan çok sahiplenme isteğinden gelir — kendinize ait bir şey kurmak istersiniz. Tek bir 1'in sınırı şudur: başlangıç gücü kadar sürdürme gücünüz yoktur, bu yüzden başladığınız işi taşıyacak bir yapıya ya da bir ortağa ihtiyaç duyarsınız.",
    "1|2": "Karar verme ve kendinizi ortaya koyma biçiminiz ölçülü. Daha çekingen ve daha hassassınız; sesinizi yükseltmeden ilerlemeyi tercih edersiniz. Buna karşın dostluk anlayışınız, diplomatik yetenekleriniz, işbirliği kapasiteniz, sezgileriniz ve verdiğiniz isabetli tavsiyelerle kendinizi kabul ettirirsiniz — bunlar sizin için gerçek değerler. Bu tablo, 1'in doğrudanlığını 2'nin dolaylı yollarına çevirir: istediğinizi elde ederken çarpışmak yerine ikna edersiniz.",
    "1|3": "Girişimciliğiniz yaratıcılık, ifade yeteneği ve coşku üzerinden ilerler. Kararlarınız kendiliğindenliğiyle öne çıkar; uzun hesaplar yapmadan atlarsınız ve bu çoğu zaman işinize yarar. Ön planda olma arzusu doğal yaratıcılığınızı harekete geçirecek — belki gereğinden fazla. Dikkat edilecek yer, bir fikri anlatmakla onu gerçekleştirmenin aynı şey olmadığı: anlatma kolaylığınız, bitirme disiplininizin önüne geçebilir.",
    "1|4": "Girişimciliğiniz ciddi niteliklerle, organizasyon yeteneğiyle, azimle ve elle tutulur başarılarla çalışır. Bir işe girerken temelini de düşünürsünüz; bu, 1'in aceleciliğini dengeleyen ender bir birleşim. Ciddi ve net bir hedefinizin olmaması girişimlerinizi yavaşlatabilir — 1 ile 4 birlikte yön istiyor; yön yoksa enerji düzene değil oyalanmaya gider.",
    "1|5": "Girişimciliğiniz çeşitlilik, özgürlük tutkusu ve yeni fikirler üzerinden ilerler. Bir kapı kapanırsa üçünü birden denersiniz; bu esneklik sizin en güçlü tarafınız. Çok fazla kısıtlama ve durağan bir çevre arzularınızı da girişimlerinizi de söndürür — sizin için sıkıcı olan, yavaş olan değil tekrarlı olandır. Aynı esnekliğin bedeli, uzun soluklu işlerde ilginizin ilk zorlukta başka yöne kayması.",
    "1|6": "Girişimciliğiniz uyum alanındaki birikiminizle çalışır: sanat, zevk, toplumsal ilişkiler. Uzlaşma yeteneğiniz ve sorumluluk üstlenme kapasiteniz sizi çevrenizde güvenilir kılar. Tek şartınız, attığınız adımın mevcut dengeyi bozmaması — 1 öne çıkmak isterken 6 kimseyi kırmamak ister. Bu gerilim iyi yönetildiğinde ikna edici bir liderlik, kötü yönetildiğinde hiç atılmayan adımlar üretir.",
    "1|7": "Girişimciliğiniz gözlem ve düşünme üzerinden ilerler. Bağımsızlığınız çoğunlukla fikirlerde ve özgünlükte görünür; kalabalığın gittiği yere gitmemek sizin için bir tavır değil, doğal bir eğilim. Kararlarınız değerler sisteminizden ve ahlaki yapınızdan güçlü biçimde etkilenir — bir işin size uygun olması, kârlı olmasından önce gelir. Fazlası, harekete geçmeden önce çok uzun süre düşünmek.",
    "1|8": "Kendi alanınızı koruma ve yönetme yeteneğiniz ile başarısızlık sonrası toparlanma gücünüz belirgin. Bağımsızlığınız ve dinamizminiz somut alanlarda, toplumsal ya da sportif başarıda görünür hale gelir; soyut bir bağımsızlık değil, gösterilebilir bir bağımsızlık istersiniz. Bu birleşim size sıra dışı bir dayanıklılık verir — düştüğünüz yerden kalkma süreniz kısadır. Karşılığında, gücü ölçmeyi öğrenmek gerekir; 1 ile 8 birlikte kolayca fazla ileri gider.",
    "1|9": "Girişimciliğiniz önce ideallerinizden ve yüksek duyarlılığınızdan beslenir. Bağımsızlığınız ve dinamizminiz yaratıcılıkta, bilgi arayışında, insana dönük işlerde ya da yardım alanlarında serbest kalır. Girişme biçiminiz evrensel bir yerden çalışır, bencillikten uzaktır ve olaylara bakış açınız geneldir. Riski de buradan gelir: geneli görmek, önünüzdeki somut adımı gözden kaçırmanıza yol açabilir.",

    "5|1": "Çeşitliliğiniz, canlı zekânız, uyum yeteneğiniz ve özgürlük ihtiyacınız kendini kendiliğinden, dinamik, özgün ve zaman zaman kışkırtıcı biçimde gösterir. Tek bir 1 ile birleşen 5, hızlı karar veren ve hızlı yön değiştiren bir yapı kurar. Sınırı açık: girişim uzun ve zorluysa, sonuç alınana kadar istek her zaman sürmez. Bu tabloyu iyi kullanmanın yolu, uzun işleri kısa etaplara bölmek.",
    "5|2": "Merak, açık fikirlilik ve uyum yeteneğiniz bir iletişim, bir ilişki ya da bir alışveriş kurmak için çalışır. İnsanla temas sizin için bir araç değil, enerjinin kendisi. Ancak kurulan işbirliğinin fazla müdahaleci ya da fazla ağır olmaması gerekir; öyle olduğunda 5'in özgürlük ihtiyacıyla çatışır ve gergin bir durum doğar. Bu tabloda ilişkiler, nefes payı bırakıldığı sürece iyi işler.",
    "5|3": "Canlılığınız, açık fikirliliğiniz, zekânız ve çok yönlülüğünüz sağlam bir zemin oluşturuyor. Yetenekleriniz öncelikle kendinizi ifade etme, iletişim ve yaratıcılık yönünde kullanılır — anlatmak sizin için düşünmenin bir parçası. Coşkunuz var ve doğal merakınız, başkalarıyla daha iyi iletişim kurmak amacıyla öğrenme isteği getirir. 5 ile 3 birlikte hızlı ve parlak bir zihin kurar; eksik kalan, o parlaklığı tek bir konuda derinleştirme sabrı.",
    "5|4": "5'in açık fikirliliği, canlılığı, çok yönlülüğü ve enerjisi somut dış etkinliklere yönelir; sonuç almak ve ilerlemek istersiniz. Bu, 5'in en verimli birleşimlerinden biri — özgürlük ihtiyacı bir üretim biçimine dönüşür. Ancak çalışma dünyasının talepleri, 5 için hayati olan hareket özgürlüğünü her zaman sunmaz. Bu tablodaki asıl mesele, işin kendisi değil işin içindeki serbestlik payı.",
    "5|5": "5'in enerjisi, tutkusu, canlı zekâsı ve en çeşitli duruma uyum sağlama yeteneği belirgin biçimde öne çıkar ve çoğunlukla yeni olanın, macera olanın peşinde kendiliğinden ifade bulur. Bu, tablonun doğal merkezine oturan bir denge: 5, beklenen düzeyde. Kendi kendini besleyen bir hareketlilik taşırsınız; dışarıdan uyarıya ihtiyacınız az. Buna karşılık kendi hareketinizi durdurmayı öğrenmek, bu tabloda dışarıdan gelen hiçbir şeyin öğretmediği tek beceri.",
    "5|6": "Açık fikirlilik, canlılık ve uyum yeteneği ağırlıklı olarak aile içinde yaşanır: uyum, insan sıcaklığı, aşk, tutku ve duygusallık üzerinden. Yakınlarınıza kapalı bir düzen değil, hareketli ve konuk kabul eden bir ortam kurarsınız. Aile sorumlulukları kısıtlayıcı hale geldiğinde dengeyi korumak zorlaşabilir. Niteliklerinizin diğer olası ifadeleri yaratıcılık ve estetik duyarlılık.",
    "5|7": "Açık fikirlilik ve uyum yeteneğiniz kavramlara ve yeni fikirlere yönelir. Merak entelektüel bir biçimde, bilgi arayışı içinde kullanılır; gözlem yeteneği ve sezgi mevcut. 5'in dışa dönük enerjisi burada içe kıvrılır — dünyayı gezmek yerine bir konunun içinde gezinirsiniz. Bunun bedeli, dışa dönük başarı tarafında bir zayıflık: fikir olgunlaşırken fırsat geçebilir.",
    "5|8": "Açık zihninizi, uyum yeteneğinizi, canlılığınızı ve çok yönlülüğünüzü maddi ve rekabetçi dünyada başarılı olmak için kullanmayı seversiniz. Hırsınız, risk alma isteğiniz ve yaşam alanına duyduğunuz ihtiyaç tutumunuzda görülür. Büyük enerjinizi yüksek ölçekli projeler için kullanmayı seversiniz, ancak bu ciddi bir denge becerisi gerektirir — 5 ile 8 birlikte hem hızı hem de riski aynı anda yükseltir.",
    "5|9": "Açık zihniniz ve keşfetme isteğiniz belirgin biçimde öne çıkar. Bu merakı ve doğal enerjiyi bilgiye, dünyaya ve insanlara açıklık yönünde kullanmaya eğilimlisiniz. Özgürlüğe, seyahate, insanlarla tanışmaya ve geniş bir alana yayılmaya ihtiyacınız var; büyük bir hoşgörü taşıyorsunuz. 5 ile 9 birlikte ufku genişletir ama merkezi zayıflatır: her yere ait olmak, hiçbir yere yerleşmemek anlamına gelebilir.",
}


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
            yeni = metin
            for eski, yerine, _ in IKAMELER:
                if eski in yeni:
                    sayaclar[eski] += yeni.count(eski)
                    yeni = yeni.replace(eski, yerine)
            kaynak_tipi = "duzeltildi" if yeni != metin else "degismedi"

        temalar = list(dict.fromkeys(ALANLAR[sayi] + ALANLAR[frekans]))
        hucreler[anahtar_hucre] = {
            "sayi": sayi,
            "frekans": frekans,
            "metin": hitap.cevir(yeni),
            "temalar": temalar,
            "kutup": kutup_belirle(yeni),
            "kaynak": kaynak_tipi,
        }

    # Bir kural uygulanmadiysa iki olasilik var:
    #  (a) hedef hucre elle yeniden yazildi -> kural gereksiz, hata degil;
    #  (b) kaynak metin beklendigi gibi degil -> gercek kacirma, hata.
    gereksiz: list[tuple[str, str]] = []
    kacirilan: list[tuple[str, str]] = []
    for eski, _, gerekce in IKAMELER:
        if sayaclar[eski]:
            continue
        kapsandi = any(eski in orijinaller.get(h, "") for h in YENI_METIN)
        (gereksiz if kapsandi else kacirilan).append((eski, gerekce))

    cikti = {
        "surum": "2.0",
        "aciklama": "Kapsam tablosunun frekans >= 1 hucreleri. Metin, sayi ile frekansin karisimini (blend) anlatir; frekansin NICELIGI ayri bir katmanda okunur (data/yogunluk.json). Bu ayrim 1.0'da karismis durumdaydi.",
        "uretim": {
            "betik": "scripts/hucre_migrasyonu.py",
            "kaynak": "inclusion.md (surum 1.0)",
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
    if kacirilan:
        print("\n  HATA - hedefini bulamayan ikame kurallari "
              "(kaynak metin beklendigi gibi degil):")
        for e, g in kacirilan:
            print(f"    - {g}\n      arandi: {e[:70]!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
