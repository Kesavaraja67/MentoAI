"""
chunker.py — Sentence-level stream chunker for low-latency voice synthesis and subtitles.
"""
import re
from typing import Generator, Tuple

SENTENCE_END = re.compile(r"([.!?]+(?:\s+|$))")


class SentenceChunker:
    def __init__(self):
        self.buffer = ""
        self.sentence_count = 0

    def feed(self, token: str) -> Generator[Tuple[str, str], None, None]:
        """
        Feeds a single streaming token or word.
        Yields (sentence_id, complete_sentence) whenever a sentence boundary is crossed.
        """
        self.buffer += token
        parts = SENTENCE_END.split(self.buffer)
        # When split matches, parts has [sentence, delimiter, sentence, delimiter, remaining]
        if len(parts) > 1:
            complete_sentences = ""
            for i in range(0, len(parts) - 1, 2):
                sentence = (parts[i] + parts[i + 1]).strip()
                if sentence:
                    self.sentence_count += 1
                    sentence_id = f"s_{self.sentence_count}"
                    yield sentence_id, sentence
            self.buffer = parts[-1]

    def flush(self) -> Generator[Tuple[str, str], None, None]:
        """Flushes any remaining text in the buffer."""
        remaining = self.buffer.strip()
        if remaining:
            self.sentence_count += 1
            sentence_id = f"s_{self.sentence_count}"
            self.buffer = ""
            yield sentence_id, remaining
