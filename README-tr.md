# eleman-net-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/eleman-net-mcp

eleman.net için resmi olmayan **salt okunur** MCP sunucusu — Türkiye'nin mavi yaka iş ilanı sitesi (Türkiye'de iş kategorisinde 2. sırada, SimilarWeb'e göre ayda ~4,4–5,1 milyon ziyaret): pozisyona veya şehre göre iş arama, iş detaylarını okuma, 93 sektörün ve 81 ilin tamamını listeleme ve en yeni ilanları getirme.

> Mohammad Abbasi tarafından "Turkey MCP factory" (Sepehr tarzı hat) kapsamında geliştirildi. eleman.net ile bağlantısı yoktur.

## Yapay zekâ ajanları için

MCP istemci yapılandırmanıza ekleyin (stdio):

```json
{
  "mcpServers": {
    "eleman-net": {
      "command": "uvx",
      "args": ["eleman-net-mcp==0.1.1"]
    }
  }
}
```

Veya yerel çalıştırın: `python -m eleman_net_mcp.server` (`mcp<2`, `curl-cffi` gerekir).

## Araçlar

| Araç | Açıklama |
|------|----------|
| `eleman_search_jobs` | İş arama — `keyword` (pozisyon, örn. "garson", "şoför", "muhasebe"), `city` (örn. "İstanbul", "Ankara"), `page` 1.., `limit` 1..30; işler (id, başlık, firma, konum, özet, URL) + sayfalama (2026-11-07'de 197 sayfa) |
| `eleman_get_job` | Tek bir işin tüm detayı — `job_url` (arama sonucundaki `…/is-ilani/<slug>-i<id>` URL'si); başlık, yayın tarihi, çalışma şekli, tam açıklama, firma (+ URL), konum, bölge, eğitim şartları |
| `eleman_list_sectors` | eleman.net'teki 93 sektörün tamamı (ad + sektör id), sitenin kendi listeleme kenar çubuğundan |
| `eleman_list_cities` | 81 ilin tamamı (+ İstanbul'un iki yakası) ve her biri için eleman.net listeleme URL'si |
| `eleman_new_listings` | En yeni ilanlar (ilk sayfa, en yeniden), `limit` 1..30 |

Örnek çıktı (`eleman_search_jobs` / "garson"):

```json
{"keyword": "garson", "count": 2, "jobs": [
  {"title": "Garson", "company": "TAVUK DÜNYASI",
   "location": "İstanbul Anadolu - Ataşehir",
   "url": "https://www.eleman.net/is-ilani/…"}, …]}
```

## Nasıl çalışıyor?

eleman.net ilanları tamamen sunucu taraflı render ediyor — giriş, API anahtarı ve oturum çerezi gerekmiyor. Listeleme sayfalarında sayfa başına 30 iş kartı var (`ilan_id_<id>` blokları: başlık, firma, "Şehir - İlçe", özet; acil işlerde başlık bloğunda "ACİL İLAN" rozeti, bazı kartlarda açıklama öncesinde yan hak rozeti bulunur — ayrıştırıcı ikisini de işler). Pozisyon ve şehir sayfaları tek bir slug alanını paylaşır (`/is-ilanlari/<slug>`: garson, istanbul, ankara …); şehir + anahtar kelime, şehir slug'ını `?aranan=<keyword>&arandi=e` ile birleştirir. İş detay sayfalarında schema.org JobPosting JSON-LD bloğu bulunur (başlık, datePosted, açıklama, employmentType, konum, firma). Yalın sayısal id geçerli bir detay URL'si değildir — arama sonucundaki tam iş URL'sini verin (bilinmeyen slug'lar ana sayfaya 301 yönlenir, ayrıştırıcı bunu reddeder). Aktarım Chrome TLS kimliğine bürünme kullanır (`curl-cffi`, `chrome120`); istekler ~0,8 sn arayla yapılır; her şey salt okunurdur.

Not: Sitenin kendi `/ara` araması ve forum araması token gerektirir; anahtar kelime araması bu nedenle yukarıdaki, canlı doğrulanan slug/parametre yollarını kullanır. Otomatik tamamlama uç noktası (`/arama_complete.php`) robots.txt'de yasaklıdır ve kullanılmaz.

## Kurulum

```bash
uvx eleman-net-mcp==0.1.1        # doğrudan çalıştır (uv gerekir)
# veya
pip install eleman-net-mcp==0.1.1
eleman-net-mcp    # MCP sunucusunu stdio üzerinde başlatır
```

## Testler

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Çevrimdışı testler kayıtlı örnek sayfalarla çalışır (2026-11-07'de çekilen gerçek sayfalar); canlı testler eleman.net'e bağlanır. Derleme anında 28/28 yeşil (15 çevrimdışı + 13 canlı) ve bir MCP stdio duman testi.

## Yol haritası

- Sektöre göre filtreli arama (`?sek[]=<id>` filtresi)
- Firma sayfaları (`/firma/<slug>`: firmanın işleri + profili)
- Sitenin yayınladığı yerlerde maaş bilgisi (JobPosting verisinde nadir)

## Lisans

MIT — bkz. [LICENSE](LICENSE).
