import os
import requests
import json
import openai
import pandas as pd
import numpy as np
from openai.embeddings_utils import distances_from_embeddings
import chromadb

openai.api_key = os.getenv("OpenAIKey")
openai.api_base = "https://invuniandesai.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2023-05-15'

deployment_name='gpt-35-turbo-rfmanrique'

print(os.getcwd())
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="collection_test")

embedding_path = os.path.abspath('src/embeddings_complete.csv')
df=pd.read_csv('front/embeddings/embeddings.csv', index_col=0)
df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

collection.add(
            embeddings=[arr.tolist() for arr in df['embeddings'].to_list()],
            documents= df['text'].to_list(),
            metadatas = df.apply(lambda row: {"title": row['title'].replace(".txt", ""), "page": str(row['page_number']), "tokens": str(row['n_tokens'])}, axis=1).tolist(),
            ids=[str(i) for i in range(len(df))]
        )

def create_context(question, df, prev_questions, max_len=1800, size="ada"):

    # HyDE:
    
    first_response = openai.ChatCompletion.create(
            engine= deployment_name, # engine = "deployment_name".
            messages=[
                {"role": "system", "content": "You are a doctor in obstetrics."},
                # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                # scientifically-grounded answers to common consumer search queries about 
                # obstetric health.

                {"role": "user", "content": f"Reword the question to correct the grammatical errors and then answer the question taking into account the previous asked questions. In your answer you must include the previous reword question and the answer./\n\n---\n\nPrevious questions and their answers: {prev_questions}\n\nQuestion: {question}\nAnswer after the colon, with the reword question and the answer, without making a separation between the reword question and the answer:"},
            ]          
        )
    print("-------------- FIRST RESPONSE --------------\n", first_response['choices'][0]['message']['content'], "\n\n")

    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    # Get the embeddings for the question
    # q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002-rfmanrique')['data'][0]['embedding']
    
    # Use the first answer of chatGPT to create the context
    q_embeddings = openai.Embedding.create(input=first_response['choices'][0]['message']['content'], engine='text-embedding-ada-002-rfmanrique')['data'][0]['embedding']
    # print("q_embeddings\n", q_embeddings)
    # Get the distances from the embeddings
    # df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')
    results = collection.query(query_embeddings=q_embeddings, n_results=10)

    returns = []
    sources = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    
        # Add the length of the text to the current length
    # for i, row in df.sort_values('distances', ascending=True).iterrows():
    for i in range(len(results['ids'][0])):
        print("**************************************************************")
        print(results['metadatas'][0][i])
        document = results['documents'][0][i]
        title = results['metadatas'][0][i]['title']
        page = results['metadatas'][0][i]['page']
        tokens= results['metadatas'][0][i]['tokens']
        print("VISU:", document, title, page, tokens)
        if(cur_len > max_len):
            break
        temp = []
        # context_chunk = row["text"]
        context_chunk = document

        response = openai.ChatCompletion.create(
            engine= deployment_name, # engine = "deployment_name".
            #prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
            messages=[
                {"role": "system", "content": "You are a doctor in obstetrics."},
                # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                # scientifically-grounded answers to common consumer search queries about 
                # obstetric health.

                {"role": "user", "content": f"Evaluate the relevance of the following context snippet to answer the following question in the field of obstetrics: {context_chunk}\n\n---\n\nThe question is: {question}\nDo you consider it relevant for providing an accurate response in this field? Please respond with a 'yes' or 'no' only."},
            ]          
        )
        print("response in lower", response['choices'][0]['message']['content'].lower())
        # response['choices'][0]['message']['content'] = 'yes'
        
        if ("yes" in (response['choices'][0]['message']['content'].lower())):
            cur_len += int(tokens) + 4
            returns.append(document)
            temp.append(title)
            temp.append(page)
            sources.append(temp)
    
        # cur_len += row['n_tokens'] + 4
        # count_context += 1
        # If the context is too long, break
        # if cur_len > max_len:
        #     break
        # Else add it to the text that is being returned
        
        # print("TEST: ","yes" in (response['choices'][0]['message']['content'].lower()))
        # print(response['choices'][0]['message']['content'])

    # Return the context
    # return (("\n\n###\n\n".join(returns)), sources)
    return(("\n\n###\n\n".join(returns)), sources)

def generate_answer(question,df_embeddings, history, deployment=deployment_name):
    prev_questions = get_previous_questions(history)
    context, sources = create_context(question, df_embeddings, prev_questions, max_len=1800, size="ada")
    # print("context: \n\n", context)
    # print("sources: \n\n", sources)
    nb_tokens=0
    for quest, ans in prev_questions:
        print("------------prev questions\n", quest, "-->", ans)
        nb_tokens+=len(quest.split())+len(ans.split())
    print("\n\n+++++++++++++++++", nb_tokens)
    if nb_tokens<2000:
        response = openai.ChatCompletion.create(
            engine= deployment_name, # engine = "deployment_name".
            #prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
            messages=[
                {"role": "system", "content": "You are a doctor in obstetrics."},
                # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                # scientifically-grounded answers to common consumer search queries about 
                # obstetric health.

                {"role": "user", "content": f"Answer the question based on the context below and on the previous questions and the answers that have already been given. Give more importance to the previous question. If the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nPrevious questions and their answers: {prev_questions}\n\nQuestion: {question}\nAnswer:"},
            ]
        )
        # print(response['choices'][0]['message']['content'])
        return ((response['choices'][0]['message']['content']),sources)
    else:
        return('You cannot continue this conversation', [])

def get_previous_questions(history):
    questions= [[elem['query'], elem['answer']] for elem in history]
    print(f"The previous questions are {questions}")
    return questions

