#!/usr/bin/env python3
"""81 il için tek n8n workflow'u üretir: n8n/workflows/tum-iller.json
Kullanım (repo kökünden): python3 n8n/il_workflow_uret.py

Bilgi toplama (RSS, resmî sayfalar, detay sayfaları, AFAD, sitedeki haberler) n8n'de yapılır;
dil modeli tek çağrıda yalnızca verilen metinlerden haber yazar (araç çağırmaz); yayını n8n MCP ile yapar.
Model çağrısı sıralı yedeklidir: hata veren modelde bir sonrakine geçilir."""
import json, sys, os, glob, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_CRED = {"httpBearerAuth": {"id": "CFRf5QKEa5UP0nb0", "name": "son-dakika-haber-mcp"}}
SAYFA_TURLERI = ['valilik', 'belediye', 'il_meb', 'su', 'saglik', 'emniyet', 'jandarma', 'afad', 'ilce_belediye', 'universite', 'dogalgaz']


def gnews(q):
    return 'https://news.google.com/rss/search?q=' + urllib.parse.quote_plus(q + ' when:1d') + '&hl=tr&gl=TR&ceid=TR:tr'


def il_ayarlari(d):
    ilceler = [x for x in d.get('ilceler', []) if x.lower() != 'merkez']
    buyuk = [s['kurum'].replace(' Belediyesi', '') for s in d['resmi'] if s['tur'] == 'ilce_belediye'][:4]
    rss = [{'kaynak': 'Google Haberler (' + d['il'] + ')', 'url': gnews(d['il'])}]
    if buyuk:
        rss.append({'kaynak': 'Google Haberler (ilçeler)', 'url': gnews('(' + ' OR '.join(buyuk) + ') ' + d['il'])})
    rss.append({'kaynak': 'Google Haberler (duyuru/kesinti)', 'url': gnews(d['il'] + ' (kesinti OR duyuru OR valilik OR "okullar tatil")')})
    sayfalar = []
    for s in d['resmi']:
        if s.get('rss') and s.get('durum') == 200:
            rss.append({'kaynak': s['kurum'], 'url': s['rss']})
        url = s.get('duyuru_url') or s.get('url')
        if s['tur'] in SAYFA_TURLERI and url and s.get('durum') == 200 and url not in [p['url'] for p in sayfalar]:
            sayfalar.append({'kurum': s['kurum'], 'tur': s['tur'], 'url': url})
    elektrik = next((s for s in d['resmi'] if s['tur'] == 'elektrik'), None)
    return {
        'il': d['il'], 'plaka': d['plaka'], 'slug': d['slug'],
        'sehirSayfasi': 'https://son-dakika-haber.com.tr/sehir/' + d['slug'],
        'ilceler': ilceler,
        'rss': rss,
        'sayfalar': sayfalar,
        'elektrikSirketi': (elektrik or {}).get('kurum', ''),
        'elektrikKesintiSayfasi': (elektrik or {}).get('duyuru_url') or (elektrik or {}).get('url', ''),
        'yerelGazeteler': [g['url'] for g in d.get('ipucu', []) if g.get('tur') == 'yerel_gazete' and g.get('durum') == 200
                           and 'haberler.com' not in g['url']],
        'degerliKonular': d.get('deger_konulari', []),
        'kaynakNotlari': d.get('notlar', '') if isinstance(d.get('notlar'), str) else ' '.join(d.get('notlar', [])),
        'enFazlaHaber': 2,
    }



# ---------------------------------------------------------------------------
# Düğüm kodları (n8n Code düğümü, "Run Once for All Items")
# ---------------------------------------------------------------------------

KOD_IL_SEC = r"""// Sırası gelen illeri seçer: en uzun süredir işlenmemiş olanlar önce.
// ilSayisi: bir çalışmada işlenecek il sayısı. enAzAralikSaat: bir il en erken kaç saat sonra tekrar işlenir.
// sadece: test için yalnızca bu plakaları işle (ör. ['43']); boşsa bütün iller sırayla.
const AYAR = { ilSayisi: 7, enAzAralikSaat: 10, sadece: [] };
const ILLER = __ILLER__;
const durum = $getWorkflowStaticData('global');
durum.sonCalisma = durum.sonCalisma || {};
const simdi = Date.now();
let aday = AYAR.sadece.length ? ILLER.filter(il => AYAR.sadece.includes(il.plaka))
  : ILLER.filter(il => simdi - (durum.sonCalisma[il.plaka] || 0) >= AYAR.enAzAralikSaat * 3600000);
aday.sort((a, b) => (durum.sonCalisma[a.plaka] || 0) - (durum.sonCalisma[b.plaka] || 0));
const secilen = aday.slice(0, AYAR.ilSayisi);
// Seçilenler hemen işaretlenir; hata veren bir il sürekli başa gelip diğerlerini bekletmesin
for (const il of secilen) durum.sonCalisma[il.plaka] = simdi;
return secilen.map(il => ({ json: il }));"""

