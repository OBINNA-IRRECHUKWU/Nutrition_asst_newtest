FROM python:3.9-slim

WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh
# RUN ollama serve & 
# RUN ollama pull llama3.2
COPY ../app .

# RUN pip install -r requirements.txt
# Install dependencies with specific versions to avoid conflicts
RUN pip install --no-cache-dir -r requirements.txt 
#    & // pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Create a config directory for Streamlit
RUN mkdir -p /root/.streamlit

# Create Streamlit config file
RUN echo '\
[server]\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
address = "0.0.0.0"\n\
port = 8501\n\
[browser]\n\
serverAddress = "0.0.0.0"\n\
serverPort = 8501\n\
' > /root/.streamlit/config.toml

RUN chmod +x startscript.sh
EXPOSE 8501
# CMD ["streamlit", "run", "app.py"]
ENTRYPOINT [ "./startscript.sh" ]
#CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]

