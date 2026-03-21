import json
import os


# -----------------------------
# LOAD FILES
# -----------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# MERGE FUNCTION
# -----------------------------
def merge_translations(corpus, translations):
    missing = []
    matched = 0

    for chunk in corpus:
        cid = chunk["chunk_id"]

        if cid in translations:
            chunk["translation"] = translations[cid]
            matched += 1
        else:
            missing.append(cid)

    return corpus, matched, missing


# -----------------------------
# VALIDATION
# -----------------------------
def validate(corpus, matched, missing):
    print("\n🔍 MERGE VALIDATION\n")

    total = len(corpus)

    print(f"Total chunks        : {total}")
    print(f"Matched translations: {matched}")
    print(f"Missing translations: {len(missing)}")

    coverage = (matched / total) * 100
    print(f"Coverage            : {coverage:.2f}%")

    # Show some missing
    if missing:
        print("\n⚠️ Sample missing IDs:")
        for m in missing[:10]:
            print(m)

    # Spot check correct mapping
    print("\n🔎 Sample merged entries:\n")
    for c in corpus[:5]:
        print(c["chunk_id"])
        print("Translation:", c.get("translation", "MISSING")[:100])
        print("---")


# -----------------------------
# SAVE OUTPUT
# -----------------------------
def save_output(corpus, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved merged corpus to: {path}")


# -----------------------------
# MAIN
# -----------------------------
def main():
    output_path = "output/chu_merged_corpus.json"

    corpus = load_json("chu_base_corpus.json")
    translations = load_json("translation_data.json")

    merged, matched, missing = merge_translations(corpus, translations)

    validate(merged, matched, missing)

    save_output(merged, output_path)


if __name__ == "__main__":
    main()