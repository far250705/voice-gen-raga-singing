import json
import re
import os
import time
import google.generativeai as genai

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = "gemini-2.5-flash"

_model = None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    _model = genai.GenerativeModel(GEMINI_MODEL)
    print(f"DEBUG: Gemini initialized with model {GEMINI_MODEL}")
else:
    print("ERROR: GEMINI_API_KEY environment variable is not set!")


class GeminiError(Exception):
    """Raised when Gemini cannot generate valid notes."""
    pass


# ── Prompt builder ────────────────────────────────────────────────────────────
def _build_prompt(raga: dict, thala: dict, avartanams: int) -> str:
    solfege_list = [info["solfege"] for _, info in raga["notes"].items()]
    valid_notes  = solfege_list + ["S'"]
    beats        = thala["beats"]

    return f"""You are a Carnatic music composer. Generate a {avartanams}-avartanam composition.

Raga: {raga['name']}
Valid notes (ONLY use these): {valid_notes}
Thala: {thala['name']} ({beats} beats per avartanam)
Arohanam:   {raga['arohanam']}
Avarohanam: {raga['avarohanam']}

Rules:
1. Each avartanam must have exactly {beats} notes.
2. Use ONLY the valid notes listed above. No other symbols.
3. The last note of the last avartanam must be "S".
4. Each avartanam should start on "S" or a raga-characteristic note.
5. Follow melodic phrases typical of {raga['name']}.

Respond ONLY with a JSON array of {avartanams} arrays, each with exactly {beats} note strings.
Example for 2 avartanams of 4 beats: [["S","R2","G3","M1"],["P","D2","N3","S"]]
No explanation, no markdown, no extra text — pure JSON only."""


# ── Validator ─────────────────────────────────────────────────────────────────
def _validate(data, raga: dict, thala: dict, avartanams: int) -> list:
    solfege_list = [info["solfege"] for _, info in raga["notes"].items()]
    valid_notes  = set(solfege_list + ["S'", "S"])
    beats        = thala["beats"]

    if not isinstance(data, list):
        raise GeminiError(f"Expected a JSON array, got {type(data).__name__}")
    if len(data) != avartanams:
        raise GeminiError(f"Expected {avartanams} avartanams, got {len(data)}")

    for i, cycle in enumerate(data):
        if not isinstance(cycle, list):
            raise GeminiError(f"Avartanam {i+1} is not a list")
        if len(cycle) != beats:
            raise GeminiError(f"Avartanam {i+1} has {len(cycle)} notes, expected {beats}")
        for note in cycle:
            if note not in valid_notes:
                raise GeminiError(
                    f"Invalid note '{note}' in avartanam {i+1}. Valid: {sorted(valid_notes)}"
                )

    # Soft-fix: ensure last note is Sa
    if data[-1][-1] not in ("S", "S'"):
        data[-1][-1] = "S"

    return data


# ── Main entry point ──────────────────────────────────────────────────────────
def generate_notes_gemini(raga: dict, thala: dict, avartanams: int = 4) -> list:
    if _model is None:
        raise GeminiError(
            "GEMINI_API_KEY is not set. Add it to your environment variables."
        )

    print(f"DEBUG: Starting Gemini generation for Raga: {raga['name']}")
    prompt     = _build_prompt(raga, thala, avartanams)
    last_error = None

    for attempt in range(3):
        try:
            print(f"DEBUG: Attempt {attempt + 1} — sending to {GEMINI_MODEL}...")
            response = _model.generate_content(
                prompt,
                generation_config={"max_output_tokens": 1024},
                request_options={"timeout": 60},   # was 25, now 60
            )
            raw = response.text.strip()
            print(f"DEBUG: Response received on attempt {attempt + 1}: {raw[:100]}...")
            break
        except Exception as e:
            last_error = e
            print(f"ERROR attempt {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)   # wait 1s then 2s before retrying
    else:
        raise GeminiError(f"Gemini failed after 3 attempts: {last_error}")

    # Strip markdown fences if Gemini added them anyway
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$",          "", raw, flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw)
        print("DEBUG: JSON parsed successfully.")
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON. Raw was: {raw}")
        raise GeminiError(f"Gemini returned invalid JSON: {e}")

    validated = _validate(data, raga, thala, avartanams)
    print("DEBUG: Validation passed.")
    return validated
