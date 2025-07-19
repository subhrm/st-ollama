# Project: st-ollama

## Description

This project is a Streamlit web application that allows users to chat with local large language models (LLMs) through the Ollama interface.

## Key Technologies

- **Python:** The core programming language.
- **Streamlit:** Used for creating the web application and user interface.
- **LangChain:** Used for building the language model chain and managing prompts.
- **Ollama:** The interface to run and interact with local LLMs.

## Core Functionality

- **Model Selection:** The application fetches and displays a list of available Ollama models for the user to choose from.
- **Persona Selection:** Users can choose from a list of predefined personas or provide a custom system prompt.
- **Temperature Control:** Users can adjust the temperature of the LLM to control the randomness of the responses.
- **Chat Interface:** It provides a chat interface where users can input prompts and receive responses from the selected LLM.
- **Conversation History:** The chat history is maintained within the session, and can be cleared.
- **Performance Metrics:** The application displays the time taken to generate a response, the number of tokens, and the tokens per second (TPS).

## File Structure

- **`app.py`:** The main Streamlit application file containing the UI and logic.
- **`requirements.txt`:** Lists the necessary Python dependencies for the project.
- **`README.md`:** A brief description of the project.