KOD_ILLER = "// AFAD isteği öğeleri değiştirdiği için seçilen illeri döngüye yeniden verir.\nreturn $('İl Seç').all().map(i => ({ json: i.json }));"

KOD_LLM_AYAR = r"""// DİL MODELİ AYARLARI (OpenAI uyumlu herhangi bir servis olabilir)
// apiKey: buraya yazabilir ya da n8n sunucusunda EVREN_API_KEY ortam değişkeni olarak tanımlayabilirsin.
// modeller: sırayla denenir; biri hata verirse (503, 429, zaman aşımı, bozuk cevap) sonrakine geçilir.
let envKey = '';
try { envKey = $env.EVREN_API_KEY || ''; } catch (e) {}
return [{ json: {
  baseUrl: 'https://evren-llmapi.ssyz.org.tr/v1',
  apiKey: envKey || 'BURAYA_evren_llm_ANAHTARI',
  modeller: ['glm-5.3', 'deepseek-v4.1-flash', 'mimo-v2.6-pro', 'qwen3.8-flash-next'],
  maxTokens: 12000,
  zamanAsimiSn: 240,
  enFazlaHaber: 2,
} }];"""

KOD_RSS_LISTESI = r"""// İlin haber akışları: Google Haberler, kurum RSS'leri ve yerel gazetelerin olası RSS adresleri
const A = $('İl Döngüsü').first().json;
// n8n Code düğümünde URL nesnesi yok; alan adını düz metinden alır
const hostAl = (u) => ((String(u || '').match(/^https?:\/\/([^\/?#:]+)/i) || [])[1] || '').replace(/^www\./, '');
const liste = A.rss.map(r => ({ ...r, tur: r.kaynak.startsWith('Google') ? 'baslik' : 'resmi' }));
for (const g of A.yerelGazeteler) {
  const base = g.endsWith('/') ? g : g + '/';
  for (const yol of ['feed', 'rss']) liste.push({ kaynak: hostAl(g), url: base + yol, tur: 'gazete' });
}
return liste.map(j => ({ json: j }));"""

KOD_SAYFA_LISTESI = "return $('İl Döngüsü').first().json.sayfalar.map(s => ({ json: s }));"

