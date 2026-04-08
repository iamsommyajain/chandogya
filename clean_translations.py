import json

INPUT_FILE = "final_corpus.json"
OUTPUT_FILE = "final_corpus.json"


# -----------------------------
# Utility: completeness score
# -----------------------------
def score(entry):
    fields = ["sanskrit", "transliteration", "translation", "word_meaning", "commentary"]
    return sum(1 for f in fields if entry.get(f, "").strip())


# -----------------------------
# Utility: check empty entry
# -----------------------------
def is_empty(entry):
    return score(entry) == 0


# -----------------------------
# Clean dataset
# -----------------------------
def clean_dataset(data):
    cleaned = {}

    for item in data:
        vid = item["verse_id"]

        # Skip completely empty entries
        if is_empty(item):
            continue

        if vid not in cleaned:
            cleaned[vid] = item
        else:
            # Keep the better (more complete) one
            if score(item) > score(cleaned[vid]):
                cleaned[vid] = item

    return list(cleaned.values())


# -----------------------------
# MAIN
# -----------------------------
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Original count: {len(data)}")

    cleaned = clean_dataset(data)

    print(f"Cleaned count: {len(cleaned)}")

    # Sort properly
    def sort_key(x):
        return list(map(int, x["verse_id"].split(".")))

    cleaned = sorted(cleaned, key=sort_key)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print("✅ Cleaned file saved as chandogya_cleaned.json")


if __name__ == "__main__":
    main()