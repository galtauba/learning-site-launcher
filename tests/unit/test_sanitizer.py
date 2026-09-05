from launcher.logging.sanitizer import sanitize
def test_hides_url_credentials():
    assert "secret" not in sanitize("https://me:secret@github.com/a/b")