KOD_ADAY = r"""// Yeni adayları toplar: RSS maddeleri (son 30 saat), resmî sayfalardaki yeni duyuru bağlantıları, AFAD depremleri.
// Daha önce görülenler ve sitede zaten olan konular elenir.
const A = $('İl Döngüsü').first().json;
const durum = $getWorkflowStaticData('global');
durum.gorulen = durum.gorulen || {};
const simdi = Date.now();
for (const [k, t] of Object.entries(durum.gorulen)) if (simdi - t > 14 * 86400000) delete durum.gorulen[k];

const kucuk = (s) => (s || '').toLocaleLowerCase('tr-TR');
const kelimeler = (s) => new Set(kucuk(s).replace(/[^a-zçğıöşü0-9 ]/g, ' ').split(/\s+/).filter(w => w.length >= 4));
const benzer = (a, b) => { const x = kelimeler(a), y = kelimeler(b); if (!x.size || !y.size) return 0; let o = 0; for (const w of x) if (y.has(w)) o++; return o / Math.min(x.size, y.size); };
// n8n Code düğümünde URL nesnesi yok; alan adını düz metinden alır
const hostAl = (u) => ((String(u || '').match(/^https?:\/\/([^\/?#:]+)/i) || [])[1] || '').replace(/^www\./, '');
// Göreli bağlantıyı sayfa adresine göre tam adrese çevirir (URL nesnesi olmadan)
const mutlak = (href, base) => {
  href = String(href || '').trim();
  if (/^https?:\/\//i.test(href)) return href;
  if (href.startsWith('//')) return 'https:' + href;
  if (!href || /^(mailto|tel|javascript|data):/i.test(href)) return null;
  const m = String(base).match(/^(https?:\/\/[^\/?#]+)(\/[^?#]*)?/i);
  if (!m) return null;
  if (href.startsWith('/')) return m[1] + href;
  if (href.startsWith('?')) return m[1] + (m[2] || '/') + href;
  const parcalar = ((m[2] || '/').replace(/[^\/]*$/, '') + href).split('/');
  const sonuc = [];
  for (const p of parcalar) { if (p === '..') { if (sonuc.length > 1) sonuc.pop(); } else if (p !== '.') sonuc.push(p); }
  return m[1] + sonuc.join('/');
};
const temizle = (s) => String(s || '').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'").replace(/&#(\d+);/g, (m, n) => String.fromCharCode(+n)).replace(/\s+/g, ' ').trim();

let siteHaberleri = [];
try {
  const r = $('Sitedeki Haberler').first().json;
  siteHaberleri = (JSON.parse(r.result?.content?.[0]?.text || '{}').items || []).map(n => ({ baslik: n.title, tarih: n.published_at, url: n.url }));
} catch (e) {}
const sitedeVar = (baslik) => siteHaberleri.some(h => benzer(h.baslik, baslik) >= 0.6);

// RSS: her öğenin hangi akıştan geldiği sırayla eşlenir
const rssListesi = $('RSS Listesi').all().map(i => i.json);
const rss = [];
const gorulenLink = new Set();
$('RSS Oku').all().forEach((it) => {
  const j = it.json;
  if (!j.title || !j.link || j.error) return;
  const t = Date.parse(j.isoDate || j.pubDate || '');
  if (t && simdi - t > 30 * 3600000) return;
  const anahtar = 'R:' + A.plaka + ':' + j.title.trim();
  if (durum.gorulen[anahtar] || gorulenLink.has(j.link) || sitedeVar(j.title)) return;
  gorulenLink.add(j.link);
  const kaynak = (rssListesi[it.pairedItem?.item ?? -1] || {});
  const host = hostAl(j.link);
  const metin = temizle(j['content:encoded'] || j.content || j.contentSnippet || '').slice(0, 1800);
  rss.push({ anahtar, baslik: temizle(j.title), tarih: j.isoDate || j.pubDate || '', link: j.link,
             kaynak: kaynak.tur === 'baslik' ? 'Google Haberler' : (kaynak.kaynak || host), tur: kaynak.tur || 'gazete',
             metin: metin.length > 120 && kucuk(metin) !== kucuk(j.title) ? metin : '' });
});

// Resmî duyuru listelerinden yeni bağlantılar
const sayfaListesi = $('Sayfa Listesi').all().map(i => i.json);
const menuMetni = /kişisel veri|kvkk|aydınlatma metni|çerez|gizlilik|site haritası|bilgi edinme|e-devlet|iletişim bilgileri|tüm hakları|erişilebilirlik|misyon|vizyon|organizasyon şeması|kalite politikası|tarihçe|hakkımızda/i;
const duyuruGibi = /duyuru|haber|detay|icerik|content|announce|news|ilan|kesinti|\/\d{3,}|[?&]id=/i;
const resmi = [], acilmayan = [];
$('Sayfa Çek').all().forEach((it, i) => {
  const s = sayfaListesi[it.pairedItem?.item ?? i];
  if (!s) return;
  const html = typeof it.json.data === 'string' ? it.json.data : '';
  if (!html || it.json.error) { acilmayan.push(s.kurum); return; }
  const re = /<a\b[^>]*href\s*=\s*["']([^"'#]+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  const gorulen = new Set(), bulunan = [];
  let m;
  while ((m = re.exec(html))) {
    const text = temizle(m[2]);
    if (text.length < 20 || text.length > 220 || menuMetni.test(text)) continue;
    const href = mutlak(m[1], s.url);
    if (!href || !/^https?:/.test(href) || /\.(pdf|docx?|xlsx?|jpe?g|png|zip|rar)(\?|$)/i.test(href) || gorulen.has(href)) continue;
    gorulen.add(href);
    bulunan.push({ text, href, puan: duyuruGibi.test(href) ? 1 : 0 });
  }
  bulunan.sort((a, b) => b.puan - a.puan);
  for (const b of bulunan.slice(0, 10)) {
    const anahtar = 'L:' + b.href;
    if (durum.gorulen[anahtar] || sitedeVar(b.text)) continue;
    resmi.push({ anahtar, kurum: s.kurum, baslik: b.text, link: b.href });
  }
});

const depremler = $('AFAD Depremler').all().map(i => i.json)
  .filter(d => d.magnitude && kucuk(d.province) === kucuk(A.il) && parseFloat(d.magnitude) >= 2.5)
  .map(d => ({ anahtar: 'D:' + d.eventID, yer: d.location, buyukluk: d.magnitude, derinlik: d.depth, tarih: d.date, ilce: d.district }))
  .filter(d => !durum.gorulen[d.anahtar]);

const yeniAnahtarlar = [...rss, ...resmi, ...depremler].map(x => x.anahtar);
// Detayı çekilecek resmî duyurular (en fazla 8) ve metni olan haber akışı maddeleri
const detaylar = resmi.slice(0, 8);
const metinliRss = rss.filter(r => r.metin);
const bos = !detaylar.length && !metinliRss.length && !depremler.length;
return [{ json: { bos, yeniAnahtarlar, resmi, detaylar, rss, depremler, siteHaberleri, acilmayan } }];"""

KOD_DETAY_LISTESI = r"""const d = $('Aday Hazırla').first().json.detaylar;
// Detay yoksa da döngü sürsün diye boş bir istek gönderilir (hata olarak geçer)
return (d.length ? d : [{ link: 'about:blank', bos: true }]).map(x => ({ json: x }));"""

