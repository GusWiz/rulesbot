from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved rule chunks.

    TODO — Milestone 3:

    `retrieved_chunks` is the list returned by retrieve(). Each item is a dict:
      - "text"     : the chunk text
      - "game"     : the game name
      - "distance" : similarity score (you can use this to filter weak matches)

    Before writing code, talk through these with your group:
      - How will you format the chunks into a context block for the prompt?
      - What instructions will stop the model from answering beyond what the
        rules say? (Grounding is the whole point — a confident wrong answer
        is worse than an honest "I don't know.")
      - How will you surface which game each answer comes from?

    Your response should:
      1. Answer using only the retrieved context — not the model's general knowledge
      2. Make clear which game the answer comes from
      3. Say so clearly when the answer isn't in the loaded rules

    Return the response as a plain string.
    """
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded rule books. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    # Format chunks for LLM
    filtered_chunk = []
    for chunk in retrieved_chunks:
        if chunk.get("distance", 0) <= 0.7:
            filtered_chunk.append(chunk)
    
    # Check filtered chunks
    if not filtered_chunk:
        return "I am sorry, but the loaded rules do not contain information to answer your question"
    
    xml_elements = ["<retrieved_context>"]
    for chunk in filtered_chunk:
        game_name = chunk.get("game", "unknown game")
        text = chunk.get("text", "").strip()
        xml_elements.append(f"<chunk gameName={game_name}>\n{text}\n</chunk>")
    xml_elements.append("</retrieved_context>")

    formatted_xml_context = "\n".join(xml_elements)
    system_prompt = (
        "You are a strict QA assistant. Answer the user's question using ONLY the text provided "
        "within the <retrieved_context> XML tags. Do not use your own pre-trained knowledge or "
        "make assumptions. If the text does not contain the answer, you must output the exact "
        "fallback string: [I am sorry, but the loaded rules do not contain information to answer "
        "your question.]. Do not speculate.\n\n"
        "Every answer must explicitly state the game it belongs to. Format the output by prefixing "
        "the answer with the game name in brackets, like this: [Game Name] - Your answer here....")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{formatted_xml_context}\n\nQuery: {query}"}
    ]

    try:
        chat_completion = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.0, # Zero temperature ensures maximum strict adherence to the context
        )

        response_text = chat_completion.choices[0].message.content.strip()
        return response_text
    
    except Exception as e:
        return f"An error occured when calling the LLM model error: {str(e)}"