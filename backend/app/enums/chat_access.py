from enum import StrEnum


class ChatAccessStatus(StrEnum):
    INVITED = "invited"
    JOINED = "joined"
    LEFT = "left"
    KICKED = "kicked"
