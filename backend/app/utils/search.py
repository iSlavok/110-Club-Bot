import re

_SPACES = re.compile(r"\s+")


# Mirrors the users.search_text expression, see app/models/user.py.
def normalize_search_query(query: str) -> str:
    return _SPACES.sub(" ", query.strip().lower().replace("ё", "е"))
