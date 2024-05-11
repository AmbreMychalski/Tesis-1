# Obstetric-GPT, a obstetrics-focused Chatbot

**Exploration of domain-specific conversational systems as a means to
enhance obstetric emergency care**

Ambre MYCHALSKI - 202326682 - 11/05/2024

This web applications was carried out within the scope of a Master Tesis in the Systems and Computing Engineering Department of the University of the Andes.

Assessor: Prof. Ruben Francisco MANRIQUE

FLAG lab
Faculty of Engineering

*This thesis is submitted in partial fulfillment of the requirements for a degree of Master in Systems
and Computing Engineering.*

## Description

This project focuses on the development of a medical chatbot capable of providing accurately sourced answers to obstetric questions posed by medical professionals in emergency contexts. It is based on a Retrieval Augmented Generation (RAG) architecture and uses the GPT-3.5-turbo and GPT-4 API from OpenAI.

## How to use it ?

### Install

To launch the project, ensure you have all the requirements installed on your computer (i.e. requirements.txt).

* In the Back_Python folder:
pip install -r requirements.txt

### Create the embedding database

The database is permanent and hosted by ChromaDB.

* In the Back_Python folder:
python databaseInit.py

If you want to recreate/change the .csv embeddings file and fill the collection with the embeddings, run the fileProcessing.py program. The documents to be processed must be included into the Front_React\documents folder:

* In the Back_Python folder:
python fileProcessing.py

### Launch the project

Please add your openAI key in the files in the files 'back.py' and 'fileProcessing.py' in the variables 'openai.api_key'.
To launch the application, open a powershell terminal:

* In the Back_Python folder:
    python app.py

Go on your navigator on: http://127.0.0.1:3001

* The credentials to access the main application are:
username: usuario
password: contrasenaobstetricgptuniandes

### Use the project

To use the project, type a question related to the obstetric field in the search bar and press Enter or click on the button "Enviar".

Example of questions:

* ¿Qué alternativas tengo si no dispongo de oxitocina para manejar la hemorragia postparto?

The source PDFs can be opened to check the context used to generate the answer by clicking on the link.

To iniciate a new conversation, click on the button "Nueva conversación".

To delete a message, click on the button "Suprimir".

To save the history in a JSON file, click on the button "Guardar historial".

## Specifications of the project:

The Python-based backend employs the Flask framework, and the construction of the vectorial database is also done in Python.

The generative LLMs used in the backend are GPT-3.5 turbo and GPT-4.

We use an API and json files to communicate with the frontend, coded with React.
