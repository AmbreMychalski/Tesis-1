FROM python:3.9.19-bookworm

WORKDIR /Tesis-1

COPY ./databaseInit.py .
COPY ./embeddings/embeddings_chunks1500.csv ./embeddings/
COPY ./requirements.txt .
COPY ./react_build/ ./react_build/
COPY ./app.py .
COPY ./back.py .

RUN pip install -r requirements.txt
RUN python databaseInit.py

EXPOSE 5000


CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
