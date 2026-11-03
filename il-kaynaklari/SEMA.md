# İl kaynakları şeması (her il bir JSON dosyası: {plaka}-{slug}.json)

Amaç: yerel haber routine'lerinin bakacağı resmî kaynaklar. Haber bilgisi yalnızca "resmi" kaynaklardan alınır;
"ipucu" kaynakları sadece konu bulmak içindir.

{
  "il": "Kütahya",
  "plaka": "43",
  "slug": "kutahya",
  "site_sehir_sayfasi": "https://son-dakika-haber.com.tr/sehir/kutahya",
  "buyuksehir": false,
  "ilceler": ["Merkez", "..."],
  "resmi": [
    {"tur": "valilik", "kurum": "Kütahya Valiliği", "url": "https://...", "duyuru_url": "https://.../duyurular", "durum": 200, "not": ""},
    {"tur": "belediye", ...}, {"tur": "il_meb", ...}, {"tur": "su", ...}, {"tur": "elektrik", ...},
    {"tur": "dogalgaz", ...}, {"tur": "saglik", ...}, {"tur": "emniyet", ...}, {"tur": "jandarma", ...},
    {"tur": "afad", ...}, {"tur": "universite", ...}, {"tur": "ilce_belediye", ...}, {"tur": "diger", ...}
  ],
  "ipucu": [
    {"tur": "google_news_rss", "url": "https://news.google.com/rss/search?q=K%C3%BCtahya+when:1d&hl=tr&gl=TR&ceid=TR:tr"},
    {"tur": "yerel_gazete", "ad": "...", "url": "https://...", "durum": 200}
  ],
  "deger_konulari": ["planlı elektrik kesintisi", "..."],
  "notlar": "Sitelerin yapısı, duyuruların hangi sayfada olduğu, erişim sorunları"
}

"durum": doğrulamada alınan HTTP kodu (200 = açılıyor). Açılmayan/şüpheli adresler "not" alanında belirtilir.
