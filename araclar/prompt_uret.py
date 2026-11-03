#!/usr/bin/env python3
"""il-kaynaklari/*.json dosyalarından il-promptlari/*.md ve README.md tablosunu üretir.
Kullanım (repo kökünden): python3 araclar/prompt_uret.py"""
import json, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def schedule(plaka):
    """Sabah/akşam birer çalışma; iller 20 zaman dilimine yayılır (ilk 5 ilin saatleri bu formülle oluşturuldu, değiştirmeyin)"""
    n = int(plaka) - 1
    minute = 5 + (n % 5) * 11            # 05, 16, 27, 38, 49
    morning = 7 + (n // 5) % 4           # 07-10
    evening = 16 + (n // 5) % 4          # 16-19
    return f'{minute} {morning},{evening} * * *', f'{morning:02d}:{minute:02d} ve {evening:02d}:{minute:02d}'


rows = []
for f in sorted(glob.glob(os.path.join(ROOT, 'il-kaynaklari', '[0-9]*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    cron, saat = schedule(d['plaka'])
    name = f"{d['plaka']}-{d['slug']}"
    prompt = (f"Sen son-dakika-haber.com.tr'nin {d['il']} muhabirisin.\n"
              f"Bu repodaki KURALLAR.md dosyasını baştan sona oku ve harfiyen uygula.\n"
              f"İl: {d['il']} (plaka {d['plaka']}, slug: {d['slug']})\n"
              f"İl kaynak dosyası: il-kaynaklari/{name}.json\n"
              f"Raporunu Türkçe yaz.")
    open(os.path.join(ROOT, 'il-promptlari', name + '.md'), 'w', encoding='utf-8').write(
        f"# {d['plaka']} {d['il']}\n\n"
        f"- Routine adı: Son Dakika Haber – {d['il']}\n"
        f"- Zamanlama: her gün {saat} (Europe/Istanbul), cron `{cron}`\n"
        f"- Repo: bu repo; bağlayıcı: son-dakika-haber MCP; web araması ve sayfa okuma açık\n\n"
        f"```\n{prompt}\n```\n")
    rows.append(f"| {d['plaka']} | {d['il']} | {saat} | il-promptlari/{name}.md |")

open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8').write(
    "# son-dakika-haber yerel kaynaklar\n\n"
    "Yerel haber routine'lerinin okuduğu dosyalar. **Bu repo gizli (private) olmalı ve sitenin kodunu içermemeli.**\n\n"
    "- `KURALLAR.md`: bütün il routine'lerinin ortak kuralları (değişince tüm routine'ler bir sonraki çalışmada yeni hali kullanır)\n"
    "- `il-kaynaklari/`: her ilin resmî kaynakları (şema: `il-kaynaklari/SEMA.md`)\n"
    "- `il-promptlari/`: her il routine'inin kısa promptu ve zamanlaması\n"
    "- `araclar/prompt_uret.py`: kaynak dosyalarından promptları ve bu tabloyu yeniden üretir\n\n"
    f"Toplam {len(rows)} il.\n\n"
    "| Plaka | İl | Saat | Prompt |\n|---|---|---|---|\n" + "\n".join(rows) + "\n")
print(f"{len(rows)} il için prompt üretildi")
