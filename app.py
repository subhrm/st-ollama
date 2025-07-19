import streamlit as st
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
import ollama
import time


def get_ollama_models():
    """Returns a list of Ollama models."""
    try:
        return [model.model for model in ollama.list()["models"]]
    except Exception as e:
        st.error(f"Error getting Ollama models: {e}")
        st.warning("Please make sure Ollama is running and accessible.")
        return []


PERSONAS = {
    "default": "You are a helpful assistant.",
    "pirate": "You are a pirate. All your responses must be in pirate dialect.",
    "therapist": "You are a therapist. Your responses should be empathetic and understanding.",
    "comedian": "You are a comedian. Your responses should be witty and humorous.",
    "custom": "",
}


def main():
    """Main function to run the Streamlit app."""
    st.title("Chat with local Ollama models")

    models = get_ollama_models()
    if not models:
        return

    col1, col2 = st.columns(2)
    with col1:
        selected_model = st.selectbox("Select a model", models)
    with col2:
        selected_persona = st.selectbox("Select a persona", list(PERSONAS.keys()))

    if selected_persona == "custom":
        custom_persona = st.text_area("Enter your custom persona prompt:")
        PERSONAS["custom"] = custom_persona

    temperature = st.slider(
        "Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05
    )

    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            llm = OllamaLLM(model=selected_model, temperature=temperature)

            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", PERSONAS[selected_persona]),
                    *st.session_state.messages,
                    ("human", "{prompt}"),
                ]
            )

            chain = prompt_template | llm | StrOutputParser()

            response = ""
            start_time = time.time()
            token_count = 0
            ollama_tps = None
            for chunk in chain.stream({"prompt": prompt}):
                response += chunk
                token_count += len(chunk.split())
                # Try to extract tps from Ollama chunk if available
                if hasattr(chunk, "tps"):
                    ollama_tps = chunk.tps
                message_placeholder.markdown(response + "▌")
            end_time = time.time()
            message_placeholder.markdown(response)

            elapsed = end_time - start_time
            tps = token_count / elapsed if elapsed > 0 else 0
            if ollama_tps is not None:
                st.caption(
                    f"Time taken: {elapsed:.2f} seconds | Tokens: {token_count} | Ollama TPS: {ollama_tps:.2f}"
                )
            else:
                st.caption(
                    f"Time taken: {elapsed:.2f} seconds | Tokens: {token_count} | Tokens/sec: {tps:.2f}"
                )

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
