from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrentBlockRow:
    club_title: str
    block_title: str
