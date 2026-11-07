"""Turkish provinces for eleman_net_mcp.

PROVINCES: the 81 provinces of Türkiye with the slug eleman.net
uses for city listing pages (/is-ilanlari/<slug>). Slugs follow the
site's deterministic pattern (Turkish-aware lowercase, ASCII fold,
spaces -> hyphens); the pattern is verified live for İstanbul,
Ankara, İzmir, Bursa, Antalya, Şanlıurfa and Diyarbakır. The two
İstanbul sides are extra entries — the site lists them separately.
"""
from __future__ import annotations

PROVINCES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray",
    "Amasya", "Ankara", "Antalya", "Ardahan", "Artvin", "Aydın",
    "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik",
    "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale",
    "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce",
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir",
    "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay",
    "Iğdır", "Isparta", "İstanbul", "İzmir", "Kahramanmaraş",
    "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri",
    "Kırıkkale", "Kırklareli", "Kırşehir", "Kilis", "Kocaeli",
    "Konya", "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin",
    "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye",
    "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas",
    "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon",
    "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak",
]

# Extra site entries (not provinces): the two İstanbul sides.
ISTANBUL_SIDES = ["İstanbul Anadolu", "İstanbul Avrupa"]
