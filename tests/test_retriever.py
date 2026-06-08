import retriever

class DummyCollectionEmpty:
    def count(self):
        return 0
    
def test_empty_collection_returns_empty_list(monkeypatch):
    # Ensure retrieve() returns [] when the vector store is empty.
    monkeypatch.setattr(retriever, "_collection", DummyCollectionEmpty())
    assert retriever.retrieve("anything") == []


class DummyCollection:
    def count(self):
        return 2
    
    def query(self, query_texts, n_results, include):
        # API returns nested lists (one inner list per query).
        return {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"game": "Catan"}, {"game": "Uno"}]],
            "distances": [[0.1, 0.2]],
        }
    
def test_retrieve_formats_results(monkeypatch):
    # Verify retrieve() converts Chroma result lists into a list of dicts.
    monkeypatch.setattr(retriever, "_collection", DummyCollection())
    res = retriever.retrieve("roll a 7", n_results=2)
    assert res == [
        {"text": "doc1", "game": "Catan", "distance": 0.1},
        {"text": "doc2", "game": "Uno", "distance": 0.2},
    ]

class DummyCollectionMissingMeta:
    def count(self):
        return 1

    def query(self, query_texts, n_results, include):
        return {
            "documents": [["only doc"]],
            "metadatas": [[{}]],  # missing "game"
            "distances": [[0.5]],
        }


def test_handles_missing_game_key(monkeypatch):
    # Ensure retrieve() handles missing metadata keys gracefully (game -> None).
    monkeypatch.setattr(retriever, "_collection", DummyCollectionMissingMeta())
    res = retriever.retrieve("query", n_results=1)
    assert res == [{"text": "only doc", "game": None, "distance": 0.5}]