KOD_HABER_YAZ = r"""// Toplanan bilgileri tek bir metne dönüştürür, dil modelinden JSON haber ister (model yedekli), cevabı denetler.
const A = $('İl Döngüsü').first().json;
const L = $('LLM Ayarları').first().json;
const aday = $('Aday Hazırla').first().json;
const temizle = (s) => String(s || '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'").replace(/&#(\d+);/g, (m, n) => String.fromCharCode(+n)).replace(/\s+/g, ' ').trim();
const govdeMetni = (html) => {
  let h = String(html || '').replace(/<(script|style|noscript|svg|nav|header|footer|form|aside|iframe)\b[\s\S]*?<\/\1>/gi, ' ');
  const ana = h.match(/<(article|main)\b[\s\S]*?<\/\1>/i);
  if (ana) h = ana[0];
  return temizle(h.replace(/<\/(p|div|li|h\d|tr|br)>/gi, '\n').replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, ' ')).slice(0, 3500);
};

// Kaynak numaraları: K1, K2 ... (modelin dayanak göstereceği kimlikler)
const kaynaklar = [];
const detayCevaplar = $('Detay Çek').all();
aday.detaylar.forEach((d, i) => {
  const it = detayCevaplar[i];
  const metin = it && !it.json.error && typeof it.json.data === 'string' ? govdeMetni(it.json.data) : '';
  kaynaklar.push({ id: 'K' + (kaynaklar.length + 1), tur: 'resmi', kurum: d.kurum, baslik: d.baslik, link: d.link, metin, anahtar: d.anahtar });
});
for (const r of aday.rss) {
  kaynaklar.push({ id: 'K' + (kaynaklar.length + 1), tur: r.tur === 'resmi' ? 'resmi' : (r.metin ? 'basin' : 'baslik'), kurum: r.kaynak, baslik: r.baslik, link: r.link, metin: r.metin, tarih: r.tarih, anahtar: r.anahtar });
}
for (const d of aday.depremler) {
  kaynaklar.push({ id: 'K' + (kaynaklar.length + 1), tur: 'resmi', kurum: 'AFAD', baslik: `${d.yer} merkezli ${d.buyukluk} büyüklüğünde deprem`,
    link: 'https://deprem.afad.gov.tr/last-earthquakes', metin: `AFAD verisi: ${d.tarih} (TSİ) ${d.yer}, büyüklük ${d.buyukluk}, derinlik ${d.derinlik} km.`, anahtar: d.anahtar });
}
const kullanilabilir = kaynaklar.filter(k => k.metin);
const yalnizBaslik = kaynaklar.filter(k => !k.metin).slice(0, 25);

const simdiUzun = new Intl.DateTimeFormat('tr-TR', { timeZone: 'Europe/Istanbul', dateStyle: 'full', timeStyle: 'short' }).format(new Date());
const system = `Sen son-dakika-haber.com.tr için ${A.il} yerel haberleri yazan bir editörsün. Yalnızca kullanıcının verdiği kaynak metinleri kullanırsın; web'e erişimin yoktur, başka bilgi ekleyemezsin. Cevabın YALNIZCA geçerli bir JSON nesnesidir; açıklama, giriş cümlesi veya plan yazma.

KURALLAR
- Okur için değerli olan en fazla ${L.enFazlaHaber} haber seç: okul tatili, su/elektrik/doğalgaz kesintisi, yol kapanması ve ulaşım, hava uyarısı, deprem, can kaybı olan kaza/afet (resmî açıklamayla), valilik yasak ve kararları, belediye fiyat/tarife kararları, sağlık ve eğitim hizmetinde değişiklik, ilde önemli olaylar.
- YAZMA: ziyaret, protokol, tören, ödül, kurs/etkinlik duyurusu, ihale ilanı, personel/atama listesi, kutlama mesajı, "çalışmalar sürüyor" türü bültenler, siyasi polemik, magazin. Değerli bir şey yoksa "haberler": [] döndür.
- Dayanak: Her haber şu kaynaklardan birine dayanmalı: (a) resmî kurum metni, (b) AFAD verisi, (c) aynı olayı anlatan en az 2 farklı basın kaynağının metni. Yalnızca başlığı verilen maddeler tek başına dayanak olamaz.
- Sitede zaten olan konuları yazma (listesi aşağıda).
- Kaynak metinde olmayan hiçbir bilgiyi (sayı, isim, tarih, saat, mahalle) ekleme. Tahmin ve yorum yok. Kaza/suç haberlerinde kurban ve şüpheli ismi yazma.
- Tamamen kendi cümlelerinle yaz; kaynaktan cümle kopyalama. Bilgiyi asıl sahibine atfet ("${A.il} Valiliğinin duyurusuna göre"). "Basına yansıyan bilgilere göre" deme. Haber sitelerinin adını yazma.
- Başlık en fazla 70 karakter, olgusal, ünlemsiz; il veya ilçe adı başlıkta geçsin (Türkçe ek uyumuna dikkat). Spot 1-2 cümle.
- İçerik HTML: 250-450 kelime; yalnızca <p>, <h2>, <ul>, <li>, <strong>. İlk paragrafta ne, nerede, ne zaman. 1-2 <h2> ara başlık. Kesinti/kapanma/tatil haberlerinde etkilenen mahalle, güzergâh, okul ve saatleri <ul> ile listele. Tarihleri açık yaz; olay bugün değilse "bugün" deme. Bağlantı ekleme (sistem ekler).
- meta_title en fazla 60, meta_description 120-160 karakter.
- kategori: gundem, ekonomi, egitim, saglik, spor değerlerinden biri.
- etiketler: 3-5 adet; ilk etiket "${A.il}", varsa ilçe adı ve genel bir konu etiketi ("su kesintisi", "elektrik kesintisi", "okul tatili", "deprem", "trafik kazası" gibi).
- son_dakika: yalnızca son 3 saatte olan 4.0+ deprem, can kaybı olan olay/afet veya okul tatili kararı ise true.

JSON BİÇİMİ
{"haberler":[{"dayanak":["K1"],"baslik":"","spot":"","icerik_html":"","kategori":"gundem","ilce":"","etiketler":[],"meta_title":"","meta_description":"","kaynak_kurum":"","son_dakika":false}],"atlananlar":[{"kaynak":"K2","neden":""}]}`;

const satir = [`Şu an: ${simdiUzun}. İl: ${A.il}. İlçeler: ${A.ilceler.join(', ')}.`];
satir.push(`\n# KAYNAK METİNLER`);
for (const k of kullanilabilir) satir.push(`\n[${k.id}] (${k.tur === 'resmi' ? 'RESMÎ' : 'BASIN'} – ${k.kurum}${k.tarih ? ', ' + k.tarih : ''}) ${k.baslik}\n${k.metin}`);
if (yalnizBaslik.length) { satir.push(`\n# YALNIZCA BAŞLIK (tek başına dayanak olamaz)`); for (const k of yalnizBaslik) satir.push(`[${k.id}] ${k.baslik} (${k.kurum})`); }
satir.push(`\n# SİTEDE SON 3 GÜNDE ÇIKMIŞ ${A.il.toLocaleUpperCase('tr-TR')} HABERLERİ (tekrar yazma)`);
satir.push(aday.siteHaberleri.length ? aday.siteHaberleri.map(h => `- ${h.baslik}`).join('\n') : '- (yok)');
satir.push(`\nDeğerli konular: ${A.degerliKonular.join('; ')}.`);
satir.push(`\nŞimdi yalnızca JSON döndür.`);
const prompt = satir.join('\n');

// --- Model çağrısı (sıralı yedek) ---
const jsonCoz = (t) => {
  let s = String(t || '').replace(/<think>[\s\S]*?<\/think>/g, '').replace(/```(?:json)?/gi, '').trim();
  const a = s.indexOf('{'), b = s.lastIndexOf('}');
  if (a < 0 || b <= a) throw new Error('JSON bulunamadı');
  const j = JSON.parse(s.slice(a, b + 1));
  if (!Array.isArray(j.haberler)) throw new Error('haberler alanı yok');
  return j;
};
const denemeler = [];
let sonuc = null, kullanilanModel = null, yetkiHatasi = false;
const anahtar = String(L.apiKey || '').trim();
if (!/^evren_llm_|^sk-/.test(anahtar)) denemeler.push('UYARI: apiKey beklenen biçimde değil (evren_llm_... ile başlamalı)');
for (const model of L.modeller) {
  for (const jsonModu of [true, false]) {
    try {
      const body = { model, max_tokens: L.maxTokens, temperature: 0.3, thinking: false,
        messages: [{ role: 'system', content: system }, { role: 'user', content: prompt }] };
      if (jsonModu) body.response_format = { type: 'json_object' };
      const r = await this.helpers.httpRequest({ method: 'POST', url: L.baseUrl.replace(/\/$/, '') + '/chat/completions',
        headers: { Authorization: 'Bearer ' + anahtar, 'X-API-Key': anahtar, 'Content-Type': 'application/json' }, body, json: true, timeout: L.zamanAsimiSn * 1000 });
      const metin = r?.choices?.[0]?.message?.content;
      sonuc = jsonCoz(metin);
      kullanilanModel = model;
      break;
    } catch (e) {
      const kod = e.httpCode || e.response?.status || e.statusCode || e.cause?.response?.status || (String(e.message).match(/status code (\d{3})/) || [])[1] || '';
      // Servisin döndürdüğü hata gövdesi (ör. {"error":{"code":"invalid_api_key"}}) teşhis için rapora yazılır
      let govde = e.response?.data ?? e.cause?.response?.data ?? e.response?.body ?? e.cause?.response?.body ?? e.description ?? '';
      if (typeof govde !== 'string') { try { govde = JSON.stringify(govde); } catch (x) { govde = String(govde); } }
      const mesaj = (String(e.message || e) + (govde ? ' | ' + govde : '')).slice(0, 400);
      denemeler.push(`${model}${jsonModu ? '' : ' (json modu kapalı)'}: ${kod} ${mesaj}`);
      if (String(kod) === '401' || String(kod) === '403') { yetkiHatasi = true; break; }
      // 400 ve JSON hatalarında aynı modeli json modu kapalı dene; diğer hatalarda doğrudan sonraki modele geç
      if (!(jsonModu && (String(kod) === '400' || /JSON|haberler/.test(mesaj)))) break;
    }
  }
  if (sonuc || yetkiHatasi) break;
}
if (!sonuc) return [{ json: { yayin: false, denemeler, rapor: yetkiHatasi
  ? 'API anahtarı reddedildi (401/403). LLM Ayarları\'ndaki apiKey\'i kontrol et; 403 terms_not_accepted ise EVREN kullanım şartlarını onayla.'
  : 'Hiçbir model cevap veremedi.' } }];

// --- Denetim: dayanak kaynaklarından adres/kimlik al, uydurma bağlantıları temizle ---
const izinli = ['gundem', 'ekonomi', 'egitim', 'saglik', 'spor'];
const haberler = [];
for (const h of (sonuc.haberler || []).slice(0, L.enFazlaHaber)) {
  const dayanak = (h.dayanak || []).map(id => kaynaklar.find(k => k.id === id)).filter(Boolean);
  const metinli = dayanak.filter(k => k.metin);
  const resmiDayanak = metinli.find(k => k.tur === 'resmi');
  if (!resmiDayanak && metinli.length < 2) { denemeler.push(`Elendi (dayanak yetersiz): ${h.baslik}`); continue; }
  if (!h.baslik || !h.icerik_html) continue;
  let icerik = String(h.icerik_html).replace(/<(script|style|iframe)\b[\s\S]*?<\/\1>/gi, '').replace(/<a\b[^>]*>([\s\S]*?)<\/a>/gi, '$1').replace(/<(?!\/?(p|h2|h3|ul|ol|li|strong)\b)[^>]+>/gi, '');
  icerik += `\n<p>${A.il} ile ilgili diğer haberler için <a href="${A.sehirSayfasi}">${A.il} haberleri</a> sayfamızı takip edebilirsiniz.</p>`;
  const anaKaynak = resmiDayanak || metinli[0];
  haberler.push({
    title: String(h.baslik).slice(0, 120), spot: String(h.spot || '').slice(0, 400), content: icerik,
    category: izinli.includes(h.kategori) ? h.kategori : 'gundem', province: A.il,
    tags: [...new Set([A.il, ...(h.etiketler || [])].map(t => String(t).trim()).filter(Boolean))].slice(0, 6),
    meta_title: String(h.meta_title || '').slice(0, 70), meta_description: String(h.meta_description || '').slice(0, 170),
    source_name: String(h.kaynak_kurum || anaKaynak.kurum || '').slice(0, 150),
    source_url: resmiDayanak && /^https?:/.test(resmiDayanak.link) && !/news\.google/.test(resmiDayanak.link) ? resmiDayanak.link : undefined,
    source_guid: String(anaKaynak.link).slice(0, 191),
    is_breaking: !!h.son_dakika, is_headline: false, is_featured: false,
    author_id: null, status: 'active', is_ai_assisted: true,
  });
}
const ozet = { model: kullanilanModel, denemeler, atlananlar: sonuc.atlananlar || [], kaynakSayisi: kullanilabilir.length };
if (!haberler.length) return [{ json: { yayin: false, rapor: 'Yayımlanacak değerli haber yok.', ...ozet } }];
return haberler.map(h => ({ json: { yayin: true, haber: h, ...ozet } }));"""

