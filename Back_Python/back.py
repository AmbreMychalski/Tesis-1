import os
import requests
import json
import openai
import pandas as pd
import numpy as np
from openai.embeddings_utils import distances_from_embeddings
import chromadb
import time
import fitz
import io

rawDataset = "react_build/documents/"

# ---------------- GPT 4 --------------
# openai.api_key = os.getenv("OpenAIKey_gpt4") #gpt 4
# openai.api_base = "https://invuniandesai-2.openai.azure.com/"
# deployment_name='gpt-4-rfmanrique'
# deployment_embeddings_name = 'gpt4-embedding-ada-002'

# ---------------- GPT 3.5 turbo --------------
openai.api_key = os.getenv("OpenAIKey")
openai.api_base = "https://invuniandesai.openai.azure.com/"
deployment_name='gpt-35-turbo-rfmanrique'
deployment_embeddings_name = 'text-embedding-ada-002-rfmanrique'

openai.api_type = 'azure'
openai.api_version = '2023-05-15'
current_sources = []

path = "chroma-db/"
chroma_client = chromadb.PersistentClient(path)
collection = chroma_client.get_collection("embedding_db_persist_1500")    

# Highlight a pdf zone: Take the filename, the pages and the coordinates of the 
# zone to highlight and return a the transformed pdf in a bytes stream.
def highlight_context(fname, pages, coords):
#     x1              x2
#  y1 -----------------
#     |               |
#     |               |
#     |               |
#     |      PDF      |
#     |               |
#     |               |
#     |               |
#  y2 -----------------


    first_page=pages[0]-1
    last_page=pages[-1]-1
    pages = []
    i=first_page
    while i!=last_page+1:
        pages.append(i)
        i+=1
    pdf_document = fitz.open(rawDataset+ fname +".pdf")
    for i in range(len(pages)):
        p = pdf_document[pages[i]]
        end_of_page_x = p.rect.width 
        end_of_page_y = p.rect.height 
        x1, y1, x2, y2 = 10.0, 10.0, end_of_page_x-10, end_of_page_y-10
        if i==0:
            if coords[0]-10 >=0.0:
                x1 = coords[0]-10
            if coords[2]-50 >=0.0:
                y1 = coords[2]-50
        elif i==len(pages)-1:
            if coords[3]+30 <=end_of_page_x:
                x2 = coords[3]+30
            if coords[0]-10 <=end_of_page_y:
                y2 = coords[1]+50
        rect_to_draw = (x1, y1, x2, y2)
        rect_highlight = fitz.Rect(rect_to_draw)
        p1 = rect_highlight.top_left  
        p2 = rect_highlight.bottom_right  
        p.draw_rect(rect_highlight,  color=fitz.utils.getColor('black'), fill=fitz.utils.getColor('yellow'), fill_opacity=0.3, width = 0.3)

    pdf_stream = io.BytesIO()
    pdf_document.save(pdf_stream)
        
    pdf_stream.seek(0)
    pdf_document.close()
    return pdf_stream

# Translate a test from Spanish to English: Take the Spanish text in input and
# return the English version 
def translate_es_en(txt_es):
    txt_en=''
    try:
        translated = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages=[
                {"role": "system", "content": "You're a translator, and you translate between Spanish and English."},
                {"role": "user", "content": f"""Text to translate: ``` {txt_es} ```. Translate the text delimited \
    by triple backticks from Spanish to English. \
    You must keep the translated text as close semantically and syntactically to its original \
    version as possible. You mustn’t add any special characters such as ```, ", / and your answer mustn’t \
    be returned between quotes. \
    Return the English translation only.\
    """},
            ]          
        )
        txt_en = translated['choices'][0]['message']['content']

    except Exception as e:
        txt_en = 'An error occurred'
    return(txt_en)

# Translate a test from English to Spanish: Take the English text in input and
# return the Spanish version 
def translate_en_es(txt_en):
    translated = openai.ChatCompletion.create(
        engine= deployment_name, 
        messages=[
            {"role": "system", "content": "You're a translator, and you translate between English and Spanish."},
            {"role": "user", "content": f"""Text to translate: ``` {txt_en} ```. Translate the text delimited \
by triple backticks from English to Spanish.
You must keep the translated text as close semantically and syntactically to its original \
version as possible. You mustn't add any special characters such as ```, ", / and your answer mustn't \
be returned between quotes.
Return the Spanish translation only.
"""},
        ]          
    )
    txt_es = translated['choices'][0]['message']['content']
    return(txt_es)

