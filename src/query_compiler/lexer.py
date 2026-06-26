"""
Lexer for boolean query DSL.
Tokenizes queries like: "transformer AND attention NOT survey"
Phase 1 of query compiler pipeline.
"""
from dataclasses import dataclass
from enum import Enum, auto
import re


class TType(Enum):
    """Token types for boolean query language."""
    TERM = auto()
    PHRASE = auto()  # "exact phrase"
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()


@dataclass
class Token:
    """Query token with type and value."""
    type: TType
    value: str = ""

    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}')" if self.value else f"Token({self.type.name})"


def tokenize(query: str) -> list[Token]:
    """
    Tokenize boolean query into Token stream.
    
    Examples:
        "neural network" -> [TERM(neural), TERM(network), EOF]
        "neural AND network" -> [TERM(neural), AND, TERM(network), EOF]
        '"exact phrase"' -> [PHRASE(exact phrase), EOF]
    """
    tokens = []
    i = 0
    q = query.strip()

    while i < len(q):
        # Skip whitespace
        if q[i].isspace():
            i += 1
            continue

        # Phrase literal
        if q[i] == '"':
            try:
                j = q.index('"', i + 1)
                tokens.append(Token(TType.PHRASE, q[i + 1:j]))
                i = j + 1
            except ValueError:
                # Unclosed quote - treat as regular term
                tokens.append(Token(TType.TERM, '"'))
                i += 1
            continue

        # Parentheses
        if q[i] == '(':
            tokens.append(Token(TType.LPAREN))
            i += 1
            continue
        if q[i] == ')':
            tokens.append(Token(TType.RPAREN))
            i += 1
            continue

        # Word token
        m = re.match(r'\w+', q[i:])
        if m:
            word = m.group()
            # Check for operators (case-insensitive)
            match word.upper():
                case "AND":
                    tokens.append(Token(TType.AND))
                case "OR":
                    tokens.append(Token(TType.OR))
                case "NOT":
                    tokens.append(Token(TType.NOT))
                case _:
                    tokens.append(Token(TType.TERM, word.lower()))
            i += len(word)
        else:
            # Unknown character - skip
            i += 1

    tokens.append(Token(TType.EOF))
    return tokens