KOD_RAPOR_YAYIN = r"""// Yayın sonuçları + bu çalışmada görülen adaylar "görüldü" olarak işaretlenir.
const durum = $getWorkflowStaticData('global');
durum.gorulen = durum.gorulen || {};
for (const k of $('Aday Hazırla').first().json.yeniAnahtarlar || []) durum.gorulen[k] = Date.now();
const yazilan = $('Haber Yaz').all().map(i => i.json);
const sonuclar = $input.all().map((it, i) => {
  let r = {};
  try { r = JSON.parse(it.json.result?.content?.[0]?.text || '{}'); } catch (e) {}
  const hata = it.json.result?.isError ? it.json.result?.content?.[0]?.text : (it.json.error?.message || it.json.error);
  return { baslik: yazilan[i]?.haber?.title, url: r.url || null, hata: hata || null, uyarilar: r.warnings || [] };
});
return [{ json: { il: $('İl Döngüsü').first().json.il, model: yazilan[0]?.model, yayimlanan: sonuclar, denemeler: yazilan[0]?.denemeler } }];"""

KOD_RAPOR_YOK = r"""// Model çalıştı ama yayımlanacak haber çıkmadı (ya da hiçbir model cevap vermedi)
const durum = $getWorkflowStaticData('global');
durum.gorulen = durum.gorulen || {};
const j = $input.first().json;
// Hiçbir model cevap veremediyse adaylar işaretlenmez; bir sonraki çalışmada yeniden denenir
if (j.model) for (const k of $('Aday Hazırla').first().json.yeniAnahtarlar || []) durum.gorulen[k] = Date.now();
return [{ json: { il: $('İl Döngüsü').first().json.il, model: j.model || null, rapor: j.rapor, atlananlar: j.atlananlar, denemeler: j.denemeler } }];"""

