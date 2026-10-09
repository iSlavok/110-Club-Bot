from app import texts


def test_admin_panel_link() -> None:
    text = texts.auth.admin_panel_link("https://club.example.com/?a=1&b=2")

    assert "https://club.example.com/?a=1&amp;b=2" in text


def test_admin_panel_link_without_url() -> None:
    assert texts.auth.admin_panel_link(None) == texts.auth.ADMIN_PANEL_URL_MISSING
