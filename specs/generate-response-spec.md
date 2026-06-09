# Spec: `generate_response()`

**File:** `generator.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user query and a list of retrieved rule chunks, generate a response that directly answers the question using only the retrieved text as context. The response must be grounded — it should not draw on the model's general knowledge of board games, only on what was retrieved.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's original question |
| `retrieved_chunks` | `list[dict]` | Ranked list of chunks from `retrieve()`, each with `"text"`, `"game"`, and `"distance"` |

**Output:** `str`

A plain string containing the response to show the user. The response should:
- Answer the question using only the retrieved rule text
- Identify which game the answer comes from
- Acknowledge clearly when the answer is not found in the loaded rules

Returns a fallback string (not an error) when `retrieved_chunks` is empty.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Context formatting

*How will you format the retrieved chunks before passing them to the LLM? Describe the structure — not the code. Consider: will you label chunks by game? Include distance scores? Separate chunks with delimiters?*

```
Note: Common delimiters include: 
- Newline characters (\n\n)
- Dash lines (---)
-XML-style tags (e.g., <chunk> ... </chunk>)

The retrieved chunks will be aggregated into a single context string using structured XML-style delimiters to isolate each text segment. 

Each segment will be wrapped in a `<chunk>` tag containing a `game` attribute to explicitly pass the source metadata to the LLM. Distance scores will be intentionally omitted from the prompt text to prevent token waste and numerical confusion, relying instead on the inherent ordering of the list.

Format Structure:
<retrieved_context>
<chunk game="Game Name A">
Text chunk content goes here...
</chunk>
<chunk game="Game Name B">
Text chunk content goes here...
</chunk>
</retrieved_context>
```

---

### System prompt — grounding instruction

*Write the exact system prompt instruction you will use to prevent the model from answering beyond the retrieved text. This is the most important design decision in this function.*

```
You are a strict QA assistant. Answer the user's question using ONLY the text provided within the <retrieved_context> XML tags. Do not use your own pre-trained knowledge or make assumptions. If the text does not contain the answer, you must output the exact fallback string: [I am sorry, but the loaded rules do not contain information to answer your question.]. Do not speculate.
```

---

### System prompt — citation instruction

*Write the exact instruction you will use to tell the model to identify which game its answer comes from.*

```
Every answer must explicitly state the game it belongs to. Format the output by prefixing the answer with the game name in brackets, like this: [Game Name] - Your answer here....
```

---

### Fallback behavior

*What should the response say when the answer isn't found in the loaded rule books? Write the exact fallback message.*

```
I am sorry, but the loaded rules do not contain information to answer your question.
```

---

### Handling low-relevance chunks

*`retrieved_chunks` may include chunks with high distance scores (weak relevance). Will you filter these out before building context, pass them all in, or handle them another way? What are the tradeoffs?*

```
We are going to omit any chunks from the relevant chunks that distance value is greater than 0.7.
```

---

### Message structure

*Describe how you will structure the messages list for the API call — what goes in the system message vs. the user message?*

```
The structure of the message list for the API call is going to follow:
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": f"{formatted_xml_context}\n\nQuery: {query}"}
]

```

---

## Implementation Notes

*Fill this in after implementing and testing.*

**Test query and response:**

```
Query: [your test query]
Response: [abbreviated response]
Correctly grounded? [yes / no]
Cited the right game? [yes / no]
```

**One thing you changed from your original spec after seeing the actual output:**

```
[your answer here]
```
