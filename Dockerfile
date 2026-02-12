FROM python:3.13-trixie

WORKDIR /app

RUN pip install --no-cache-dir streamlit httpx

COPY app.py .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
