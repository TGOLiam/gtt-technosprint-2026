import csv
import re
from pathlib import Path

import requests

OUTPUT = Path("data/prompts.csv")


DIAGNOSTIC_PAIRS = [
    ("Banggi na, magturug na kita.", "naga"),
    ("Gab-i na, magturug na kita.", "albay"),
    ("Mayo nin tawo sa harong.", "naga"),
    ("Warâ nin tawo sa balay.", "albay"),
    ("Magkakan kita nin pamahaw.", "naga"),
    ("Magkaon kita nin pamahaw.", "albay"),
    ("An damulag nag-aarado sa uma.", "naga"),
    ("An karabaw nag-aarado sa uma.", "albay"),
    ("Harong mi ini sa Naga.", "naga"),
    ("Balay mi ini sa Legazpi.", "albay"),
    ("Maugma akong magin Bikolano.", "naga"),
    ("Maugma akong magin Bikolano.", "albay"),
    ("Dai ko aram kun sain siya nagduman.", "naga"),
    ("Dai ko aram kun hain siya nagduman.", "albay"),
    ("Mabakal ako nin sira sa saod.", "naga"),
    ("Mabakal ako nin sira sa sadan.", "albay"),
    ("Nag-istar ako sa may simbahan.", "naga"),
    ("Nag-istar ako sa may simbahan.", "albay"),
    ("Magayon an panahon ngunyan.", "naga"),
    ("Magayon an panahon ngunyan.", "albay"),
]

GENERAL = [
    "Salamat sa saimong tabang.",
    "Pwede tabi akong maghapot?",
    "Hain an pinakaharaning ospital?",
    "Gurano ini kamahal?",
    "Paki-ulay tabi nin luway-luway.",
    "An buhay sa probinsya mas simple.",
    "Dakulang problema ini sa komunidad.",
    "An satuyang lengguwahe importante sa kultura.",
    "Dai dapat kalimutan an satuyang ginikanan.",
    "An mga aki dapat makanuod nin Bikol.",
    "Pirmi kong nadadangog an kantang ini.",
    "An satuyang mga ginikanan mayaman sa istorya.",
    "Pwede kitang maghirilingan sa maabot na aldaw.",
    "Dakula an pasasalamat ko saindo gabos.",
    "Pirmi akong nag-eerok digdi sa probinsya.",
    "Kaipuhan ta magtarabangan bilang sarong komunidad.",
    "An edukasyon importante sa lambang aki.",
    "Dai paglingawan an satuyang tradisyon.",
    "Magayon an satuyang lugar pag tig-init.",
    "Ini an samuyang istaran puon pa kan aki ako.",
]

BIBLE = [
    "Ta namumutan nin Diyos an kinaban.",
    "Kaya itinao Niya an Saiyang bugtong na Aki.",
    "Tanganing an siisay man na nagtutubod sa Saiya dai mapahamak.",
    "Kundi magkaigwa nin buhay na daing kasagkoran.",
    "Ako an dalan asin an katotoohan saka an buhay.",
    "An kapinunan kan tataramon iyo an Diyos.",
    "Asin an tataramon kaibahan kan Diyos.",
]


def scrape_wikipedia(lang, page_count=30):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    sentences = []
    en_words = {"the", "and", "of", "in", "to", "a", "is", "for", "on", "with", "by", "at", "an", "it", "or", "as", "be", "was", "are", "has", "had", "this", "that", "from", "but", "not", "we", "they", "he", "she", "his", "her", "its", "their", "been", "were", "can", "will", "would", "could", "should", "may", "also"}

    try:
        r = requests.get(url, params={
            "action": "query", "format": "json",
            "list": "random", "rnnamespace": 0, "rnlimit": page_count,
        }, headers={"User-Agent": "BikolScraper/1.0"}, timeout=20)
        data = r.json()
        page_ids = [p["id"] for p in data.get("query", {}).get("random", [])]

        r2 = requests.get(url, params={
            "action": "query", "format": "json",
            "pageids": "|".join(str(p) for p in page_ids),
            "prop": "extracts", "exintro": True, "explaintext": True,
        }, headers={"User-Agent": "BikolScraper/1.0"}, timeout=20)
        data2 = r2.json()

        for page in data2.get("query", {}).get("pages", {}).values():
            text = page.get("extract", "")
            for sent in re.split(r"(?<=[.?!])\s+", text):
                sent = re.sub(r"\s+", " ", sent).strip()
                words = sent.split()
                if 3 <= len(words) <= 15 and len(sent) < 200:
                    en_count = sum(1 for w in words if w.lower().rstrip(".,;:") in en_words)
                    if en_count / len(words) < 0.2:
                        sentences.append(sent)
        return sentences
    except Exception:
        return []


def main():
    prompts = []
    seen = set()

    for text, dialect in DIAGNOSTIC_PAIRS:
        key = text.lower().strip()
        if key not in seen:
            seen.add(key)
            prompts.append({"text": text, "dialect": dialect, "category": "diagnostic", "source": "manual"})

    for text in GENERAL:
        key = text.lower().strip()
        if key not in seen:
            seen.add(key)
            prompts.append({"text": text, "dialect": "", "category": "general", "source": "manual"})

    for text in BIBLE:
        key = text.lower().strip()
        if key not in seen:
            seen.add(key)
            prompts.append({"text": text, "dialect": "", "category": "bible", "source": "bcl_bible"})

    wiki = scrape_wikipedia("bcl", 40)
    for sent in wiki:
        key = sent.lower().strip()
        if key not in seen:
            seen.add(key)
            prompts.append({"text": sent, "dialect": "", "category": "general", "source": "bcl_wikipedia"})

    prompts = list({p["text"].lower().strip(): p for p in prompts}.values())

    naga = sum(1 for p in prompts if p["dialect"] == "naga")
    albay = sum(1 for p in prompts if p["dialect"] == "albay")
    gen = sum(1 for p in prompts if not p["dialect"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "text", "dialect_variant", "category", "source"])
        w.writeheader()
        for i, p in enumerate(prompts):
            w.writerow({"id": f"p{i:04d}", "text": p["text"], "dialect_variant": p["dialect"],
                        "category": p["category"], "source": p["source"]})

    print(f"Wrote {len(prompts)} prompts to {OUTPUT}  (naga={naga} albay={albay} general={gen})")


if __name__ == "__main__":
    main()
