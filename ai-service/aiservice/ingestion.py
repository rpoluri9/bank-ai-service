"""Document ingestion: parsing, chunking, and TF-IDF indexing.

Pure Python standard library only. No AI libraries, no API keys, no network:
the whole RAG pipeline runs offline on this machine.
"""

import math
import re
from collections import Counter

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "for", "with", "and", "or", "by", "at", "as",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "my", "your", "his", "her", "our", "their", "do", "does",
    "did", "can", "could", "will", "would", "should", "how", "what", "when",
    "where", "why", "which", "who", "is", "am", "an",
}

TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def tokenize(text):
    """Lowercase alphanumeric tokens with stopwords removed."""
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def chunk_text(text, max_chars=800):
    """Split a document into chunks on sentence boundaries.

    Sentences are grouped until the chunk would exceed max_chars, so each
    chunk stays small enough to be a useful retrieval unit.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, current = [], ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip() if current else sentence
    if current:
        chunks.append(current)
    return chunks


class TfIdfIndex:
    """A small TF-IDF index over document chunks.

    This plays the role of the 'embedding-style indexing' step: each chunk
    becomes a vector, and retrieval ranks chunks by cosine similarity to the
    question vector. The vectors are term-frequency based instead of neural
    embeddings, which is why the service needs no model downloads or keys.
    """

    def __init__(self, chunks):
        """chunks: list of dicts with keys doc_id, title, text."""
        self.chunks = chunks
        self.doc_count = len(chunks)
        self.df = Counter()
        self.vectors = []
        tokenized = []
        for chunk in chunks:
            tokens = tokenize(chunk["text"])
            tokenized.append(tokens)
            for term in set(tokens):
                self.df[term] += 1
        for tokens in tokenized:
            tf = Counter(tokens)
            vector = {}
            for term, count in tf.items():
                idf = math.log((1 + self.doc_count) / (1 + self.df[term])) + 1.0
                vector[term] = (1 + math.log(count)) * idf
            norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
            self.vectors.append({t: v / norm for t, v in vector.items()})

    def search(self, query, top_k=3):
        """Return the top_k chunks ranked by cosine similarity to the query."""
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        q_tf = Counter(query_tokens)
        q_vec = {}
        for term, count in q_tf.items():
            idf = math.log((1 + self.doc_count) / (1 + self.df.get(term, 0))) + 1.0
            q_vec[term] = (1 + math.log(count)) * idf
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        q_vec = {t: v / q_norm for t, v in q_vec.items()}

        scored = []
        for chunk, vector in zip(self.chunks, self.vectors):
            score = sum(q_vec.get(term, 0.0) * weight for term, weight in vector.items())
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [{"score": round(score, 4), **chunk} for score, chunk in scored[:top_k]]


def build_index(documents):
    """Ingest documents: parse -> chunk -> index. Returns a TfIdfIndex."""
    chunks = []
    for doc in documents:
        for chunk_text_piece in chunk_text(doc["text"]):
            chunks.append({
                "doc_id": doc["id"],
                "title": doc["title"],
                "text": chunk_text_piece,
            })
    return TfIdfIndex(chunks)
