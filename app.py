import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── Data ──────────────────────────────────────────────────────────────────────

THALAS = [
    {
        "name": "Adi",
        "beats": 8,
        "subdivisions": [4, 2, 2],
        "subdivision_names": ["Laghu", "Drutam", "Drutam"],
        "clap_pattern": ["Clap", "Finger1", "Finger2", "Finger3", "Clap", "Wave", "Clap", "Wave"],
        "description": "Most common thala in Carnatic music"
    },
    {
        "name": "Rupaka",
        "beats": 6,
        "subdivisions": [2, 4],
        "subdivision_names": ["Drutam", "Laghu"],
        "clap_pattern": ["Clap", "Wave", "Clap", "Finger1", "Finger2", "Finger3"],
        "description": "Common in devotional compositions"
    },
    {
        "name": "Misra Chapu",
        "beats": 7,
        "subdivisions": [3, 2, 2],
        "subdivision_names": ["Tisra", "Drutam", "Drutam"],
        "clap_pattern": ["Clap", "Finger1", "Finger2", "Clap", "Wave", "Clap", "Wave"],
        "description": "Asymmetric thala with 3+2+2 grouping"
    },
    {
        "name": "Khanda Chapu",
        "beats": 5,
        "subdivisions": [2, 3],
        "subdivision_names": ["Drutam", "Tisra"],
        "clap_pattern": ["Clap", "Wave", "Clap", "Finger1", "Finger2"],
        "description": "Asymmetric thala with 2+3 grouping"
    }
]

SHRUTIS = [
    {"name": "Sa (C)",  "key": "C",    "base_frequency_hz": 261.63},
    {"name": "C#/Db",  "key": "C#",   "base_frequency_hz": 277.18},
    {"name": "D",       "key": "D",    "base_frequency_hz": 293.66},
    {"name": "D#/Eb",  "key": "D#",   "base_frequency_hz": 311.13},
    {"name": "E (Ga)", "key": "E",    "base_frequency_hz": 329.63},
    {"name": "F",       "key": "F",    "base_frequency_hz": 349.23},
    {"name": "F#",      "key": "F#",   "base_frequency_hz": 369.99},
    {"name": "G",       "key": "G",    "base_frequency_hz": 392.00},
    {"name": "G#/Ab",  "key": "G#",   "base_frequency_hz": 415.30},
    {"name": "A",       "key": "A",    "base_frequency_hz": 440.00},
    {"name": "A#/Bb",  "key": "A#",   "base_frequency_hz": 466.16},
    {"name": "B",       "key": "B",    "base_frequency_hz": 493.88}
]

RAGAS = [
    {
        "name": "Kalyani",
        "melakarta_number": 65,
        "thaat": "Kalyan",
        "notes": {
            "Sa":   {"solfege": "S",  "semitone_offset": 0},
            "Ri2":  {"solfege": "R2", "semitone_offset": 2},
            "Ga3":  {"solfege": "G3", "semitone_offset": 4},
            "Ma2":  {"solfege": "M2", "semitone_offset": 6},
            "Pa":   {"solfege": "P",  "semitone_offset": 7},
            "Dha2": {"solfege": "D2", "semitone_offset": 9},
            "Ni3":  {"solfege": "N3", "semitone_offset": 11}
        },
        "arohanam":  ["Sa", "Ri2", "Ga3", "Ma2", "Pa", "Dha2", "Ni3", "Sa'"],
        "avarohanam": ["Sa'", "Ni3", "Dha2", "Pa", "Ma2", "Ga3", "Ri2", "Sa"]
    },
    {
        "name": "Shankarabharanam",
        "melakarta_number": 29,
        "thaat": "Bilawal",
        "notes": {
            "Sa":   {"solfege": "S",  "semitone_offset": 0},
            "Ri2":  {"solfege": "R2", "semitone_offset": 2},
            "Ga3":  {"solfege": "G3", "semitone_offset": 4},
            "Ma1":  {"solfege": "M1", "semitone_offset": 5},
            "Pa":   {"solfege": "P",  "semitone_offset": 7},
            "Dha2": {"solfege": "D2", "semitone_offset": 9},
            "Ni3":  {"solfege": "N3", "semitone_offset": 11}
        },
        "arohanam":  ["Sa", "Ri2", "Ga3", "Ma1", "Pa", "Dha2", "Ni3", "Sa'"],
        "avarohanam": ["Sa'", "Ni3", "Dha2", "Pa", "Ma1", "Ga3", "Ri2", "Sa"]
    },
    {
        "name": "Mayamalavagowla",
        "melakarta_number": 15,
        "thaat": "Bhairav",
        "notes": {
            "Sa":   {"solfege": "S",  "semitone_offset": 0},
            "Ri1":  {"solfege": "R1", "semitone_offset": 1},
            "Ga3":  {"solfege": "G3", "semitone_offset": 4},
            "Ma1":  {"solfege": "M1", "semitone_offset": 5},
            "Pa":   {"solfege": "P",  "semitone_offset": 7},
            "Dha1": {"solfege": "D1", "semitone_offset": 8},
            "Ni3":  {"solfege": "N3", "semitone_offset": 11}
        },
        "arohanam":  ["Sa", "Ri1", "Ga3", "Ma1", "Pa", "Dha1", "Ni3", "Sa'"],
        "avarohanam": ["Sa'", "Ni3", "Dha1", "Pa", "Ma1", "Ga3", "Ri1", "Sa"]
    }
]

