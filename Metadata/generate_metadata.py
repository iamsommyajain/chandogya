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
    return f"""You are an expert philosopher trained in the Upanishads and Advaita Vedanta.

Your task is to analyze a given verse's Sanskrit text, transliteration, translation, word meaning, and commentary to extract arguable, grounded, and debate-ready philosophical content.

### GROUNDING RULE:

- Every claim MUST be directly supportable from the translation, word meaning, or commentary.
- Do NOT invent interpretations not grounded in the text.
- If ambiguity exists, do not fabricate objections or claims.


### CONCEPT TAG RULES

- Choose 1 to 3 of the most relevant concept tags for the given verse ONLY from the exact list below:

The Sacred Syllable "Om"
The Three Branches of Duty
The Individual Self Identical with the Infinite Brahman
The Cosmic-Egg
The Story of Jabala, a Brahmin
Brahman as Life, Joy, and the Void
Man’s Destiny Determined by His Conduct
The Universal Self
Being as the Source of All
In Sleep One Reaches Being
The Unitary World-Self, The Immanent Reality of All Things and Man
Progressive Worship of Brahman up to the Universal Self
The Progressive Instruction of Indra by Prajapati
The Knowledge of Brahman
Sacrifice and Asceticism (Tapas)
The Atman (Brahman) as the Unity
The Symbolical Representations of Brahman
Substitutes for Ritual Practices
Sole Reality of Brahman
Brahman as the Cosmological and Physical Principle
Organic and Inorganic Nature
The Subtle Body and Ethical Qualification
The Empirical Form of Emancipation
Ethical Theories of Transmigration


### CLAIM CANDIDATE RULES
- Definition: Claim candidates are short statements that a verse can support, and that someone could agree or disagree with in a conversation.

- They are basically: What philosophical point can we reasonably argue from this verse?

### Rules:

- Generate exactly 2–4 claims (Output as an array of strings).
- Each claim must be DISTINCT
- Must be arguable (not descriptive summary).
- Must be strictly grounded in the commentary/translation.


### OBJECTION HOOK RULES

Definition: Objection Hooks are common doubts, misunderstandings, or counter-questions that people naturally raise when hearing those claims.

They are basically: If I say this claim, what will a user likely object to next?

### Rules:

- Generate exactly 2–4 objections (Output as an array of strings).
- Each objection hook MUST be grounded in at least one claim_candidate.
- Must expose philosophical tension, contradiction, or ambiguity based on the claims. 
- Must NOT simply restate the claims in the negative


### INPUT:

Verse Sanskrit: {chunk.get('sanskrit', '')}
Verse Transliteration: {chunk.get('transliteration', '')}
Translation: {chunk.get('translation', '')}
Verse Word Meaning: {chunk.get('word_meaning', '')}
Commentary: {chunk.get('commentary', '')}

###  STRICT OUTPUT RULES:

Return ONLY valid JSON.
No markdown formatting blocks (like ```json), no explanations, no extra text before or after the JSON.
All fields must be present.
Follow the schema exactly.


OUTPUT FORMAT:

{{
"concept_tags": ["tag1", "tag2"],
"claim_candidates": ["claim 1", "claim 2"],
"objection_hooks": ["objection 1", "objection 2"],
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
    input_path = "output/final_corpus.json"
    output_path = "output/chundogya_upnishad_generated_metadata.json"

    with open(input_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    enriched = []
    failed = []

    
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
