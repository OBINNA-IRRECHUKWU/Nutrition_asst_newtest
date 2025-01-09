#!/bin/bash

# Start Ollama in the background
ollama serve &

# Wait for Ollama to start
sleep 5

# download the model
ollama pull llama3.2

# Start Streamlit in the foreground
streamlit run app.py