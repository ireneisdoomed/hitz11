from hitz11.crawler import parse_letter_page


def test_parse_letter_page_extracts_word_and_text():
    html = """
    <html><body>
      <div id="contenido2020">
        <dl>
          <dt><div class="palabras">Obito</div></dt>
          <dd class="dd">"Fallecimiento". OBI = "fosa" + TU = "depositar".</dd>
        </dl>
      </div>
    </body></html>
    """

    result = parse_letter_page(html, "https://example.test/o.html")

    assert len(result) == 1
    assert result[0].word == "Obito"
    assert "OBI" in result[0].etymology_text
    assert result[0].definition == "Fallecimiento"
