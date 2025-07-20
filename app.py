import streamlit as st
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
import ollama
import time
from audiorecorder import audiorecorder
import speech_recognition as sr
from gtts import gTTS
import base64
import os


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
}


def text_to_speech(text):
    """Converts text to speech and returns the audio as a base64 string."""
    try:
        tts = gTTS(text=text, lang='en')
        with open("response.mp3", "wb") as f:
            tts.write_to_fp(f)
        with open("response.mp3", "rb") as f:
            audio_bytes = f.read()
        os.remove("response.mp3")
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return f"data:audio/mp3;base64,{audio_base64}"
    except Exception as e:
        st.error(f"Error in text-to-speech: {e}")
        return None


def main():
    """Main function to run the Streamlit app."""
    st.title("Chat with local Ollama models")

    models = get_ollama_models()
    if not models:
        return

    with st.sidebar:
        selected_model = st.selectbox("Select a model", models)
        temperature = st.slider(
            "Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05
        )

        selected_persona = st.selectbox("Select a persona", list(PERSONAS.keys()))

        system_prompt = st.text_area(
            "System Prompt", value=PERSONAS[selected_persona], height=200
        )

        

        if st.button("Clear History"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Reset chat if system prompt changes
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = system_prompt
    elif st.session_state.system_prompt != system_prompt:
        st.session_state.system_prompt = system_prompt
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "audio" in message and message["audio"]:
                st.audio(message["audio"], format="audio/mp3")

    col1, col2 = st.columns([7, 1])
    with col1:
        prompt = st.chat_input("What is up?")
    with col2:
        audio = audiorecorder("", "", key="recorder")

    if len(audio) > 0:
        st.info("Transcribing audio...")
        audio.export("input.wav", format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile("input.wav") as source:
            audio_data = recognizer.record(source)
        try:
            prompt = recognizer.recognize_google(audio_data)
            st.sidebar.success(f"Transcription: {prompt}")
        except sr.UnknownValueError:
            st.sidebar.error("Google Speech Recognition could not understand audio")
            prompt = None
        except sr.RequestError as e:
            st.sidebar.error(
                f"Could not request results from Google Speech Recognition service; {e}"
            )
            prompt = None
        finally:
            os.remove("input.wav")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            llm = OllamaLLM(model=selected_model, temperature=temperature)

            messages_for_prompt = [
                (msg["role"], msg["content"]) for msg in st.session_state.messages
            ]

            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    *messages_for_prompt,
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

            with st.spinner("Generating audio response..."):
                audio_base64 = text_to_speech(response)
                if audio_base64:
                    st.markdown(
                        f'''
                        <audio autoplay>
                            <source src="{audio_base64}" type="audio/mp3">
                        </audio>
                    ''',
                        unsafe_allow_html=True,
                    )

            st.session_state.messages.append(
                {"role": "assistant", "content": response, "audio": audio_base64}
            )


if __name__ == "__main__":
    main()
