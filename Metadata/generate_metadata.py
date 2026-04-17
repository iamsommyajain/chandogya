import json
import os
import time
import re
from tqdm import tqdm
from dotenv import load_dotenv
from groq import Groq  # Switched from google.genai
import argparse

# -----------------------------
# LOAD .ENV & CONFIGURE CLIENT
# -----------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY_12")

if not api_key:
    print("❌ Error: GROQ_API_KEY_12 not found in .env file.")
    exit(1)

# Initialize the Groq Client
client = Groq(api_key=api_key)
MODEL_ID = "openai/gpt-oss-120b" 



def build_prompt(chunk):
    return f"""You are an expert philosopher trained in the Upanishads and Advaita Vedanta.

Your task is to analyze a given verse's Sanskrit text, transliteration, translation, word meaning, and commentary to extract arguable, grounded, and debate-ready philosophical content.

### GROUNDING RULE:
- Every claim MUST be directly supportable from the translation, word meaning, or commentary.
- Do NOT invent interpretations not grounded in the text.
- If ambiguity exists, do not fabricate objections or claims.

### CONCEPT TAG RULES
- Choose 1 to 3 of the most relevant concept tags for the given verse ONLY from the exact list below:
1) The Sacred Syllable "Om"
2) The Three Branches of Duty
3) The Individual Self Identical with the Infinite Brahman
4) The Cosmic-Egg
5) The Story of Jabala, a Brahmin
6) Brahman as Life, Joy, and the Void
7) Man’s Destiny Determined by His Conduct
8) The Universal Self
9) Being as the Source of All
10) In Sleep One Reaches Being
11) The Unitary World-Self, The Immanent Reality of All Things and Man
12) Progressive Worship of Brahman up to the Universal Self
13) The Progressive Instruction of Indra by Prajapati
14) The Knowledge of Brahman
15) Sacrifice and Asceticism (Tapas)
16) The Atman (Brahman) as the Unity
17) The Symbolical Representations of Brahman
18) Substitutes for Ritual Practices
19) Sole Reality of Brahman
20) Brahman as the Cosmological and Physical Principle
21) Organic and Inorganic Nature
22) The Subtle Body and Ethical Qualification
23) The Empirical Form of Emancipation
24) Ethical Theories of Transmigration

### CLAIM CANDIDATE RULES
- Generate exactly 2–4 claims
- Each claim must be DISTINCT
- Must be arguable
- Must be grounded in commentary/translation

### OBJECTION HOOK RULES
- Generate exactly 2–4 objections
- Must relate to claims
- Must expose philosophical tension

### IMPORTANT OUTPUT RULES
- Return ONLY valid JSON
- No markdown
- No explanations
- No extra text
- Do NOT use double quotes inside string values
- Use single quotes if quoting is needed
- All values must be single-line strings

### INPUT:

Verse ID: {chunk.get('verse_id', '')}
Verse Sanskrit: {chunk.get('sanskrit', '')}
Verse Transliteration: {chunk.get('transliteration', '')}
Translation: {chunk.get('translation', '')}
Verse Word Meaning: {chunk.get('word_meaning', '')}
Commentary: {chunk.get('commentary', '')}

OUTPUT FORMAT:
{{
"concept_tags": ["tag1", "tag2"],
"claim_candidates": ["claim 1", "claim 2"],
"objection_hooks": ["objection 1", "objection 2"]
}}
"""

# -----------------------------
# CLEAN JSON
# -----------------------------
def clean_json(text):
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return text

# -----------------------------
# VALIDATE SCHEMA
# -----------------------------
def validate_schema(data):
    required = ["concept_tags", "claim_candidates", "objection_hooks"]

    if not all(k in data for k in required):
        return False

    if not isinstance(data["concept_tags"], list):
        return False

    if not isinstance(data["claim_candidates"], list):
        return False

    if not isinstance(data["objection_hooks"], list):
        return False

    return True

# -----------------------------
# GENERATE METADATA
# -----------------------------
def generate_metadata(chunk):
    prompt = build_prompt(chunk)

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            top_p=1,
            max_completion_tokens=2048,
        )

        response_text = completion.choices[0].message.content
        cleaned = clean_json(response_text)

        parsed = json.loads(cleaned)

        if validate_schema(parsed):
            return parsed

        return None

    except Exception as e:
        print(f"\n⚠️ Groq API Error for {chunk.get('verse_id')}: {e}")
        return None

# -----------------------------
# RETRY
# -----------------------------
def generate_with_retry(chunk, retries=3):
    for i in range(retries):
        result = generate_metadata(chunk)

        if result:
            return result

        print(f"Retrying {chunk.get('verse_id')} ({i+1}/{retries})...")
        time.sleep(20)

    return None

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Enrich Upanishad corpus using Groq.")
    parser.add_argument("--input", default="final_corpus.json")
    parser.add_argument("--output", default="chandogya_enriched.jsonl")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"File not found: {args.input}")
        return

    with open(args.input, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    processed_ids = set()

    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    processed_ids.add(json.loads(line)["verse_id"])
                except:
                    continue

        print(f"Resuming: {len(processed_ids)} already completed.")

    with open(args.output, "a", encoding="utf-8") as f_out:
        for chunk in tqdm(corpus, desc="Tagging"):
            vid = chunk.get("verse_id")

            if vid in processed_ids:
                continue

            metadata = generate_with_retry(chunk)

            if metadata:
                chunk.update(metadata)
                f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                f_out.flush()
                os.fsync(f_out.fileno())

            time.sleep(15)

    print(f"\n✅ Done. Results saved in: {args.output}")

# -----------------------------
# ENTRY
# -----------------------------
if __name__ == "__main__":
    main()


# python generate_metadata.py --input path/to/corpus.json  --output path/to/output.json
