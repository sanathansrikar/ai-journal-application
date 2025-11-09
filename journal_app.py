import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import traceback
import re

# ------------------- SETUP -------------------
load_dotenv()
st.set_page_config(page_title="AI Journal", page_icon="📔", layout="centered")

if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ Missing GEMINI_API_KEY or GOOGLE_API_KEY in .env file.")
    st.stop()

# ------------------- CLIENT CACHE -------------------
@st.cache_resource
def get_client(api_key: str):
    """Initialize genai client once per session."""
    return genai.Client(api_key=api_key)

# ------------------- RETRY HANDLER -------------------
def safe_generate(client, model, contents, config, retries=3):
    """Retries on 429 or transient errors (silently)."""
    for attempt in range(retries):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                time.sleep((attempt + 1) * 5)
            else:
                raise
    raise RuntimeError("Failed after multiple retries due to rate limits.")

# ------------------- JOURNAL TOOLS -------------------
add_entry_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="add_journal_entry",
            description="Add a new journal entry.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "content": types.Schema(type="STRING"),
                    "category": types.Schema(type="STRING"),
                    "tags": types.Schema(type="ARRAY", items=types.Schema(type="STRING")),
                },
                required=["content", "category"],
            ),
        )
    ]
)

query_entries_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="query_journal_entries",
            description="Search journal entries.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "category": types.Schema(type="STRING"),
                    "search_query": types.Schema(type="STRING"),
                },
            ),
        )
    ]
)

# ------------------- FUNCTIONS -------------------
def add_journal_entry(content, category, tags=None):
    entry = {
        "id": len(st.session_state.journal_entries) + 1,
        "content": content.strip(),
        "category": category.strip().lower(),
        "tags": tags or [],
        "timestamp": datetime.now().isoformat(),
    }
    st.session_state.journal_entries.append(entry)
    return {"success": True, "message": f"Added {category} entry."}

def query_journal_entries(category="all", search_query=None):
    entries = st.session_state.journal_entries
    if category != "all":
        entries = [e for e in entries if e["category"].lower() == category.lower()]
    if search_query:
        entries = [e for e in entries if search_query.lower() in e["content"].lower()]
    if not entries:
        return {"result": "No entries found."}

    formatted = "\n".join(
        f"- [{e['category']}] {e['content']} ({datetime.fromisoformat(e['timestamp']).strftime('%Y-%m-%d %H:%M')})"
        for e in entries
    )
    return {"result": formatted}

def execute_function(function_call):
    name = function_call.name
    args = dict(function_call.args)
    if name == "add_journal_entry":
        return add_journal_entry(**args)
    elif name == "query_journal_entries":
        return query_journal_entries(**args)
    return {"error": "Unknown function"}

def get_system_instruction():
    return """You are a helpful personal journal assistant.
Classify the user's message as one of: ["add_journal_entries", "query_journal_entries", "irrelevant"].

You can:
- Add entries when the user mentions tasks, reminders, notes, thoughts, recommendations, or shopping lists.
- Use the category exactly as mentioned (e.g., "shoppinglist", "reminder", etc.)
- Never ask for clarification — infer intent.
- Retrieve entries when the user asks for lists, reminders, or what they logged earlier.

You must always use the functions when the user asks about:
- showing, listing, displaying, or viewing logs
- shopping lists or items to buy
- any mention of tasks, reminders, or notes

Valid categories: reminder, note, thought, recommendation, shoppinglist.

Restrictions:
- Only handle journaling tasks.
- If the user message is found to be irrelevant to journaling, decline politely.
- Decline non-journal queries politely.

Keep responses short and natural."""

# ------------------- CONTEXT DECIDER -------------------
def should_include_context(user_message: str) -> bool:
    keywords = ["what", "list", "show", "remind", "buy", "task", "to-do", "remember", "summary", "note"]
    return any(k in user_message.lower() for k in keywords)

# ------------------- BULK ENTRY DETECTOR -------------------
def parse_bulk_entries(text: str):
    pattern = r"(\w+)\s+—\s+[\d\-\:\s]+(.+)"
    matches = re.findall(pattern, text)
    return [{"category": c.strip(), "content": x.strip(), "tags": []} for c, x in matches]

