LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "bn": "Bengali",
    "pa": "Punjabi",
    "jv": "Javanese",
    "id": "Indonesian",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "pl": "Polish",
    "uk": "Ukrainian",
    "nl": "Dutch",
    "el": "Greek",
    "cs": "Czech",
    "sv": "Swedish",
    "hu": "Hungarian",
    "fi": "Finnish",
    "no": "Norwegian",
    "da": "Danish",
    "th": "Thai",
    "he": "Hebrew",
    "ca": "Catalan",
}

def get_full_language_name(language_code: str) -> str:
    """Return the full language name for a given ISO code."""
    if "-" in language_code:
        base_code = language_code.split("-")[0]
        return LANGUAGE_MAP.get(base_code, language_code)
    return LANGUAGE_MAP.get(language_code, language_code)