# ── Health check (required by Azure App Service) ──────────────────────────────

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Carnatic Music API is running"})

# ── Thalas ────────────────────────────────────────────────────────────────────

@app.route("/api/thalas", methods=["GET"])
def get_thalas():
    """Return all thalas."""
    return jsonify({"thalas": THALAS})

@app.route("/api/thalas/<string:name>", methods=["GET"])
def get_thala(name):
    """Return a single thala by name (case-insensitive)."""
    thala = next(
        (t for t in THALAS if t["name"].lower() == name.lower()), None
    )
    if thala is None:
        return jsonify({"error": f"Thala '{name}' not found"}), 404
    return jsonify(thala)

# ── Shrutis ───────────────────────────────────────────────────────────────────

@app.route("/api/shrutis", methods=["GET"])
def get_shrutis():
    """Return all shrutis."""
    return jsonify({"shrutis": SHRUTIS})

@app.route("/api/shrutis/<string:key>", methods=["GET"])
def get_shruti(key):
    """Return a single shruti by key (e.g. C, C#, D)."""
    shruti = next(
        (s for s in SHRUTIS if s["key"].lower() == key.lower()), None
    )
    if shruti is None:
        return jsonify({"error": f"Shruti '{key}' not found"}), 404
    return jsonify(shruti)

# ── Ragas ─────────────────────────────────────────────────────────────────────

@app.route("/api/ragas", methods=["GET"])
def get_ragas():
    """Return all ragas."""
    return jsonify({"ragas": RAGAS})

@app.route("/api/ragas/<string:name>", methods=["GET"])
def get_raga(name):
    """Return a single raga by name (case-insensitive)."""
    raga = next(
        (r for r in RAGAS if r["name"].lower() == name.lower()), None
    )
    if raga is None:
        return jsonify({"error": f"Raga '{name}' not found"}), 404
    return jsonify(raga)

@app.route("/api/ragas/<string:name>/notes", methods=["GET"])
def get_raga_notes(name):
    """Return just the notes of a raga, optionally transposed to a shruti key."""
    raga = next(
        (r for r in RAGAS if r["name"].lower() == name.lower()), None
    )
    if raga is None:
        return jsonify({"error": f"Raga '{name}' not found"}), 404

    # Optional ?shruti=C# query param — returns absolute frequencies
    shruti_key = request.args.get("shruti")
    if shruti_key:
        shruti = next(
            (s for s in SHRUTIS if s["key"].lower() == shruti_key.lower()), None
        )
        if shruti is None:
            return jsonify({"error": f"Shruti '{shruti_key}' not found"}), 404

        base_hz = shruti["base_frequency_hz"]
        notes_with_freq = {}
        for note_name, note_data in raga["notes"].items():
            offset = note_data["semitone_offset"]
            freq = round(base_hz * (2 ** (offset / 12)), 2)
            notes_with_freq[note_name] = {**note_data, "frequency_hz": freq}

        return jsonify({
            "raga": raga["name"],
            "shruti": shruti_key,
            "base_frequency_hz": base_hz,
            "notes": notes_with_freq
        })

    return jsonify({"raga": raga["name"], "notes": raga["notes"]})

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Azure sets the PORT env var; fall back to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
