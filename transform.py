import json

# Load your JSON file
with open("output/chu_merged_corpus.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# If it's a list of chunks
for item in data:
    item["transliteration"] = item.pop("sanskrit")
    item["meaning_sanskrit"] = item.pop("commentary")

# Save updated JSON
with open("output/chu_merged_corpus.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)