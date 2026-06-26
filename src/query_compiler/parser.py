"""
Recursive-descent parser for boolean queries.
Compiles token stream into Abstract Syntax Tree (AST).
Phase 2 of query compiler pipeline.

Grammar:
    expr     → or_expr
    or_expr  → and_expr (OR and_expr)*
    and_expr → not_expr (AND? not_expr)*
    not_expr → NOT primary | primary
    primary  → TERM | PHRASE | '(' expr ')'
"""
from .lexer import tokenize, TType, Token


class ASTNode:
    """Base class for AST nodes."""
    pass


class TermNode(ASTNode):
    """Leaf node: single term."""
    def __init__(self, term: str):
        self.term = term

    def __repr__(self):
        return f"TERM({self.term})"

    def to_dict(self):
        return {"type": "term", "value": self.term}


class PhraseNode(ASTNode):
    """Leaf node: exact phrase."""
    def __init__(self, phrase: str):
        self.phrase = phrase

    def __repr__(self):
        return f'PHRASE("{self.phrase}")'

    def to_dict(self):
        return {"type": "phrase", "value": self.phrase}


class BinaryNode(ASTNode):
    """Binary operator: AND, OR."""
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

    def to_dict(self):
        return {
            "type": "binary",
            "op": self.op,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


class NotNode(ASTNode):
    """Unary NOT operator."""
    def __init__(self, child: ASTNode):
        self.child = child

    def __repr__(self):
        return f"NOT({self.child})"

    def to_dict(self):
        return {"type": "not", "child": self.child.to_dict()}


class QueryParser:
    """
    Recursive-descent parser for boolean queries.
    Implements standard precedence: OR < AND < NOT.
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        """Look at current token without consuming."""
        return self.tokens[self.pos]

    def consume(self, ttype: TType) -> Token:
        """Consume token of expected type, raise if mismatch."""
        t = self.tokens[self.pos]
        if t.type != ttype:
            raise SyntaxError(f"Expected {ttype.name}, got {t.type.name} at position {self.pos}")
        self.pos += 1
        return t

    def parse(self) -> ASTNode:
        """Entry point: parse full expression."""
        ast = self._expr()
        if self.peek().type != TType.EOF:
            raise SyntaxError(f"Unexpected token after expression: {self.peek()}")
        return ast

    def _expr(self) -> ASTNode:
        """expr → or_expr"""
        return self._or_expr()

    def _or_expr(self) -> ASTNode:
        """or_expr → and_expr (OR and_expr)*"""
        node = self._and_expr()
        while self.peek().type == TType.OR:
            self.pos += 1
            node = BinaryNode("OR", node, self._and_expr())
        return node

    def _and_expr(self) -> ASTNode:
        """and_expr → not_expr (AND? not_expr)*"""
        node = self._not_expr()
        # Implicit AND: "neural network" = "neural AND network"
        # Also handle explicit AND and NOT (since NOT binds tighter than AND)
        while self.peek().type in (TType.AND, TType.TERM, TType.PHRASE, TType.LPAREN, TType.NOT):
            if self.peek().type == TType.AND:
                self.pos += 1
            node = BinaryNode("AND", node, self._not_expr())
        return node

    def _not_expr(self) -> ASTNode:
        """not_expr → NOT primary | primary"""
        if self.peek().type == TType.NOT:
            self.pos += 1
            return NotNode(self._primary())
        return self._primary()

    def _primary(self) -> ASTNode:
        """primary → TERM | PHRASE | '(' expr ')'"""
        t = self.peek()

        if t.type == TType.TERM:
            self.pos += 1
            return TermNode(t.value)

        if t.type == TType.PHRASE:
            self.pos += 1
            return PhraseNode(t.value)

        if t.type == TType.LPAREN:
            self.consume(TType.LPAREN)
            node = self._expr()
            self.consume(TType.RPAREN)
            return node

        raise SyntaxError(f"Unexpected token in primary: {t}")


def compile_query(query_str: str) -> ASTNode:
    """
    Entry point: compile query string to AST.
    
    Examples:
        "neural network" -> AND(TERM(neural), TERM(network))
        "neural AND (network OR system)" -> AND(TERM(neural), OR(TERM(network), TERM(system)))
        "transformer NOT survey" -> AND(TERM(transformer), NOT(TERM(survey)))
    """
    tokens = tokenize(query_str)
    parser = QueryParser(tokens)
    return parser.parse()
