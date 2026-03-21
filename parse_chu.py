import re
import json
import argparse
import os


# -----------------------------
# Utility: Clean text
# -----------------------------
def clean_text(text):
    if not text:
        return ""

    text = text.strip()

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove trailing markers like //1 // or ||...||
    text = re.sub(r"//\d+\s*", "", text)
    text = re.sub(r"\|\|.*?\|\|", "", text)

    return text.strip()


# -----------------------------
# Extract Chunk ID
# -----------------------------
def extract_id(block):
    match = re.search(r"ChUp\s+(\d+),(\d+)\.(\d+)", block)
    if match:
        a, k, v = match.groups()
        return f"CHU.{a}.{k}.{v}"
    return None


# -----------------------------
# Extract Sanskrit Verse
# -----------------------------
def extract_sanskrit(block):
    match = re.search(
        r"\n(.*?)\|\|\s*ChUp_\d+,\d+\.\d+\s*\|\|",
        block,
        re.DOTALL
    )
    if match:
        return clean_text(match.group(1))
    return ""


# -----------------------------
# Extract Commentary (Bhāṣya)
# -----------------------------
def extract_commentary(block):
    match = re.search(
        r"ChUpBh_\d+,\d+\.\d+\s+(.*)",
        block,
        re.DOTALL
    )
    if match:
        return clean_text(match.group(1))
    return ""


# -----------------------------
# Main Parsing Function
# -----------------------------
def parse_text(raw_text):
    chunks = []

    blocks = raw_text.split("START")

    for block in blocks:
        block = block.strip()

        if not block:
            continue

        chunk_id = extract_id(block)

        if not chunk_id:
            print("⚠️ Skipping block (no ID found)")
            continue

        sanskrit = extract_sanskrit(block)
        commentary = extract_commentary(block)

        chunk = {
            "chunk_id": chunk_id,
            "sanskrit": sanskrit,
            "commentary": commentary
        }

        chunks.append(chunk)

    return chunks


# -----------------------------
# Validation
# -----------------------------
def validate(chunks):
    print("\n🔍 Running Validation...\n")

    ids = set()

    for c in chunks:
        cid = c["chunk_id"]

        # Duplicate check
        if cid in ids:
            print(f"❌ Duplicate ID: {cid}")
        ids.add(cid)

        # Missing fields
        if not c["sanskrit"]:
            print(f"⚠️ Missing Sanskrit: {cid}")

        if not c["commentary"]:
            print(f"⚠️ Missing Commentary: {cid}")

    print(f"\n✅ Total Chunks Parsed: {len(chunks)}\n")


# -----------------------------
# Main CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to input text file")
    parser.add_argument("--output", default="chu_base_corpus.json")

    args = parser.parse_args()

    # Check file exists
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        return

    # Read file
    with open(args.input, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Parse
    chunks = parse_text(raw_text)

    # Validate
    validate(chunks)

    # Save JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"📁 Output saved to: {args.output}")


if __name__ == "__main__":
    main()