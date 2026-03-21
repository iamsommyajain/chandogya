import json
import os
import time
import re
from tqdm import tqdm
import google.generativeai as genai


# -----------------------------
# CONFIGURE API
# -----------------------------
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use latest stable Gemini model
model = genai.GenerativeModel("gemini-2.5-flash-lite")


# -----------------------------
# PROMPT BUILDER
# -----------------------------
def build_prompt(chunk):
    return f"""
You are an expert philosopher trained in Vedanta, metaphysics, and textual analysis.

Your task is to analyze a single passage from the Chandogya Upanishad and generate structured philosophical metadata. You are annotating a philosophical dataset based on the Chandogya Upanishad.

GOAL:
Enable deep philosophical discussion grounded in the text.

STRICT RULES:
Return ONLY valid JSON.
2. DO NOT use markdown (no ```json).
3. DO NOT include explanations.
4. DO NOT include extra text before or after JSON.
5. Ensure all fields are present.
6. Ensure consistent schema.
7. Keep output concise but meaningful.


CONCEPT TAG RULES:
- Tags must refer to specific Upanishadic concepts, not general philosophy
- Avoid abstract words like: philosophy, spirituality, ultimate_reality, symbolism, principle
- Prefer tags like:
  om_symbolism
  prana_speech_identity
  hierarchy_of_essence
  sound_metaphysics
  ritual_to_knowledge_transition
- Use 3–5 tags only

CLAIM RULES:
- 2–4 precise claims
- Non-redundant
- Use compact subject-predicate structure
- Ground in commentary when possible
- Do NOT restate the same claim in different wording.
- Each claim must express a distinct philosophical statement.

OBJECTION RULES:
- Must be real philosophical challenges
- Not paraphrases of claims
- Should expose tension, ambiguity, or epistemic gaps

PHILOSOPHICAL MOVES:
- Identify reasoning types (e.g., symbolic_identification, analogy, hierarchy, identity_claim, ritual_to_metaphysics)
- Do NOT restate the same claim in different wording.
Each claim must express a distinct philosophical statement.

DIALECTICAL POTENTIAL:
- Identify types of debates this supports (e.g., symbol_vs_reality, means_vs_end, epistemic_validity, metaphysical_identity)

DEPTH SCORE:
1 = descriptive
2 = symbolic
3 = conceptual
4 = philosophical reasoning
5 = metaphysical core

INPUT:
Chunk ID: {chunk['chunk_id']}

Translation:
{chunk.get('translation', '')}

Commentary:
{chunk.get('commentary', '')}

IMPORTANT:
Prioritize commentary over translation.

OUTPUT:
{{
  "concept_tags": [...],
  "claim_candidates": [...],
  "objection_hooks": [...],
  "philosophical_moves": [...],
  "dialectical_potential": [...],
  "depth_score": X
}}
"""


# -----------------------------
# CLEAN JSON OUTPUT
# -----------------------------
def clean_json(text):
    text = text.strip()

    # Remove markdown ```json blocks
    if text.startswith("```"):
        text = re.sub(r"```[a-zA-Z]*", "", text)
        text = text.replace("```", "")

    # Extract JSON safely
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group()

    return text


# -----------------------------
# GENERATE METADATA
# -----------------------------
def generate_metadata(chunk):
    prompt = build_prompt(chunk)

    response = model.generate_content(prompt)
    text = response.text

    cleaned = clean_json(text)

    try:
        return json.loads(cleaned)
    except Exception:
        print("⚠️ JSON parse error for:", chunk["chunk_id"])
        print(cleaned[:300])
        return None


# -----------------------------
# RETRY LOGIC
# -----------------------------
def generate_with_retry(chunk, retries=3):
    for i in range(retries):
        result = generate_metadata(chunk)
        if result:
            return result

        print(f"Retry {i+1} for {chunk['chunk_id']}...")
        time.sleep(5)

    return None


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():
    input_path = "output/chu_merged_corpus.json"
    output_path = "output/chu_metadata_sample.json"

    with open(input_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    enriched = []
    failed = []

    # 🔥 Start small (scale later)
    for chunk in tqdm(corpus[:3]):

        metadata = generate_with_retry(chunk)

        if metadata:
            chunk.update(metadata)
            enriched.append(chunk)
        else:
            failed.append(chunk["chunk_id"])
            print("❌ Failed:", chunk["chunk_id"])

        # 🚨 Rate limiting (Gemini free tier)
        time.sleep(3)

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print("\n✅ Metadata generation complete")
    print(f"✔ Success: {len(enriched)}")
    print(f"❌ Failed: {len(failed)}")

    if failed:
        print("\n⚠️ Failed IDs:")
        for fid in failed:
            print(fid)


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    main()