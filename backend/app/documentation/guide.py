from dataclasses import dataclass


@dataclass(frozen=True)
class GuideItem:
    text: str
    evidence: list[str]


@dataclass(frozen=True)
class GuideSection:
    title: str
    items: list[GuideItem]


@dataclass(frozen=True)
class Guide:
    title: str
    sections: list[GuideSection]
    evidence: list[str]
    assumptions: list[str]
