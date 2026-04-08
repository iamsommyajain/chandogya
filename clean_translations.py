import json
import re

INPUT_FILE = "final_corpus.json"
OUTPUT_FILE = "cleaned_corpus.json"


# -----------------------------
# RULE 1: Remove verse markers
# -----------------------------
def remove_verse_markers(text):
    if not text:
        return text
    return re.sub(r"[|।॥]+\s*\d+\.\d+\.\d+\s*[|।॥]*", "", text)


# -----------------------------
# RULE 2: Normalize whitespace
# -----------------------------
def normalize_whitespace(text):
    if not text:
        return text
    text = re.sub(r"\s+", " ", text)  # collapse multiple spaces/newlines
    return text.strip()

def remove_translation_prefix(text):
    if not text:
        return text
    # Removes patterns like "1. ", "23. ", etc. only at the beginning
    return re.sub(r"^\d+\.\s*", "", text)


# -----------------------------
# RULE 3: Fix punctuation spacing
# -----------------------------
def fix_punctuation_spacing(text):
    if not text:
        return text

    # remove space BEFORE punctuation
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\s+;", ";", text)
    text = re.sub(r"\s+:", ":", text)

    # ensure space AFTER punctuation (optional but cleaner)
    text = re.sub(r",(?=\S)", ", ", text)
    text = re.sub(r";(?=\S)", "; ", text)
    text = re.sub(r":(?=\S)", ": ", text)

    return text


# -----------------------------
# APPLY CLEANING PIPELINE
# -----------------------------
def clean_text(text):
    text = remove_verse_markers(text)
    text = normalize_whitespace(text)
    text = fix_punctuation_spacing(text)
    return text


def clean_dataset(data):
    fields = ["sanskrit", "transliteration", "translation", "word_meaning", "commentary"]

    for entry in data:
        for field in fields:
            if field in entry and entry[field]:
                entry[field] = clean_text(entry[field])

        # Apply ONLY to translation
        if "translation" in entry and entry["translation"]:
            entry["translation"] = remove_translation_prefix(entry["translation"])

    return data


# -----------------------------
# MAIN
# -----------------------------
def main():
    print("Loading dataset...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Cleaning dataset...")
    cleaned_data = clean_dataset(data)

    print("Saving cleaned dataset...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print("Done! Cleaned file saved as:", OUTPUT_FILE)


if __name__ == "__main__":
    main()