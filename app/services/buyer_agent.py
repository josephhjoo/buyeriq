"""
The core agent: takes a target company description, uses Claude with
web search to research likely buyers, and returns a structured list
with confidence scores.
"""
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
MAX_SEARCHES = 10

SYSTEM_PROMPT = """You are an M&A buyer research analyst working for a boutique investment bank.

Given a target company being sold, your job is to identify the most likely buyers — both strategic acquirers (companies in the same or adjacent industries) and financial buyers (private equity firms whose mandate fits the deal).

For each buyer, you must also identify the most relevant contact person — typically a Managing Director, Partner, or Principal at a PE firm, or a VP/Head of Corporate Development at a strategic acquirer.

USE WEB SEARCH to find real, current information. Do not invent firms or people. Every contact must come from a source you actually found.

CONFIDENCE SCORING — for each contact, assign a confidence score (0-100) based on:
- 80-100: Found on the firm's official website or a recent (within 12 months) press release / deal announcement
- 60-79: Found on LinkedIn or a reputable industry publication, appears current
- 40-59: Found but information may be outdated, or the person's exact role relevance is uncertain
- 0-39: Weak source, inferred, or possibly no longer at the firm

Be honest about confidence. A shorter list of high-confidence contacts is more valuable than a long list of guesses.

OUTPUT FORMAT — your final message must be ONLY a JSON object, no preamble, no markdown fences:
{
  "buyers": [
    {
      "firm_name": "...",
      "buyer_type": "strategic" or "financial",
      "rationale": "1-2 sentences on why this firm would want this deal",
      "contact_name": "..." or null if none found,
      "contact_title": "..." or null,
      "confidence": 0-100,
      "confidence_reasoning": "1 sentence on why this confidence level",
      "source_urls": ["...", "..."]
    }
  ],
  "research_notes": "1-3 sentences on overall search quality and any caveats"
}"""


def research_buyers(target: dict) -> dict:
    """
    Run the buyer research agent for a target company.

    target = {
        "name": str,
        "industry": str,
        "revenue_m": float,
        "geography": str,
        "description": str,
        "num_buyers": int,
    }
    """
    # Test mode: set BUYERIQ_TEST_MODE=1 to skip the paid API call and return
    # canned data. Useful for testing the save/display/export flow for free.
    if os.getenv("BUYERIQ_TEST_MODE") == "1":
        return _fake_result()

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    num_buyers = target.get("num_buyers", 10)

    user_prompt = f"""Research potential buyers for this sell-side M&A engagement:

TARGET COMPANY:
- Name: {target.get('name', 'Confidential')}
- Industry: {target.get('industry')}
- Revenue: ${target.get('revenue_m')}M
- Geography: {target.get('geography')}
- Description: {target.get('description')}

Find approximately {num_buyers} potential buyers — a mix of strategic acquirers and PE firms with a relevant mandate. For each, identify the best contact person and score your confidence.

Search the web for: PE firms investing in this industry and size range, recent comparable acquisitions (the acquirers are likely buyers again), and corporate development contacts at strategic acquirers.

Remember: final message must be ONLY the JSON object."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": MAX_SEARCHES,
        }],
    )

    # The response contains a mix of text, web search tool use, and
    # search result blocks. The final JSON lives in the text blocks —
    # concatenate them all and extract the JSON object.
    text_parts = [block.text for block in response.content if block.type == "text"]
    full_text = "\n".join(text_parts).strip()

    return _parse_json(full_text)


def _parse_json(text: str) -> dict:
    """Extract the JSON object from the model's response, tolerating
    markdown fences or stray text around it."""
    # Strip markdown fences if present
    cleaned = text.replace("```json", "").replace("```", "").strip()

    # Find the outermost JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in response: {text[:500]}")

    try:
        result = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}\nResponse was: {text[:500]}")

    if "buyers" not in result:
        raise ValueError("Response JSON missing 'buyers' key")

    # Sort by confidence, highest first
    result["buyers"].sort(key=lambda b: b.get("confidence", 0), reverse=True)
    return result


def _fake_result() -> dict:
    """Canned data for free testing of the save/display/export flow."""
    return {
        "buyers": [
            {
                "firm_name": "TEST — PremiStar / Partners Group",
                "buyer_type": "strategic",
                "rationale": "Test entry. One of the most active acquirers in the sector with a stated geographic expansion mandate.",
                "contact_name": "Test Contact",
                "contact_title": "Vice President, M&A",
                "confidence": 92,
                "confidence_reasoning": "Test entry — high confidence example.",
                "source_urls": ["https://example.com/source1", "https://example.com/source2"],
            },
            {
                "firm_name": "TEST — Broadwing Capital",
                "buyer_type": "financial",
                "rationale": "Test entry. Lower-middle-market PE firm targeting family-owned businesses at this revenue size.",
                "contact_name": "Test Partner",
                "contact_title": "Managing Partner",
                "confidence": 64,
                "confidence_reasoning": "Test entry — medium confidence example.",
                "source_urls": ["https://example.com/source3"],
            },
            {
                "firm_name": "TEST — Caymus Equity",
                "buyer_type": "financial",
                "rationale": "Test entry. Relevant mandate but no verifiable contact found.",
                "contact_name": None,
                "contact_title": None,
                "confidence": 32,
                "confidence_reasoning": "Test entry — low confidence, no contact.",
                "source_urls": ["https://example.com/source4"],
            },
        ],
        "research_notes": "TEST MODE — this is canned data, no API call was made. Set BUYERIQ_TEST_MODE=0 to use the real agent.",
    }