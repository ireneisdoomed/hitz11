from hitz11.models import Entry
from hitz11.telegram_client import compose_message


def test_compose_message_truncates_long_etymology():
    entry = Entry(
        id=1,
        word="Obito",
        definition="Fallecimiento",
        etymology_text="x" * 5000,
        origin_key="basque",
        language="es",
        source_url="https://example.test/o.html",
    )

    text = compose_message(entry, "daily")

    assert "Palabra del dia" in text
    assert len(text) <= 4096
    assert text.endswith("#Hitz11 #Etimologia")
