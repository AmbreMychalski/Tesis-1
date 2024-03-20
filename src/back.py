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
    txt_en=''
    try:
        translated = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages=[
                {"role": "system", "content": "You're a translator, and you translate between Spanish and English ."},
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

def translate_en_es(txt_en):
    translated = openai.ChatCompletion.create(
        engine= deployment_name, 
        messages=[
            {"role": "system", "content": "You're a translator, and you translate between English and Spanish ."},
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

def create_context(question, prev_questions, max_len=1800, size="ada"):
    global current_sources
    current_sources = []

    # HyDE:
    first_response = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages=[
                {"role": "system", "content": "You are a doctor in obstetrics."},
                {"role": "user", "content": f"Reword the question to correct the grammatical errors and then answer the question considering the previous asked questions. In your answer you must include the previous reword question and the answer. \n\n---\n\nPrevious questions and their answers: {prev_questions}\n\nQuestion: {question}\nAnswer after the colon, with the reword question and the answer, without making a separation between the reword question and the answer:"},
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
    results = collection.query(query_embeddings=q_embeddings, n_results=50)

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
                {"role": "user", "content": f"Evaluate the relevance of the following context snippet to answer the following question in the field of obstetrics: {context_chunk}\n\nThe question is: {question}\nDo you consider it relevant for providing an accurate response in this field? Respond with a 'yes' or 'no' only."},
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
    results = collection.query(query_embeddings=q_embeddings, n_results=50)

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
                {"role": "user", "content": f"Evaluate the relevance of the following context snippet to answer the following question in the field of obstetrics: {context_chunk}\n\nThe question is: {question}\nDo you consider it relevant for providing an accurate response in this field? Respond with a 'yes' or 'no' only."},
            ]     
        )
        time.sleep(0.1)

        # response['choices'][0]['message']['content'] = 'yes'
    
        # Add the length of the text to the current length
        if ("yes" in (response['choices'][0]['message']['content'].lower())):
            cur_len += int(tokens) + 4
            returns.append(document)
            temp.append(title)
            temp.append(page)
            temp.append(coords)
            sources.append(temp)
            print('---index---', i)
    
    for i in range(len(sources)):
        src = sources[i][1].replace('(', '').replace(')', '').split(', ')
        for j in range(len(src)):
            src[j]=int(src[j])
        if src[0]==src[1]:
            sources[i][1] = "("+str(src[0])+")"


    # print("-----------------CONTEXTBIS---------------")
    # for i in returns:
    #     print(i)
    #     print(len(i))
    # print("-----------------ENDCONTEXTBIS---------------")
            
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
    role_sys = {"role": "system", "content": "You are a specialized obstetric chatbot. You respond to questions from other doctors regarding obstetrical emergencies."}
    context, sources, question_en = create_context_es(question_es, prev_questions, max_len=1800, size="ada")
    nb_tokens=0
    # print("---------------CONTEXT------------------")
    # print(context)
    # print("---------------ENDCONTEXT------------------")
    if 'An error occurred:' in question_en:
        answer_es = 'Ocurrió un error: La respuesta fue filtrada debido a que la solicitud activó la política de gestión de contenido de Azure OpenAI. Por favor, modifica tu solicitud y vuelve a intentarlo. Para obtener más información sobre nuestras políticas de filtrado de contenido, por favor lee nuestra documentación: https://go.microsoft.com/fwlink/?linkid=2198766'
        return (answer_es, question_en, '', sources)

    for quest, ans in prev_questions:
        nb_tokens+=len(quest.split())+len(ans.split())
    if nb_tokens<2000:
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
        # print("----------------------------- Previous questions -----------------------------")
        # print(prev_questions)
        # print("----------------------------- End Previous questions -----------------------------")
        
        response = openai.ChatCompletion.create(
            engine= deployment_name, 
            messages= prev_questions
        )
        answer_en = response['choices'][0]['message']['content']
        print("----------------------------- Answer EN -----------------------------")
        print(answer_en )
        answer_es = translate_en_es(answer_en)
        print("----------------------------- Answer ES -----------------------------")
        print(answer_es )
        return (answer_es, answer_en, question_en, sources)
    else:
        return('You cannot continue this conversation', [])


