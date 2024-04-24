FROM python:3.9.19-bookworm

WORKDIR /my-music-gpt

COPY ./init_db.py .
COPY ./embeddings_complete.csv .
COPY ./requirements.txt .
COPY ./react_build/ ./react_build/
COPY ./app.py .
COPY ./back.py .

RUN pip install -r requirements.txt
RUN python init_db.py

EXPOSE 5000


CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
