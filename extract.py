import requests
from bs4 import BeautifulSoup
import json
import time
from tqdm import tqdm

BASE_URL = "https://www.wisdomlib.org/hinduism/book/chandogya-upanishad-english/d/"
START_URL = BASE_URL + "doc238710.html"

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------
# Fetch page
# -----------------------------
def fetch(url):
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return None
    return BeautifulSoup(res.text, "html.parser")


# -----------------------------
# Extract verse data
# -----------------------------
def parse_page(soup):
    data = {}

    text = soup.get_text("\n")

    # -----------------------------
    # Verse ID
    # -----------------------------
    import re
    match = re.search(r"Verse\s+(\d+\.\d+\.\d+)", text)
    if not match:
        return None

    verse_id = match.group(1)
    data["verse_id"] = verse_id

    # -----------------------------
    # Extract sections by anchors
    # -----------------------------
    sections = {
        "sanskrit": "",
        "transliteration": "",
        "translation": "",
        "word_meaning": "",
        "commentary": ""
    }

    lines = text.split("\n")

    current = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Detect sections
        if "Word-for-word explanation" in line:
            current = "word_meaning"
            continue

        if "Commentary:" in line:
            current = "commentary"
            continue

        # Detect Sanskrit (Devanagari block)
        if "॥" in line and not sections["sanskrit"]:
            sections["sanskrit"] = line
            continue

        # Detect transliteration (contains || 1.1.1 ||)
        if "||" in line and any(c.isdigit() for c in line):
            if not sections["transliteration"]:
                sections["transliteration"] = line
                continue

        # Detect translation (starts with number.)
        if line.startswith(tuple(str(i) for i in range(1, 20))):
            current = "translation"
            sections["translation"] += line + " "
            continue

        # Append to active section
        if current:
            sections[current] += line + " "

    # Clean whitespace
    for k in sections:
        sections[k] = sections[k].strip()

    data.update(sections)

    # -----------------------------
    # Next page link
    # -----------------------------
    next_link = soup.find("a", string=lambda x: x and "Next" in x)
    next_url = None

    if next_link and next_link.get("href"):
        next_url = "https://www.wisdomlib.org" + next_link["href"]

    return data, next_url


# -----------------------------
# Crawl all verses
# -----------------------------
def scrape_all():
    url = START_URL
    results = []

    visited = set()

    while url and url not in visited:
        visited.add(url)

        soup = fetch(url)
        if not soup:
            break

        parsed = parse_page(soup)
        if not parsed:
            break

        data, next_url = parsed

        print(f"Scraped {data['verse_id']}")
        results.append(data)

        url = next_url
        time.sleep(1)  # be polite

    return results

def clean_data(data):
    unique = {}

    for item in data:
        vid = item["verse_id"]

        # Skip completely empty entries
        if all(not item[k].strip() for k in ["sanskrit", "transliteration", "translation", "word_meaning", "commentary"]):
            continue

        # If verse not seen → add
        if vid not in unique:
            unique[vid] = item
        else:
            # Prefer the richer (non-empty) version
            existing = unique[vid]

            score_existing = sum(bool(existing[k].strip()) for k in existing if k != "verse_id")
            score_new = sum(bool(item[k].strip()) for k in item if k != "verse_id")

            if score_new > score_existing:
                unique[vid] = item

    return list(unique.values())

# -----------------------------
# MAIN
# -----------------------------
def main():
    raw_data = scrape_all()
    data = clean_data(raw_data)

    with open("chandogya_wisdomlib.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nTotal verses scraped: {len(data)}")


if __name__ == "__main__":
    main()