KOD_ADAY_YOK = r"""const a = $input.first().json;
return [{ json: { il: $('İl Döngüsü').first().json.il, rapor: 'Yeni aday yok; model çağrılmadı.', acilmayan: a.acilmayan } }];"""

KOD_OZET = r"""// Bu çalışmada işlenen illerin raporları
return [{ json: { tarih: new Date().toISOString(), iller: $input.all().map(i => i.json) } }];"""


def code(name, js, pos, nid):
    return {"parameters": {"jsCode": js}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos, "id": nid, "name": name}


def build_tek():
    iller = [il_ayarlari(json.load(open(f, encoding='utf-8')))
             for f in sorted(glob.glob(os.path.join(ROOT, 'il-kaynaklari', '[0-9]*.json')))]
    n = lambda i: f"d0000000-0000-4000-8000-0000000000{i:02d}"
    tolerant = {"onError": "continueRegularOutput", "alwaysOutputData": True}
    sayfa_opts = {"allowUnauthorizedCerts": True, "timeout": 20000, "response": {"response": {"responseFormat": "text"}},
                  "batching": {"batch": {"batchSize": 3, "batchInterval": 500}}}
    ua = {"parameters": [{"name": "User-Agent", "value": "Mozilla/5.0 (compatible; SonDakikaHaberBot/1.0; +https://son-dakika-haber.com.tr)"}]}
    mcp_body = lambda expr: "={{ JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: " + expr + " }) }}"
    mcp_http = lambda name, pos, nid, expr, extra: dict({
        "parameters": {"method": "POST", "url": "https://son-dakika-haber.com.tr/mcp",
                       "authentication": "genericCredentialType", "genericAuthType": "httpBearerAuth",
                       "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Accept", "value": "application/json, text/event-stream"}]},
                       "sendBody": True, "specifyBody": "json", "jsonBody": mcp_body(expr), "options": {"timeout": 60000}},
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": pos, "id": nid, "name": name, "credentials": MCP_CRED}, **extra)

    nodes = [
        {"parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "5 6-22 * * *"}]}},
         "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": [0, 0], "id": n(1), "name": "Zamanlayıcı"},
        code("LLM Ayarları", KOD_LLM_AYAR, [200, 0], n(2)),
        code("İl Seç", KOD_IL_SEC.replace('__ILLER__', json.dumps(iller, ensure_ascii=False)), [400, 0], n(3)),
        dict({"parameters": {"url": "https://servisnet.afad.gov.tr/apigateway/deprem/apiv2/event/filter", "sendQuery": True,
                             "queryParameters": {"parameters": [
                                 {"name": "start", "value": "={{ $now.setZone('Europe/Istanbul').minus({hours: 24}).toFormat(\"yyyy-MM-dd'T'HH:mm:ss\") }}"},
                                 {"name": "end", "value": "={{ $now.setZone('Europe/Istanbul').toFormat(\"yyyy-MM-dd'T'HH:mm:ss\") }}"},
                                 {"name": "minmag", "value": "2.5"}]},
                             "options": {"timeout": 20000}},
              "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [600, 0], "id": n(4), "name": "AFAD Depremler", "executeOnce": True}, **tolerant),
        code("İller", KOD_ILLER, [800, 0], n(5)),
        {"parameters": {"options": {}}, "type": "n8n-nodes-base.splitInBatches", "typeVersion": 3, "position": [1000, 0], "id": n(6), "name": "İl Döngüsü"},
        code("Özet", KOD_OZET, [1220, -240], n(7)),
        # --- il gövdesi ---
        code("RSS Listesi", KOD_RSS_LISTESI, [1220, 160], n(8)),
        dict({"parameters": {"url": "={{ $json.url }}", "options": {"ignoreSSL": True}},
              "type": "n8n-nodes-base.rssFeedRead", "typeVersion": 1.1, "position": [1420, 160], "id": n(9), "name": "RSS Oku"}, **tolerant),
        code("Sayfa Listesi", KOD_SAYFA_LISTESI, [1620, 160], n(10)),
        dict({"parameters": {"url": "={{ $json.url }}", "sendHeaders": True, "headerParameters": ua, "options": sayfa_opts},
              "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1820, 160], "id": n(11), "name": "Sayfa Çek"}, **tolerant),
        mcp_http("Sitedeki Haberler", [2020, 160], n(12),
                 "{ name: 'news_list', arguments: { province: $('İl Döngüsü').first().json.il, date_from: $now.setZone('Europe/Istanbul').minus({days: 3}).toFormat('yyyy-MM-dd'), status: 'public', per_page: 50 } }",
                 dict({"executeOnce": True}, **tolerant)),
        code("Aday Hazırla", KOD_ADAY, [2220, 160], n(13)),
        {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"}, "combinator": "and",
                                       "conditions": [{"id": "c1", "leftValue": "={{ $json.bos }}", "rightValue": False, "operator": {"type": "boolean", "operation": "equals"}}]}, "options": {}},
         "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [2420, 160], "id": n(14), "name": "Yeni Aday Var mı?"},
        code("Detay Listesi", KOD_DETAY_LISTESI, [2620, 60], n(15)),
        dict({"parameters": {"url": "={{ $json.link }}", "sendHeaders": True, "headerParameters": ua, "options": sayfa_opts},
              "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [2820, 60], "id": n(16), "name": "Detay Çek"}, **tolerant),
        code("Haber Yaz", KOD_HABER_YAZ, [3020, 60], n(17)),
        {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"}, "combinator": "and",
                                       "conditions": [{"id": "c2", "leftValue": "={{ $json.yayin }}", "rightValue": True, "operator": {"type": "boolean", "operation": "equals"}}]}, "options": {}},
         "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [3220, 60], "id": n(18), "name": "Haber Var mı?"},
        mcp_http("Yayımla", [3420, -40], n(19), "{ name: 'news_create', arguments: $json.haber }", tolerant),
        code("Rapor", KOD_RAPOR_YAYIN, [3620, -40], n(20)),
        code("Rapor (haber yok)", KOD_RAPOR_YOK, [3420, 160], n(21)),
        code("Aday Yok", KOD_ADAY_YOK, [2620, 300], n(22)),
        {"parameters": {"content":
            "## 81 il – yerel haber\n"
            "Her saat (06:05–22:05) sırası gelen illeri işler (*İl Seç* → AYAR: ilSayisi, enAzAralikSaat, sadece).\n\n"
            "**Akış (il başına):** RSS (Google Haberler, kurum RSS'leri, yerel gazete RSS'leri) + resmî duyuru sayfaları → yeni adaylar → "
            "resmî duyuruların detay sayfaları çekilir → **Haber Yaz**: dil modeli tek çağrıda yalnızca verilen metinlerden JSON haber yazar "
            "(araç kullanmaz) → **Yayımla**: MCP news_create.\n\n"
            "**Model yedeği:** *LLM Ayarları* → modeller listesi sırayla denenir; 503/429/zaman aşımı/bozuk cevapta sonrakine geçilir.\n\n"
            "**Kurulum:** 1) *LLM Ayarları*'na API anahtarı (veya sunucuda EVREN_API_KEY). 2) *Sitedeki Haberler* ve *Yayımla*'da MCP Bearer credential. "
            "3) Test için İl Seç'te `sadece: ['43']`, sonra boşalt ve Active yap.\n"
            "Sıra ve 'görülenler' hafızası yalnızca Active çalışmalarda kalıcıdır.", "height": 460, "width": 560},
         "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [0, -520], "id": n(23), "name": "Not"},
    ]
    m = lambda a, i=0: {"node": a, "type": "main", "index": i}
    conn = {
        "Zamanlayıcı": {"main": [[m("LLM Ayarları")]]},
        "LLM Ayarları": {"main": [[m("İl Seç")]]},
        "İl Seç": {"main": [[m("AFAD Depremler")]]},
        "AFAD Depremler": {"main": [[m("İller")]]},
        "İller": {"main": [[m("İl Döngüsü")]]},
        "İl Döngüsü": {"main": [[m("Özet")], [m("RSS Listesi")]]},
        "RSS Listesi": {"main": [[m("RSS Oku")]]},
        "RSS Oku": {"main": [[m("Sayfa Listesi")]]},
        "Sayfa Listesi": {"main": [[m("Sayfa Çek")]]},
        "Sayfa Çek": {"main": [[m("Sitedeki Haberler")]]},
        "Sitedeki Haberler": {"main": [[m("Aday Hazırla")]]},
        "Aday Hazırla": {"main": [[m("Yeni Aday Var mı?")]]},
        "Yeni Aday Var mı?": {"main": [[m("Detay Listesi")], [m("Aday Yok")]]},
        "Detay Listesi": {"main": [[m("Detay Çek")]]},
        "Detay Çek": {"main": [[m("Haber Yaz")]]},
        "Haber Yaz": {"main": [[m("Haber Var mı?")]]},
        "Haber Var mı?": {"main": [[m("Yayımla")], [m("Rapor (haber yok)")]]},
        "Yayımla": {"main": [[m("Rapor")]]},
        "Rapor": {"main": [[m("İl Döngüsü")]]},
        "Rapor (haber yok)": {"main": [[m("İl Döngüsü")]]},
        "Aday Yok": {"main": [[m("İl Döngüsü")]]},
    }
    return {"name": "Son Dakika Haber – 81 İl Yerel Haber", "nodes": nodes, "connections": conn, "pinData": {},
            "settings": {"executionOrder": "v1", "timezone": "Europe/Istanbul", "saveDataSuccessExecution": "all"}}


if __name__ == '__main__':
    out = os.path.join(ROOT, 'n8n', 'workflows'); os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'tum-iller.json')
    json.dump(build_tek(), open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(p, os.path.getsize(p) // 1024, 'KB')
