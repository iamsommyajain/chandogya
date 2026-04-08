import requests
from bs4 import BeautifulSoup
import re
import json

# ================================
# CONFIG
# ================================
INPUT_JSON = "output/chu_merged_corpus.json"     # your existing JSON
OUTPUT_JSON = "output/chu_merged_with_sanskrit.json"   # final merged JSON
URL = "https://sanskritdocuments.org/doc_upanishhat/chhaandogya.html"

# ================================
# STEP 1: FETCH WEBPAGE
# ================================
print("Fetching Sanskrit text...")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(URL, headers=headers)
response.encoding = "utf-8"

if response.status_code != 200:
    print("Status Code:", response.status_code)
    raise Exception("Failed to fetch webpage")

html = response.text

# ================================
# STEP 2: PARSE TEXT
# ================================
soup = BeautifulSoup(html, "html.parser")
text = soup.get_text("\n")

# ================================
# STEP 3: UTIL FUNCTIONS
# ================================

# Devanagari → Arabic numeral conversion
DEV_TO_ARABIC = str.maketrans("०१२३४५६७८९", "0123456789")

def convert_dev_to_arabic(dev_str):
    return dev_str.translate(DEV_TO_ARABIC)

def clean_text(t):
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.replace(" ।", "।")
    return t

# ================================
# STEP 4: EXTRACT VERSES
# ================================
print("Extracting verses...")

pattern = r"(.*?)॥\s*([०-९]+\.[०-९]+\.[०-९]+)\s*॥"
matches = re.findall(pattern, text, re.DOTALL)

sanskrit_map = {}

for verse_text, dev_id in matches:
    # Convert ID
    clean_id = convert_dev_to_arabic(dev_id.strip())
    chunk_id = f"CHU.{clean_id}"

    # Clean verse text
    verse_text = clean_text(verse_text)

    # Store
    sanskrit_map[chunk_id] = verse_text

print(f"Total verses extracted: {len(sanskrit_map)}")

# ================================
# STEP 5: LOAD YOUR JSON
# ================================
print("Loading input JSON...")

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# ================================
# STEP 6: MERGE DATA
# ================================
print("Merging Sanskrit into JSON...")

matched = 0
missing = []

for item in data:
    cid = item.get("chunk_id")

    if cid in sanskrit_map:
        item["sanskrit_original"] = sanskrit_map[cid]
        matched += 1
    else:
        item["sanskrit_original"] = ""
        missing.append(cid)

print(f"Matched: {matched}")
print(f"Missing: {len(missing)}")

# ================================
# STEP 7: SAVE OUTPUT
# ================================
print("Saving output...")

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Done ✅")

# ================================
# OPTIONAL DEBUG
# ================================
if missing:
    print("\nSample missing IDs:")
    print(missing[:10])