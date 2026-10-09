import streamlit as st

from agent import AgentError, run_agent


st.set_page_config(page_title="SmartCalc AI", page_icon="🧮")

st.title("SmartCalc AI")
st.write(
    "A beginner-friendly AI agent that understands natural-language math "
    "questions and uses a calculator tool when needed."
)

with st.sidebar:
    st.subheader("How it works")
    st.markdown("**Agent → Tool → Result → Answer**")
    st.caption(
        "The LLM interprets your question, the calculator performs the "
        "validated operation, and the LLM explains the result."
    )
    show_debug = st.checkbox("Show debug details", value=False)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if show_debug and message["role"] == "assistant" and message.get("debug"):
            with st.expander("Debug details"):
                st.json(message["debug"])

question = st.chat_input("Ask a math question, such as: What is 25% of 800?")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer, debug = run_agent(question)
            except AgentError as error:
                answer = f"Sorry, I could not complete that request: {error}"
                debug = None

        st.markdown(answer)
        if show_debug and debug:
            with st.expander("Debug details"):
                st.json(debug)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "debug": debug}
    )
