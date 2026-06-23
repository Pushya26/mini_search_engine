from dataclasses import dataclass

@dataclass
class Paper:
    doc_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    published: str
    pdf_url: str
    references: list[str]
