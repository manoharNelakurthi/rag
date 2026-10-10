
import streamlit as st
from rag_pipeline import load_document, chunk_text, Retriever, generate_answer

# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# 2. PROFESSIONAL UI STYLING
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background-color: #14263f;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    .hero {
        padding: 24px;
        border-radius: 16px;
        background: linear-gradient(120deg, #14263f, #28527a);
        color: white;
        margin-bottom: 20px;
    }

    .hero h1 {
        color: white;
        margin-bottom: 8px;
    }

    .hero p {
        color: #e4edf7;
        margin-bottom: 0;
    }

    .panel {
        background: white;
        border: 1px solid #e5eaf2;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5eaf2;
        padding: 14px;
        border-radius: 12px;
    }

    .small-note {
        color: #64748b;
        font-size: 13px;
    }

    .stButton button {
        border-radius: 9px;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 3. SESSION STATE
# --------------------------------------------------
defaults = {
    "retriever": None,
    "chunks": None,
    "file_name": None,
    "messages": [],
    "summary": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def ask_question(question):
    """Retrieve relevant chunks and generate an answer."""
    if not st.session_state.retriever:
        return

    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    try:
        results = st.session_state.retriever.search(question)
        answer, _ = generate_answer(question, results)

        st.session_state.messages.append({
            "role": "assistant",
            "content": str(answer),
        })
    except Exception as error:
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "I couldn't generate an answer. "
                "Please try again. Technical details: "
                + str(error)
            ),
        })


# --------------------------------------------------
# 4. SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("## ⚖️ Legal AI")
    st.caption("Document intelligence assistant")
    st.divider()

    st.markdown("### 📄 Your document")

    uploaded_file = st.file_uploader(
        "Upload a legal PDF or TXT file",
        type=["pdf", "txt"],
        help="Upload a document to ask questions about it.",
    )

    if uploaded_file is not None:
        if st.session_state.file_name != uploaded_file.name:
            try:
                with st.spinner("Processing document..."):
                    text = load_document(uploaded_file)
                    chunks = chunk_text(text)

                    if not chunks:
                        st.error("No readable text was found.")
                    else:
                        retriever = Retriever(chunks)

                        st.session_state.retriever = retriever
                        st.session_state.chunks = chunks
                        st.session_state.file_name = uploaded_file.name
                        st.session_state.messages = []
                        st.session_state.summary = None

                        st.success("Document processed successfully!")

            except Exception as error:
                st.error(f"Could not process the document: {error}")

    if st.session_state.file_name:
        st.markdown("**Current file**")
        st.caption(f"📎 {st.session_state.file_name}")

        if st.session_state.chunks is not None:
            st.metric("Text chunks", len(st.session_state.chunks))

        if st.button("🗑️ Clear current document", use_container_width=True):
            st.session_state.retriever = None
            st.session_state.chunks = None
            st.session_state.file_name = None
            st.session_state.messages = []
            st.session_state.summary = None
            st.rerun()

    st.divider()
    st.markdown("### ✨ Available features")
    st.markdown(
        "- Document question answering\n"
        "- AI-generated summary\n"
        "- Suggested questions\n"
        "- Source-grounded responses"
    )

    st.divider()
    st.caption("For informational purposes only. Not legal advice.")


# --------------------------------------------------
# 5. MAIN HEADER
# --------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>⚖️ Legal Document Assistant</h1>
    <p>
        Understand legal documents, explore important clauses,
        and ask questions using Retrieval-Augmented Generation.
    </p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 6. DOCUMENT OVERVIEW
# --------------------------------------------------
if st.session_state.chunks:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Documents loaded", 1)

    with col2:
        st.metric("Text chunks", len(st.session_state.chunks))

    with col3:
        st.metric("Questions asked", sum(
            1 for msg in st.session_state.messages
            if msg["role"] == "user"
        ))

    tab_chat, tab_summary, tab_help = st.tabs([
        "💬 Ask questions",
        "📝 Document summary",
        "ℹ️ How to use",
    ])

    # --------------------------------------------------
    # 7. CHAT TAB
    # --------------------------------------------------
    with tab_chat:
        st.subheader("Ask your document")
        st.caption(
            "Ask about clauses, obligations, dates, conditions, "
            "or other details contained in your document."
        )

        st.markdown("**Try a suggested question:**")

        suggestions = [
            "What is this document about?",
            "What are the important clauses?",
            "What obligations are mentioned?",
        ]

        suggestion_cols = st.columns(3)

        for index, suggestion in enumerate(suggestions):
            with suggestion_cols[index]:
                if st.button(
                    suggestion,
                    key=f"suggestion_{index}",
                    use_container_width=True,
                ):
                    ask_question(suggestion)
                    st.rerun()

        st.divider()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input(
            "Ask a question about your legal document..."
        )

        if question:
            ask_question(question)
            st.rerun()

    # --------------------------------------------------
    # 8. SUMMARY TAB
    # --------------------------------------------------
    with tab_summary:
        st.subheader("Document summary")
        st.write(
            "Generate a summary based on the relevant content "
            "retrieved from your document."
        )

        if st.button("✨ Generate summary", type="primary"):
            try:
                with st.spinner("Generating summary..."):
                    summary_query = (
                        "Summarize this legal document. Explain its "
                        "purpose, important clauses, parties, "
                        "obligations, dates, and potential risks "
                        "if these details are available in the text. "
                        "Do not invent missing information."
                    )

                    results = st.session_state.retriever.search(
                        summary_query
                    )
                    summary, _ = generate_answer(
                        summary_query, results
                    )

                    st.session_state.summary = str(summary)

            except Exception as error:
                st.error(f"Summary generation failed: {error}")

        if st.session_state.summary:
            st.markdown("### Summary")
            st.markdown(st.session_state.summary)

            st.download_button(
                "⬇️ Download summary",
                data=st.session_state.summary,
                file_name="legal_document_summary.txt",
                mime="text/plain",
            )

        st.info(
            "The summary uses retrieved text, so it may not cover "
            "every part of a long document. Review the original file."
        )

    # --------------------------------------------------
    # 9. HELP TAB
    # --------------------------------------------------
    with tab_help:
        st.subheader("How to use Legal AI")

        st.markdown("""
        1. Upload a readable PDF or TXT file in the sidebar.
        2. Wait for the document processing to finish.
        3. Open **Ask questions** and enter your question.
        4. Review the generated answer against the original document.
        5. Open **Document summary** to request a summary.

        **Important:** AI answers can be incomplete or incorrect.
        Check important legal details against the original document
        and consult a qualified lawyer when necessary.
        """)

else:
    st.markdown("""
    <div class="panel">
        <h3>👋 Welcome to your Legal AI Assistant</h3>
        <p>
            Start by uploading a legal PDF or TXT document in the
            sidebar. Once it is processed, you can ask questions,
            explore clauses, and generate a summary.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### What you can do")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📄 Analyze")
        st.write("Upload a legal document for processing.")

    with col2:
        st.markdown("#### 💬 Ask")
        st.write("Ask questions about the document's contents.")

    with col3:
        st.markdown("#### 📝 Summarize")
        st.write("Generate a concise summary of retrieved passages.")
