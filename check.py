import json
from collections import defaultdict

# -----------------------------
# Load JSON
# -----------------------------
with open("final_corpus.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# -----------------------------
# Parse verse_id
# -----------------------------
def parse_vid(vid):
    ch, sec, v = map(int, vid.split("."))
    return ch, sec, v

# -----------------------------
# Group verses by (chapter, section)
# -----------------------------
groups = defaultdict(list)

for item in data:
    ch, sec, v = parse_vid(item["verse_id"])
    groups[(ch, sec)].append(v)

# -----------------------------
# Find missing verses
# -----------------------------
missing_report = []

for (ch, sec), verses in sorted(groups.items()):
    verses = sorted(set(verses))  # remove duplicates

    expected = list(range(verses[0], verses[-1] + 1))

    missing = sorted(set(expected) - set(verses))

    if missing:
        missing_report.append({
            "chapter": ch,
            "section": sec,
            "missing_verses": missing
        })

# -----------------------------
# Print results
# -----------------------------
if not missing_report:
    print("✅ No missing verses found!")
else:
    print("⚠️ Missing verses detected:\n")
    for item in missing_report:
        ch = item["chapter"]
        sec = item["section"]
        miss = item["missing_verses"]

        print(f"Chapter {ch}, Section {sec} → Missing: {miss}")