# son-dakika-haber yerel kaynaklar

Yerel haber routine'lerinin okuduğu dosyalar. **Bu repo gizli (private) olmalı ve sitenin kodunu içermemeli.**

- `KURALLAR.md`: bütün il routine'lerinin ortak kuralları (değişince tüm routine'ler bir sonraki çalışmada yeni hali kullanır)
- `il-kaynaklari/`: her ilin resmî kaynakları (şema: `il-kaynaklari/SEMA.md`)
- `il-promptlari/`: her il routine'inin kısa promptu ve zamanlaması
- `araclar/prompt_uret.py`: kaynak dosyalarından promptları ve bu tabloyu yeniden üretir

Toplam 65 il.

| Plaka | İl | Saat | Prompt |
|---|---|---|---|
| 01 | Adana | 07:05 ve 16:05 | il-promptlari/01-adana.md |
| 02 | Adıyaman | 07:16 ve 16:16 | il-promptlari/02-adiyaman.md |
| 03 | Afyonkarahisar | 07:27 ve 16:27 | il-promptlari/03-afyonkarahisar.md |
| 04 | Ağrı | 07:38 ve 16:38 | il-promptlari/04-agri.md |
| 05 | Amasya | 07:49 ve 16:49 | il-promptlari/05-amasya.md |
| 06 | Ankara | 08:05 ve 17:05 | il-promptlari/06-ankara.md |
| 07 | Antalya | 08:16 ve 17:16 | il-promptlari/07-antalya.md |
| 08 | Artvin | 08:27 ve 17:27 | il-promptlari/08-artvin.md |
| 09 | Aydın | 08:38 ve 17:38 | il-promptlari/09-aydin.md |
| 10 | Balıkesir | 08:49 ve 17:49 | il-promptlari/10-balikesir.md |
| 11 | Bilecik | 09:05 ve 18:05 | il-promptlari/11-bilecik.md |
| 12 | Bingöl | 09:16 ve 18:16 | il-promptlari/12-bingol.md |
| 13 | Bitlis | 09:27 ve 18:27 | il-promptlari/13-bitlis.md |
| 14 | Bolu | 09:38 ve 18:38 | il-promptlari/14-bolu.md |
| 15 | Burdur | 09:49 ve 18:49 | il-promptlari/15-burdur.md |
| 16 | Bursa | 10:05 ve 19:05 | il-promptlari/16-bursa.md |
| 17 | Çanakkale | 10:16 ve 19:16 | il-promptlari/17-canakkale.md |
| 18 | Çankırı | 10:27 ve 19:27 | il-promptlari/18-cankiri.md |
| 19 | Çorum | 10:38 ve 19:38 | il-promptlari/19-corum.md |
| 20 | Denizli | 10:49 ve 19:49 | il-promptlari/20-denizli.md |
| 21 | Diyarbakır | 07:05 ve 16:05 | il-promptlari/21-diyarbakir.md |
| 22 | Edirne | 07:16 ve 16:16 | il-promptlari/22-edirne.md |
| 23 | Elazığ | 07:27 ve 16:27 | il-promptlari/23-elazig.md |
| 24 | Erzincan | 07:38 ve 16:38 | il-promptlari/24-erzincan.md |
| 25 | Erzurum | 07:49 ve 16:49 | il-promptlari/25-erzurum.md |
| 26 | Eskişehir | 08:05 ve 17:05 | il-promptlari/26-eskisehir.md |
| 27 | Gaziantep | 08:16 ve 17:16 | il-promptlari/27-gaziantep.md |
| 28 | Giresun | 08:27 ve 17:27 | il-promptlari/28-giresun.md |
| 29 | Gümüşhane | 08:38 ve 17:38 | il-promptlari/29-gumushane.md |
| 30 | Hakkari | 08:49 ve 17:49 | il-promptlari/30-hakkari.md |
| 31 | Hatay | 09:05 ve 18:05 | il-promptlari/31-hatay.md |
| 32 | Isparta | 09:16 ve 18:16 | il-promptlari/32-isparta.md |
| 33 | Mersin | 09:27 ve 18:27 | il-promptlari/33-mersin.md |
| 34 | İstanbul | 09:38 ve 18:38 | il-promptlari/34-istanbul.md |
| 35 | İzmir | 09:49 ve 18:49 | il-promptlari/35-izmir.md |
| 36 | Kars | 10:05 ve 19:05 | il-promptlari/36-kars.md |
| 37 | Kastamonu | 10:16 ve 19:16 | il-promptlari/37-kastamonu.md |
| 38 | Kayseri | 10:27 ve 19:27 | il-promptlari/38-kayseri.md |
| 39 | Kırklareli | 10:38 ve 19:38 | il-promptlari/39-kirklareli.md |
| 40 | Kırşehir | 10:49 ve 19:49 | il-promptlari/40-kirsehir.md |
| 41 | Kocaeli | 07:05 ve 16:05 | il-promptlari/41-kocaeli.md |
| 42 | Konya | 07:16 ve 16:16 | il-promptlari/42-konya.md |
| 43 | Kütahya | 07:27 ve 16:27 | il-promptlari/43-kutahya.md |
| 44 | Malatya | 07:38 ve 16:38 | il-promptlari/44-malatya.md |
| 45 | Manisa | 07:49 ve 16:49 | il-promptlari/45-manisa.md |
| 46 | Kahramanmaraş | 08:05 ve 17:05 | il-promptlari/46-kahramanmaras.md |
| 47 | Mardin | 08:16 ve 17:16 | il-promptlari/47-mardin.md |
| 48 | Muğla | 08:27 ve 17:27 | il-promptlari/48-mugla.md |
| 49 | Muş | 08:38 ve 17:38 | il-promptlari/49-mus.md |
| 50 | Nevşehir | 08:49 ve 17:49 | il-promptlari/50-nevsehir.md |
| 51 | Niğde | 09:05 ve 18:05 | il-promptlari/51-nigde.md |
| 52 | Ordu | 09:16 ve 18:16 | il-promptlari/52-ordu.md |
| 53 | Rize | 09:27 ve 18:27 | il-promptlari/53-rize.md |
| 54 | Sakarya | 09:38 ve 18:38 | il-promptlari/54-sakarya.md |
| 55 | Samsun | 09:49 ve 18:49 | il-promptlari/55-samsun.md |
| 56 | Siirt | 10:05 ve 19:05 | il-promptlari/56-siirt.md |
| 57 | Sinop | 10:16 ve 19:16 | il-promptlari/57-sinop.md |
| 58 | Sivas | 10:27 ve 19:27 | il-promptlari/58-sivas.md |
| 59 | Tekirdağ | 10:38 ve 19:38 | il-promptlari/59-tekirdag.md |
| 60 | Tokat | 10:49 ve 19:49 | il-promptlari/60-tokat.md |
| 61 | Trabzon | 07:05 ve 16:05 | il-promptlari/61-trabzon.md |
| 62 | Tunceli | 07:16 ve 16:16 | il-promptlari/62-tunceli.md |
| 63 | Şanlıurfa | 07:27 ve 16:27 | il-promptlari/63-sanliurfa.md |
| 64 | Uşak | 07:38 ve 16:38 | il-promptlari/64-usak.md |
| 65 | Van | 07:49 ve 16:49 | il-promptlari/65-van.md |
