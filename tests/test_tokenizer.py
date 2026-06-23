import pytest
from src.tokenizer.tokenizer import Tokenizer

def test_basic_tokenization():
    tokenizer = Tokenizer(use_stemming=False)
    result = tokenizer.tokenize("Hello World!")
    assert result == ["hello", "world"]

def test_stopword_removal():
    tokenizer = Tokenizer(use_stemming=False)
    result = tokenizer.tokenize("This is a test")
    assert "this" not in result
    assert "is" not in result
    assert "a" not in result
    assert "test" in result

def test_min_length_filter():
    tokenizer = Tokenizer(use_stemming=False)
    result = tokenizer.tokenize("I am ok")
    assert "i" not in result
    assert "ok" in result

def test_stemming():
    tokenizer = Tokenizer(use_stemming=True)
    result = tokenizer.tokenize("Transformers are ALL you need!")
    assert "transform" in result
    assert "need" in result
    assert "are" not in result
    assert "you" not in result

def test_empty_input():
    tokenizer = Tokenizer()
    result = tokenizer.tokenize("")
    assert result == []

def test_punctuation_only():
    tokenizer = Tokenizer()
    result = tokenizer.tokenize("!@#$%^&*()")
    assert result == []
