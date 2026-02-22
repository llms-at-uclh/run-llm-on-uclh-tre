# ─────────────────────────────────────────────────────────────────────────────
# prompt.py — Edit this file to change what the model is asked to do.
# ─────────────────────────────────────────────────────────────────────────────
#
# HOW TO EDIT:
#   1. Change SYSTEM_PROMPT to give the model its overall role/instructions.
#   2. Change the user message in build_messages() to set the per-row task.
#      Use {text} anywhere you want the row's text to be inserted.
#
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful clinical assistant.
Your task is to read clinical notes and produce a concise, accurate summary.
Always be factual. Never invent information not present in the note."""


def build_messages(text: str) -> list[dict]:
    """
    Build the chat messages for a single row.

    Parameters
    ----------
    text : str
        The value from the 'text' column for this row.

    Returns
    -------
    list[dict]
        A list of chat messages in the format expected by the model.
        Add more turns (e.g. few-shot examples) by inserting additional
        {"role": "user"/"assistant", "content": "..."} dicts before the
        final user message.
    """
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Please summarise the following clinical note:\n\n{text}"},
    ]