# ------------------- PROCESS MESSAGE -------------------
def process_message(user_message: str) -> str:
    try:
        client = get_client(api_key)
        text = user_message.strip().lower()

        # --- 1️⃣ Bulk entry paste handling ---
        bulk_entries = parse_bulk_entries(user_message)
        if bulk_entries:
            for entry in bulk_entries:
                add_journal_entry(entry["content"], entry["category"], entry["tags"])
            return f"✅ Added {len(bulk_entries)} journal entries successfully."
        
        # ---  2️⃣ Handle manual list queries before LLM ---
        if re.search(r"(what|show|list|display).*(shopping|buy|grocer|item)", text) and not re.search(r"(add|note)", text):
            result = query_journal_entries("shoppinglist")
            return result["result"]

        if re.search(r"(what|show|list|display).*(remind|task|todo|to-do|event)", text) and not re.search(r"(add|note)", text):
            result = query_journal_entries("reminder")
            return result["result"]

        if re.search(r"(what|show|list|display).*(note|thought|idea|recommendation)", text) and not re.search(r"(add|note)", text):
            result = query_journal_entries("note")
            return result["result"]
        
        if re.search(r"(remind|appointment|meeting|schedule|event)", text) and not re.search(r"(add|note)", text):
                if re.search(r"(do|does|did|any|what|show|list|display|have|are there)", text):
                    result = query_journal_entries("reminder")
                    return result["result"]


        # --- 3️⃣ NLP for implicit adds ---
        actions = re.split(r"(?:(?<=\.)|(?<=\n)|(?<=and ))(?=\s*add )", user_message, flags=re.IGNORECASE)
        added_count = 0
        for action in actions:
            if not action.strip():
                continue

            if re.search(r"(to shopping list|to buy|list to buy)", action, re.IGNORECASE):
                match = re.findall(r"(?:buy|for|to buy|list to buy)\s+(.*)", action, re.IGNORECASE)
                if match:
                    add_journal_entry(match[0].strip(), "shoppinglist")
                    added_count += 1
                continue

            if re.search(r"(remind|appointment|meeting|schedule|event)", action, re.IGNORECASE):
                # avoid false positives for questions
                if re.search(r"\b(do|does|did|any|what|show|list|display|have|are there)\b", action, re.IGNORECASE):
                    continue  # this is likely a query, not an add
                add_journal_entry(action, "reminder")
                added_count += 1
                continue


        if added_count:
            return f"✅ Added {added_count} journal entr{'y' if added_count == 1 else 'ies'} successfully."

        # --- 4️⃣ Contextual LLM step for everything else ---
        context_text = ""
        if should_include_context(user_message) and st.session_state.journal_entries:
            recent = st.session_state.journal_entries[-10:]
            context_text = "Here are recent journal entries:\n" + "\n".join(
                [f"- [{e['category']}] {e['content']}" for e in recent]
            )

        contents = [context_text, user_message] if context_text else [user_message]

        config = types.GenerateContentConfig(
            system_instruction=get_system_instruction(),
            tools=[add_entry_tool, query_entries_tool],
        )

        response = safe_generate(client, "models/gemini-2.0-flash-lite", contents, config)

        # --- 5️⃣ Tool execution if model triggers it ---
        function_calls = [
            part.function_call for part in response.candidates[0].content.parts
            if hasattr(part, "function_call") and part.function_call
        ]

        if function_calls:
            results = []
            for func_call in function_calls:
                args = dict(func_call.args or {})
                if "category" in args and not args["category"]:
                    args["category"] = "note"
                result = execute_function(types.FunctionCall(name=func_call.name, args=args))
                results.append(types.Part.from_function_response(name=func_call.name, response=result))

            response = safe_generate(
                client,
                "models/gemini-2.0-flash-lite",
                [
                    *[types.Part.from_function_call(name=f.name, args=f.args) for f in function_calls],
                    *results
                ],
                config,
            )
            return response.text

        return response.text

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error: {str(e)}"

# ------------------- SIDEBAR -------------------
with st.sidebar:
    st.title("📒 Journal Entries")
    st.metric("Total Entries", len(st.session_state.journal_entries))

    if st.session_state.journal_entries:
        for entry in reversed(st.session_state.journal_entries):
            content_text = entry['content'].strip() or "🗒️ No details available"
            st.markdown(
                f"""
                <div style='background-color:#f9fafb;padding:10px;border-radius:10px;margin-bottom:10px;
                border:1px solid #eee;box-shadow:0 1px 3px rgba(0,0,0,0.05)'>
                    <b style='color:#333'>{entry['category'].capitalize()}</b><br>
                    <small style='color:#888'>{datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')}</small><br>
                    <div style='margin-top:4px;color:#444'>{content_text}</div>
                    <div style='margin-top:6px;font-size:12px;color:#666'>
                        <i>Tags:</i> {', '.join(entry['tags']) if entry['tags'] else 'None'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    if st.button("🗑️ Clear All Entries", use_container_width=True):
        st.session_state.journal_entries.clear()
        st.session_state.chat_history.clear()
        st.rerun()

# ------------------- MAIN UI -------------------
st.title("📔 AI Journal Assistant")
st.markdown("*Your personal journal powered by Gemini 2.0 Flash Lite*")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = process_message(prompt)
            st.markdown(reply)

    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    st.rerun()
