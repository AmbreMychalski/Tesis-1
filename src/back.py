import os
import requests
import json
import openai
import pandas as pd
import numpy as np
from openai.embeddings_utils import distances_from_embeddings
import chromadb
import fitz
import io

rawDataset = "front/rawDataset/"
modified_docs = "front/public/rawDataset/"

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

path = "C:/Users/ambre/Desktop/INSA/5A/202320/Tesis_I/APP/front/src"
chroma_client = chromadb.PersistentClient(path)
collection = chroma_client.get_collection("embedding_db_persist")    

def highlight_context(fname, pages, coords):
    pages = [p-1 for p in pages]
    pdf_document = fitz.open(rawDataset+ fname +".pdf")

    for i in range(len(pages)):
        x1, x2, y1, y2 = 0.0, 0.0, 0.0, 0.0
        p = pdf_document[pages[i]]
        if i==0:
            end_of_page_x = p.rect.width 
            end_of_page_y = p.rect.height 
            x1 = coords[0]
            x2 = coords[1]
            y1 = end_of_page_x
            y2 = end_of_page_y
            print(x1, x2, y1, y2)
        elif i < (len(pages)-1):
            end_of_page_x = p.rect.width 
            end_of_page_y = p.rect.height 
            x1 = 0.0
            x2 = 0.0
            y1 = end_of_page_x
            y2 = end_of_page_y
        else:
            print(i)
            x1 = 0.0
            x2 = 0.0
            y1 = coords[2]
            y2 = coords[3]
        rect_to_draw = (x1, x2, y1, y2)
        p.add_highlight_annot(rect_to_draw)
    pdf_stream = io.BytesIO()
    pdf_document.save(pdf_stream)
        
    pdf_stream.seek(0)
    pdf_document.close()
    return pdf_stream

def translate_es_en(txt_es):
    translated = openai.ChatCompletion.create(
        engine= deployment_name, 
        messages=[
            {"role": "system", "content": "You're a translator, and you translate between Spanish and English ."},
            # You are a helpful medical knowledge assistant. Provide useful, complete, and 
            # scientifically-grounded answers to common consumer search queries about 
            # obstetric health.
            # If the text is written in spanish translate it in english. Write the translation after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible:

            {"role": "user", "content": f"Translate the following text from spanish to english./\n\n---\n\n/{txt_es}\n\n/You have to keep the translated text as close semantically and syntactically to its original version as possible. Return the English translation only:"},
        ]          
    )
    txt_en = translated['choices'][0]['message']['content']
    return(txt_en)

def translate_en_es(txt_en):
    translated = openai.ChatCompletion.create(
        engine= deployment_name, 
        messages=[
            {"role": "system", "content": "You're a translator, and you translate between English and Spanish ."},
            # You are a helpful medical knowledge assistant. Provide useful, complete, and 
            # scientifically-grounded answers to common consumer search queries about 
            # obstetric health.
            # If the text is written in spanish translate it in english. Write the translation after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible:

            {"role": "user", "content": f"Translate the following text from english to spanish./\n\n---\n\n/{txt_en}\n\n/You have to keep the translated text as close semantically and syntactically to its original version as possible. Return the Spanish translation only:"},
        ]          
    )
    txt_es = translated['choices'][0]['message']['content']
    return(txt_es)

def create_context(question, prev_questions, max_len=1800, size="ada"):
    global current_sources
    current_sources = []

    # HyDE:
    first_response = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages=[
                {"role": "system", "content": "You are a doctor in obstetrics."},
                # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                # scientifically-grounded answers to common consumer search queries about 
                # obstetric health.

                {"role": "user", "content": f"Reword the question to correct the grammatical errors and then answer the question taking into account the previous asked questions. In your answer you must include the previous reword question and the answer./\n\n---\n\nPrevious questions and their answers: {prev_questions}\n\nQuestion: {question}\nAnswer after the colon, with the reword question and the answer, without making a separation between the reword question and the answer:"},
            ]          
        )
    
    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    # Get the embeddings for the question
    # q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002-rfmanrique')['data'][0]['embedding']
    # Use the first answer of chatGPT to create the context
    q_embeddings = openai.Embedding.create(input=first_response['choices'][0]['message']['content'], engine=deployment_embeddings_name)['data'][0]['embedding']

    # Get the distances from the embeddings
    # df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')
    results = collection.query(query_embeddings=q_embeddings, n_results=20)

    returns = []
    sources = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
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

        response = openai.ChatCompletion.create(
            engine= deployment_name, # engine = "deployment_name".
            messages=[  
                {"role": "system", "content": "You are a doctor in obstetrics."},
                # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                # scientifically-grounded answers to common consumer search queries about 
                # obstetric health.

                {"role": "user", "content": f"Evaluate the relevance of the following context snippet to answer the following question in the field of obstetrics: {context_chunk}\n\n---\n\nThe question is: {question}\nDo you consider it relevant for providing an accurate response in this field? Please respond with a 'yes' or 'no' only."},
            ]          
        )

        # response['choices'][0]['message']['content'] = 'yes'
    
        # Add the length of the text to the current length
        if ("yes" in (response['choices'][0]['message']['content'].lower())):
            cur_len += int(tokens) + 4
            returns.append(document)
            temp.append(title)
            temp.append(page)
            temp.append(coords)
            sources.append(temp)
            
    # Return the context
    return(("\n\n###\n\n".join(returns)), sources)

