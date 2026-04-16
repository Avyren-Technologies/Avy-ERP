CLASSIFY_DIFFERENCE = """You are classifying a detected difference between two document versions.

The difference is:
- Type: {difference_type}
- Before (Version A): {value_before}
- After (Version B): {value_after}
- Context: {context}

Classify the significance of this difference:

- **material**: Differences in specifications, tolerances, quantities, materials, dimensions, or any value that would affect manufacturing or pricing
- **substantive**: Differences in requirements text, scope descriptions, terms, or conditions that alter meaning
- **cosmetic**: Formatting, whitespace, pagination, or stylistic differences with no impact on meaning
- **uncertain**: Cannot confidently classify; requires reviewer verification

Also rate your confidence from 0.0 to 1.0.

Return JSON:
```json
{{
  "significance": "material|substantive|cosmetic|uncertain",
  "confidence": 0.95,
  "reasoning": "Brief explanation of classification"
}}
```"""


CLASSIFY_DIFFERENCE_ANTHROPIC = f"""<task>
{CLASSIFY_DIFFERENCE}
</task>
<output_format>JSON only</output_format>"""


def get_classify_prompt(
    provider: str,
    difference_type: str,
    value_before: str,
    value_after: str,
    context: str,
) -> str:
    template = CLASSIFY_DIFFERENCE_ANTHROPIC if provider == "anthropic" else CLASSIFY_DIFFERENCE
    return template.format(
        difference_type=difference_type,
        value_before=value_before or "(none)",
        value_after=value_after or "(none)",
        context=context or "(no surrounding context)",
    )
