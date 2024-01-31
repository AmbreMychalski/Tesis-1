import os
import requests
import json
import openai
import pandas as pd
import numpy as np
from openai.embeddings_utils import distances_from_embeddings

openai.api_key = ""
openai.api_base = "https://invuniandesai.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2023-05-15'

deployment_name='gpt-35-turbo-rfmanrique'

df=pd.read_csv('front/embeddings/embeddings.csv', index_col=0)
df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

def create_context(question, df, max_len=1800, size="ada"):

    """
    Create a context for a question by finding the most similar context from the dataframe
    """
    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002-rfmanrique')['data'][0]['embedding']
    print("q_embeddings\n", q_embeddings)
    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')
    
    returns = []
    sources = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    
        # Add the length of the text to the current length
    for i, row in df.sort_values('distances', ascending=True).iterrows():
        
        if(cur_len > max_len):
            break
        temp = []
        context_chunk = row["text"]
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
        print(response['choices'][0]['message']['content'].lower())
        if ("yes" in (response['choices'][0]['message']['content'].lower())):
            cur_len += row['n_tokens'] + 4
            returns.append(row["text"])
            temp.append(row['title'].split('.txt')[0])
            temp.append(row['page_number'])
            sources.append(temp)
    
        # cur_len += row['n_tokens'] + 4
        # count_context += 1
        # If the context is too long, break
        # if cur_len > max_len:
        #     break
        # Else add it to the text that is being returned
        
        # print("TEST: ","yes" in (response['choices'][0]['message']['content'].lower()))
        # print(response['choices'][0]['message']['content'])
        
    for context in (returns):
        print(context)  
        print()  

    # Return the context
    # return (("\n\n###\n\n".join(returns)), sources)
    return(("\n\n###\n\n".join(returns)), sources)

def generate_answer(question,df_embeddings, deployment=deployment_name):
    context, sources = create_context(question, df_embeddings, max_len=1800, size="ada")
    # print("context: \n\n", context)
    # print("sources: \n\n", sources)
    response = openai.ChatCompletion.create(
        engine= deployment_name, # engine = "deployment_name".
        #prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
        messages=[
            {"role": "system", "content": "You are a doctor in obstetrics."},
            # You are a helpful medical knowledge assistant. Provide useful, complete, and 
            # scientifically-grounded answers to common consumer search queries about 
            # obstetric health.

            {"role": "user", "content": f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:"},
        ]
    )
    # print(response['choices'][0]['message']['content'])
    return ((response['choices'][0]['message']['content']),sources)

