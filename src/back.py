import os
import requests
import json
import openai
import pandas as pd
import numpy as np
from openai.embeddings_utils import distances_from_embeddings

openai.api_key = "cf0bd49030ed4aa6a6509be1cd9d604b"
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
   # print("\n\noui 2 \n\n",q_embeddings)
    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')


    print("oui\n\n",df['text'],df['embeddings'], df['distances'])

    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values('distances', ascending=True).iterrows():

        # Add the length of the text to the current length
        cur_len += row['n_tokens'] + 4

        # If the context is too long, break
        if cur_len > max_len:
            break

        # Else add it to the text that is being returned
        returns.append(row["text"])

    # Return the context
    return "\n\n###\n\n".join(returns)

def generate_answer(question,df_embeddings, deployment=deployment_name):
    context = create_context(question, df_embeddings, max_len=1800, size="ada")
    print("context: \n\n",context)
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
    # print(response)
    # print(response['choices'][0]['message']['content'])
    return response['choices'][0]['message']['content']

