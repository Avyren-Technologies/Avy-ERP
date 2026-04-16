TRANSCRIBE_HANDWRITING = """This image contains a handwritten annotation or note on a document page.

Please:
1. Transcribe the handwritten text as accurately as possible
2. Rate your confidence in the transcription (0.0 to 1.0)
3. Describe the type of annotation (margin note, correction, checkmark, arrow, circle, etc.)

Return JSON:
```json
{{
  "transcription": "the handwritten text",
  "confidence": 0.75,
  "annotation_type": "margin_note|correction|checkmark|arrow|circle|underline|strikethrough|other",
  "notes": "any additional observations about the annotation"
}}
```

If the handwriting is completely illegible, return confidence 0.0 and transcription as empty string."""


def get_transcribe_prompt(provider: str) -> str:
    if provider == "anthropic":
        return f"<task>\n{TRANSCRIBE_HANDWRITING}\n</task>\n<output_format>JSON only</output_format>"
    return TRANSCRIBE_HANDWRITING