def create_context_es(question, prev_questions, max_len=1800, size="ada"):
    global current_sources
    current_sources = []

    # Spanish to English translation
    question_en = translate_es_en(question)
    
    # HyDE:
    first_response = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages=[
                {"role": "system", "content": "You are a doctor in obstetrics."},
                # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                # scientifically-grounded answers to common consumer search queries about 
                # obstetric health.

                {"role": "user", "content": f"Reword the question to correct the grammatical errors and then answer the question taking into account the previous asked questions. In your answer you must include the previous reword question and the answer./\n\n---\n\nPrevious questions and their answers: {prev_questions}\n\nQuestion: {question_en}\nAnswer after the colon, with the reword question and the answer, without making a separation between the reword question and the answer:"},
            ]          
        )
    
    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    # Get the embeddings for the question
    # q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002-rfmanrique')['data'][0]['embedding']
    # print("\n\nFIRST ANSWER", first_response['choices'][0]['message']['content'], "\n\n")
    # Use the first answer of chatGPT to create the context
    q_embeddings = openai.Embedding.create(input=first_response['choices'][0]['message']['content'], engine=deployment_embeddings_name)['data'][0]['embedding']

    # Get the distances from the embeddings
    # df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')
    results = collection.query(query_embeddings=q_embeddings, n_results=20)

    returns = []
    sources = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
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

        response = openai.ChatCompletion.create(
            engine= deployment_name, # engine = "deployment_name".
            messages=[  
                {"role": "system", "content": "You are a doctor in obstetrics."},
                # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                # scientifically-grounded answers to common consumer search queries about 
                # obstetric health.

                {"role": "user", "content": f"Evaluate the relevance of the following context snippet to answer the following question in the field of obstetrics: {context_chunk}\n\n---\n\nThe question is: {question_en}\nDo you consider it relevant for providing an accurate response in this field? Please respond with a 'yes' or 'no' only."},
            ]          
        )

        # response['choices'][0]['message']['content'] = 'yes'
    
        # Add the length of the text to the current length
        if ("yes" in (response['choices'][0]['message']['content'].lower())):
            cur_len += int(tokens) + 4
            returns.append(document)
            temp.append(title)
            temp.append(page)
            temp.append(coords)
            sources.append(temp)
            
    # Return the context
    return(("\n\n###\n\n".join(returns)), sources, question_en)

def get_previous_questions(history):
    # print("----------------------------- History -----------------------------")
    # print(history)
    # print("\n")
    questions= [[elem['query_en'], elem['answer_en']] for elem in history]
    prev_questions = []
    for elem in history:
        prev_questions.append({'role':'user','content':elem['query_en']})
        prev_questions.append({'role':'assistant','content':elem['answer_en']})
    return prev_questions

def format_previous_questions(prev_questions):
    return 0

def generate_answer(question_es, history, deployment=deployment_name):
    prev_questions = get_previous_questions(history)
    role_sys = {"role": "system", "content": "You are a doctor in obstetrics."}
    context, sources, question_en = create_context_es(question_es, prev_questions, max_len=1800, size="ada")
    nb_tokens=0
    for quest, ans in prev_questions:
        nb_tokens+=len(quest.split())+len(ans.split())
    if nb_tokens<2000:
        prev_questions.insert(0, role_sys)
        prev_questions.append({"role": "user", "content": f"""##Provided Information## {context} \n\n---\n\##Question## {question_en} \
                    \n\n---\n\Based on the ##Provided Information## above and its relevant topic, and continuing the previous conversation ##Previous \
                    conversation##, answer the ##Question##. The answer must be short, and fit in maximum 2 sentences. If the question cannot be answered using the provided informations, or if there are no provided informations, \
                 just respond \"I don\'t know\""""})
        # print("----------------------------- Previous questions -----------------------------")
        # print(prev_questions)
        
        response = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages= prev_questions
        )
        answer_en = response['choices'][0]['message']['content']
        answer_es = translate_en_es(answer_en)

        context = context.split("\n###\n")
        return (answer_es, answer_en, question_en, sources)
    else:
        return('You cannot continue this conversation', [])


