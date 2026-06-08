# Spec: `retrieve()`

**File:** `retriever.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user's natural language query, find the most relevant chunks from the vector store using semantic similarity search. Return them ranked by relevance so that `generate_response()` can use them as context.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's natural language question |
| `n_results` | `int` | Maximum number of chunks to return (default: `N_RESULTS` from `config.py`) |

**Output:** `list[dict]`

Each dict in the returned list must contain exactly these keys:

| Key | Type | Description |
|-----|------|-------------|
| `"text"` | `str` | The chunk text |
| `"game"` | `str` | The game name this chunk came from |
| `"distance"` | `float` | Cosine distance score — lower means more similar to the query |

Results should be ordered from most to least relevant (lowest to highest distance). Returns an empty list `[]` if the collection contains no documents.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Query approach

*Describe how you will use `_collection.query()` to find relevant chunks. What arguments will you pass, and why?*

```
Must pass the user query, n the number of chunks we want returned, and the type of data struct we want the data return as. So we are going to have params:
- 'query'
- 'n' for the number of chunks
- 'list' that contains {`"documents"`, `"metadatas"`, `"distances"`}
```

---

### Return structure

*Sketch out what one item in your return list looks like as a concrete example. Where does each field come from in the query results?*

```
It will return a list with items that each have a chunk of text(str), game name(str), distance value.
All these values were given to our Chroma database to safe. E.g.:
- {"text": "When a 7 is rolled, no resources are produced...", "game": "Catan", "distance": 0.121412}
```

---

### Handling the nested result structure

*`_collection.query()` returns nested lists. Describe what index you need to access to get the actual list of results for a single query, and why the nesting exists.*

```
Since a list-per-query is returned we have to access them with an index (0). 
docs = list_q["documents"][0]
metas = list_q["metadatas"][0]
dists = list_q["distances"][0]

Then we can create an item like {"text": docs[i], "game": metas[i]l, "distance": dists[i]}
```

---

### Relevance threshold

*Will you filter out results above a certain distance score, or return all `n_results` regardless of how relevant they are? What are the tradeoffs of each approach?*

```
Relevance threshold: We will not apply a hard distance cutoff in `retrieve()`. Returning the top `n_results` keeps retrieval simple and ensures the generator always has context to work with. If needed, a confidence warning can be added later in `generate_response()`.
```

---

### Edge cases

*How does your implementation behave when: (a) the collection is empty, (b) the query matches no chunks well, (c) the query matches chunks from multiple games?*

```
(a) If the collection is empty, `retrieve()` returns an empty list `[]`. This signals that no rule books have been loaded yet, and `generate_response()` can use that to tell the user the system has no context available.

(b) If the collection has documents but the query does not match any chunk strongly, `retrieve()` will still return the top `n_results` results sorted by distance. The downstream generator can decide whether the match quality is too weak to answer confidently.

(c) If the query matches chunks from multiple games, `retrieve()` will return the best chunks across all games. This is expected behavior because the query may be ambiguous or overlap multiple rule books.

```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**Test query and top result returned:**

```
Query: [your test query]
Top result game: [game name]
Distance score: [score]
Does it make sense? [yes / no / explain]
```

**One thing about the query results that surprised you:**

```
[your answer here]
```
