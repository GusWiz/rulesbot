from ingest import chunk_document

def test_empty_text_return_empty_list():
    assert chunk_document("", "Test Game") == []

def test_chunking_basic_behavior():
    text = "x" * 700 # text size of the "notes"
    game = "My Game"
    chunks = chunk_document(text, game)

    # Check that there are 3 chunks with a prefix derived form game name
    assert len(chunks) == 3
    assert [c["chunk_id"] for c in chunks] == ["my_game_0", "my_game_1", "my_game_2"]

    for c in chunks:
        assert c["game"] == game
        assert isinstance(c["text"], str) and len(c["text"]) >= 50