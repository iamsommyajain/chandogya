import requests
from bs4 import BeautifulSoup
import re
import json

URL = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_chAndogyopaniSad-comm.htm"


# -----------------------------
# STEP 1: FETCH PAGE
# -----------------------------
def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        raise Exception("Failed to fetch webpage")

    # 🚨 CRITICAL FIX
    return res.content.decode("utf-8", errors="ignore")

def fix_encoding(text):
    try:
        return text.encode("latin1").decode("utf-8")
    except:
        return text

# -----------------------------
# STEP 2: EXTRACT RAW TEXT
# -----------------------------
def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # Try <pre> first (some GRETIL pages use it)
    pre = soup.find("pre")
    if pre:
        return pre.get_text("\n")

    # Fallback: extract full visible text
    body = soup.find("body")
    if body:
        return body.get_text("\n")

    # Last fallback
    return soup.get_text("\n")


# -----------------------------
# STEP 3: PREPROCESS
# -----------------------------
def preprocess(text):
    text = re.sub(r"\r", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


# -----------------------------
# STEP 4: PARSE STRUCTURED DATA
# -----------------------------
def parse_chandogya(text):
    data = {}

    # -----------------------------
    # 1. Split into START blocks
    # -----------------------------
    blocks = re.split(r"START\s+ChUp\s+", text)

    for block in blocks:
        # Match chapter.section.verse
        header = re.match(r"(\d+),(\d+)\.(\d+)", block)
        if not header:
            continue

        ch, sec, v = map(int, header.groups())
        chunk_id = f"CHU.{ch}.{sec}.{v}"

        # -----------------------------
        # 2. Extract Sanskrit
        # -----------------------------
        sanskrit_match = re.search(
            r"\d+,\d+\.\d+\s+(.*?)\|\|\s*ChUp_",
            block,
            re.DOTALL
        )

        sanskrit = ""
        if sanskrit_match:
            sanskrit = sanskrit_match.group(1)

        # -----------------------------
        # 3. Extract Commentary
        # -----------------------------
        commentary_match = re.search(
            r"\|\|\s*ChUp_.*?\|\|\s*(.*)",
            block,
            re.DOTALL
        )

        commentary = ""
        if commentary_match:
            commentary = commentary_match.group(1)

        # -----------------------------
        # 4. Clean both
        # -----------------------------
        sanskrit = fix_encoding(sanskrit)
        commentary = fix_encoding(commentary)

        sanskrit = re.sub(r"\s+", " ", sanskrit.strip())
        commentary = re.sub(r"\s+", " ", commentary.strip())

        # Remove accidental leakage
        commentary = re.sub(r"ChUpBh_.*", "", commentary)

        data[chunk_id] = {
            "chunk_id": chunk_id,
            "sanskrit": sanskrit,
            "commentary": commentary
        }

    # -----------------------------
    # 5. Return sorted
    # -----------------------------
    return sorted(
        data.values(),
        key=lambda x: list(map(int, x["chunk_id"].split(".")[1:]))
    )


# -----------------------------
# STEP 5: MAIN
# -----------------------------
def main():
    print("Fetching page...")
    html = fetch_page(URL)

    print("Extracting text...")
    raw_text = extract_text(html)

    print("Preprocessing...")
    clean_text = preprocess(raw_text)

    print("Parsing structured verses...")
    data = parse_chandogya(clean_text)

    print(f"Total verses extracted: {len(data)}")

    # Save
    with open("chu_base_corpus.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Saved to chu_base_corpus.json")


if __name__ == "__main__":
    main()