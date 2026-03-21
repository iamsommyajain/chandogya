import re
import json
import argparse
import os


# -----------------------------
# STEP 1: PREPROCESS RAW TEXT
# -----------------------------
def preprocess_translation_text(text):
    """
    Cleans raw PDF-pasted text.
    """

    # Remove multiple newlines → single space
    text = re.sub(r"\n+", " ", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    # Remove weird page headers (optional tweak if needed)
    text = re.sub(r"Chandogya Upanishad.*?Math, Chennai", "", text, flags=re.IGNORECASE)

    return text.strip()


# -----------------------------
# STEP 2: PARSE VERSES
# -----------------------------
def parse_translation(text):
    """
    Extracts verse-wise translations using verse markers like 1.1.1:
    """

    text = preprocess_translation_text(text)

    data = {}

    # Split using verse markers (keeps markers)
    parts = re.split(r"(\d+\.\d+\.\d+:)", text)

    for i in range(1, len(parts), 2):
        marker = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""

        # Extract numbers
        nums = re.findall(r"\d+", marker)

        if len(nums) != 3:
            continue

        a, k, v = nums
        chunk_id = f"CHU.{a}.{k}.{v}"

        # Clean content
        content = content.strip()

        # Remove accidental next verse
        content = re.sub(r"\d+\.\d+\.\d+:.*", "", content)

        # Fix encoding artifacts (like Udg$tha)
        content = content.replace("$", "")

        # Remove trailing noise
        content = re.sub(r"\s+", " ", content)

        data[chunk_id] = content.strip()

    return data


# -----------------------------
# STEP 3: VALIDATION
# -----------------------------
def validate(data):
    print("\n🔍 VALIDATION REPORT\n")

    print(f"Total verses extracted: {len(data)}\n")

    # Show first few entries
    print("Sample output:\n")

    for i, (k, v) in enumerate(data.items()):
        print(f"{k} → {v[:100]}")
        print("------")

        if i == 9:
            break


# -----------------------------
# STEP 4: MAIN
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Clean and parse translation file")
    parser.add_argument("--input", required=True, help="Path to translation text file")
    parser.add_argument("--output", default="translation_data.json", help="Output JSON file")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        return

    # Read input
    with open(args.input, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Parse
    translation_data = parse_translation(raw_text)

    # Validate
    validate(translation_data)

    # Save
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(translation_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved cleaned translations to: {args.output}")


if __name__ == "__main__":
    main()