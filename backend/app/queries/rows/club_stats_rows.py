from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlockMemberCountsRow:
    members: int
    members_with_tg: int