# Create a context relevant to a given question: Take the question in Spanish and 
# the history in input and return a context of a defined maximum length with the 
# corresponding sources
def create_context_es(question, prev_questions, max_len=1500, size="ada"):
    global current_sources
    current_sources = []

    # Spanish to English translation
    question_en = translate_es_en(question)
    if 'An error occurred' in question_en:
        return('', [], question_en)

    # HyDE:
    first_response = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages=[
                {"role": "system", "content": "You are a doctor in obstetrics."},
                {"role": "user", "content": f"Reword the question to correct the grammatical errors and then answer the question considering the previous asked questions. In your answer you must include the previous reword question and the answer. \n\n---\n\nPrevious questions and their answers: {prev_questions}\n\nQuestion: {question}\nAnswer after the colon, with the reword question and the answer, without making a separation between the reword question and the answer:"},
            ]        
        )
    
    # Pass the question into a vector (Embedding)
    q_embeddings = openai.Embedding.create(input=first_response['choices'][0]['message']['content'], engine=deployment_embeddings_name)['data'][0]['embedding']

    # Get the more similar embeddings from the database
    results = collection.query(query_embeddings=q_embeddings, n_results=50)

    returns = []
    sources = []
    cur_len = 0

    # Add the chunk to the context until the context is too long
    for i in range(len(results['ids'][0])):
        document = results['documents'][0][i]
        title = results['metadatas'][0][i]['title']
        page = results['metadatas'][0][i]['page']
        coords = results['metadatas'][0][i]['coords']
        tokens= results['metadatas'][0][i]['tokens']
        if(cur_len > max_len):
            break
        temp = []
        context_chunk = document

        # Check if the context chunk is relevant to the query
        response = openai.ChatCompletion.create(
            engine= deployment_name,
            messages=[  
                {"role": "system", "content": "You are a doctor in obstetrics."},
                {"role": "user", "content": f"Evaluate the relevance of the following context snippet to answer the following question in the field of obstetrics: {context_chunk}\n\nThe question is: {question}\nDo you consider it relevant for providing an accurate response in this field? Respond with a 'yes' or 'no' only."},
            ]     
        )
        time.sleep(0.1)
    
        # Add the chunk to the context if relevant
        if ("yes" in (response['choices'][0]['message']['content'].lower())):
            cur_len += int(tokens) + 4
            returns.append(document)
            temp.append(title)
            temp.append(page)
            temp.append(coords)
            sources.append(temp)
    
    # Treat the sources typing
    for i in range(len(sources)):
        src = sources[i][1].replace('(', '').replace(')', '').split(', ')
        for j in range(len(src)):
            src[j]=int(src[j])
        if src[0]==src[1]:
            sources[i][1] = "("+str(src[0])+")"
            
    # Return the context and sources
    return(("\n\n###\n\n".join(returns)), sources, question_en)

# Get the previous questions from history: Take the history in input and return the 
# questions it contains
def get_previous_questions(history):
    questions= [[elem['query_en'], elem['answer_en']] for elem in history]
    prev_questions = []
    for elem in history:
        prev_questions.append({'role':'user','content':elem['query_en']})
        prev_questions.append({'role':'assistant','content':elem['answer_en']})
    return prev_questions

# Generate an answer to a question: Take the Spanish question and the history in input
# and return the answers (in English and in Spanish) and the sources used in the RAG process
# to ground the answer.
def generate_answer(question_es, history, deployment=deployment_name):
    # Retrieve the previous questions from the history
    prev_questions = get_previous_questions(history)

    role_sys = {"role": "system", "content": "You are a specialized obstetric chatbot. You respond to questions from other doctors regarding obstetrical emergencies."}
    
    # Create a context to ground the answer
    context, sources, question_en = create_context_es(question_es, prev_questions, max_len=1800, size="ada")
    nb_tokens=0
    
    if 'An error occurred:' in question_en:
        answer_es = 'Ocurrió un error: La respuesta fue filtrada debido a que la solicitud activó la política de gestión de contenido de Azure OpenAI. Por favor, modifica tu solicitud y vuelve a intentarlo. Para obtener más información sobre nuestras políticas de filtrado de contenido, por favor lee nuestra documentación: https://go.microsoft.com/fwlink/?linkid=2198766'
        return (answer_es, question_en, '', sources)

    for quest, ans in prev_questions:
        nb_tokens+=len(quest.split())+len(ans.split())
        
    # Prompt to generate the answer
    try:
        prev_questions.insert(0, role_sys)
        prev_questions.append({"role": "user", "content": f"""```  {context}  ```
            Question ---  {question_en}  ---  
    From the support information that you are provided, delimited by triple backticks, extract the \
    relevant information \
    based on the asked question delimited by triple quotes. If there are any measurements or doses \
    mentioned in the question, try to locate them in the provided information. 
    Then, using these relevant details and any measurements or dosis you extracted, continue the previous \
    conversation by answering the question.
    Provide a detailed answer, offering further explanations and elaborating on the information. 
    The answer mustn’t include special characters such as /, ", ---, ``` etc. 
    If the question cannot be answered with the provided information, simply write "I don't know.".
            """})
        prev_questions.append({"role": "user", "content": f"""Once you thought about your answer, revise it following these steps:
    1. Verify your answer and remove any references to the provided information. For instance, \
    if your answer states:  "Based on the information provided, it seems that ...", replace it with \
    "It seems that ". Refer to these information as your own knowledge as an obstetrical chatbot. \
    Your response mustn't mention the words "provided information" or "given information" under any circumstances.
    2. If if the context delimited by triple backticks is empty or if your answer implies that you cannot \
    respond based on the given information, simply state "I don't know.".
    3. Remove from your answer any advice reminding him to consult with a healthcare professional."""})
        
        response = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages= prev_questions
        )
        answer_en = response['choices'][0]['message']['content']
        answer_es = translate_en_es(answer_en)
        return (answer_es, answer_en, question_en, sources)
    except Exception as e:
        if "4096 tokens" in str(e):
            return("Ha alcanzado el límite máximo de una conversación: por favor elimine mensajes anteriores o inicie una nueva conversación.",
                   "You have reached the maximum size of a conversation: please delete previous messages or start a new conversation.",
                   question_en, [])


