import os
import requests
import json
import openai
import re
import PyPDF2
import pandas as pd
import tiktoken
import time
import chromadb
import numpy as np

openai.api_key = os.getenv("OpenAIKey")
openai.api_base = "https://invuniandesai.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2023-05-15'

max_tokens = 1000

# Know if the last file is in english or not
last_file = ''
last_file_en = True

rawDataset = "front/rawDataset/"
txt_directory = "front/ProcessedDataset/txt/"
scraped_directory = "front/ProcessedDataset/scraped/"
embeddings_directory = "front/embeddings/"

deployment_name='gpt-35-turbo-rfmanrique'

def process_to_txt():

    for filename in os.listdir(rawDataset):
        # Ouvrir le fichier PDF en mode lecture binaire ('rb')
        with open(rawDataset+filename, 'rb') as pdf_file:
            # Créer un objet PDFReader
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Initialiser une variable pour stocker le texte brut
            raw_text = ''

            # Parcourir chaque page du PDF
            for page_num in range(len(pdf_reader.pages)):
                # Extraire le texte de la page
                page = pdf_reader.pages[page_num]
                raw_text += "###" + str(page_num+1)+ "###" + page.extract_text() + "\n"

        raw_text = raw_text.replace(",",' ')
        filename=filename.replace(".pdf",".txt")
        # Si vous souhaitez sauvegarder le texte brut dans un fichier texte
        with open(txt_directory+filename, 'w', encoding='utf-8') as txt_file:
            txt_file.write(raw_text)

def remove_newlines(serie):
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('\n', ' ')
    return serie

def txt_to_scraped():

    # Create a list to store the text files
    texts=[]
    # Get all the text files in the text directory
    for file in os.listdir(txt_directory):
        # Open the file and read the text
        with open(txt_directory + file, "r", encoding="UTF-8") as f:
            text = f.read()
            texts.append([file.replace(".txt", ""),text])

    # Create a dataframe from the list of texts
    df = pd.DataFrame(texts, columns = ['fname', 'text'])
    print(df['fname'])
    # Set the text column to be the raw text with the newlines removed
    df['text'] = remove_newlines(df.text)
    df.to_csv(scraped_directory+'scraped.csv')

def split_into_many(text, tokenizer, max_tokens = max_tokens):

    # Split the text into sentences
    sentences = text.split('.')

    # Get the number of tokens for each sentence
    n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]

    chunks = []
    tokens_so_far = 0
    chunk = []
    last_page_number = '0'
    # Loop through the sentences and tokens joined together in a tuple
    for sentence, token in zip(sentences, n_tokens):
        page_number = re.findall(r'###(\d+)###', sentence)
        sentence = re.sub(r'###\d+###', '', sentence)
        
        if len(page_number)>0:
            last_page_number=page_number[0]
        # If the number of tokens so far plus the number of tokens in the current sentence is greater
        # than the max number of tokens, then add the chunk to the list of chunks and reset
        # the chunk and tokens so far
        if tokens_so_far + token > max_tokens:
            chunks.append(". ".join(chunk) + ".")
            chunk = []
            tokens_so_far = 0

        # If the number of tokens in the current sentence is greater than the max number of
        # tokens, go to the next sentence
        if token > max_tokens:
            continue

        # Otherwise, add the sentence to the chunk and add the number of tokens to the total
        chunk.append('###'+last_page_number+"###"+sentence)
        tokens_so_far += token + 1

    return chunks

def scraped_shortened():
    global last_file
    global last_file_en

    # Load the cl100k_base tokenizer which is designed to work with the ada-002 model
    tokenizer = tiktoken.get_encoding("cl100k_base")

    df = pd.read_csv(scraped_directory+'/scraped.csv', index_col=0)

    df.columns = ['title', 'text']

    # Tokenize the text and save the number of tokens to a new column
    df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))

    shortened = []
    # Loop through the dataframe
    for row in df.iterrows():
        temp=[]
        # If the text is None, go to the next row
        if row[1]['text'] is None:
            continue

        # If the number of tokens is greater than the max number of tokens, split the text into chunks
        if row[1]['n_tokens'] > max_tokens:
            temp += split_into_many(text=row[1]['text'], tokenizer=tokenizer)
            for text in temp:
                data=[]
                if last_file != row[1]['title']:
                    last_file_en = True
                    last_file = row[1]['title']
                    
                    translated = openai.ChatCompletion.create(
                        engine= deployment_name, 
                        messages=[
                            {"role": "system", "content": "You're a translator, and you translate between Spanish and English ."},
                            # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                            # scientifically-grounded answers to common consumer search queries about 
                            # obstetric health.
                            # If the text is written in spanish translate it in english. Write the translation after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible:

                            {"role": "user", "content": f"Analyse the differents words of the following text./\n\n---\n\n/Text: {row[1]['title']}\n\n/Is this written in spanish? Answer by yes or no"},
                        ]          
                    )
                    # print("\n-------------- FIRST RESPONSE --------------\n", translated['choices'][0]['message']['content'])
                    # print("TITLE", row[1]['title'], "\n")
                    if 'yes' in translated['choices'][0]['message']['content'].lower():
                        last_file_en = False
                print("TITLE", row[1]['title'], last_file_en, "\n")
                page_nb = re.findall(r'###(\d+)###', text)
                page_nb=list(set(page_nb))
                text = re.sub(r'###\d+###', '', text)
                if last_file_en == False:
                    # print("\n***********To translate***********\n")
                    translated = openai.ChatCompletion.create(
                        engine= deployment_name, 
                        messages=[
                            {"role": "system", "content": "You're a translator, and you translate between Spanish and English ."},
                            # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                            # scientifically-grounded answers to common consumer search queries about 
                            # obstetric health.
                            # If the text is written in spanish translate it in english. Write the translation after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible:

                            {"role": "user", "content": f"Translate the following text in english./\n\n---\n\n/{text}\n\n/Write the translation only after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible. Keep any character you don't understand unmodified:"},
                        ]          
                    )
                    # print("\n-----------------ORIGINAL---------------:", text, '\n')
                    # print("-----------------TRANSLATION---------------:\n", translated['choices'][0]['message']['content'], '\n')
                    text = translated['choices'][0]['message']['content']
                # print(page_nb, text)
                data.append(row[1]['title'])
                data.append(page_nb)
                data.append(text)
                shortened.append(data)

        # Otherwise, add the text to the list of shortened texts
        else:
            for text in temp:
                data=[]
                page_nb = re.findall(r'###(\d+)###', text)
                page_nb=list(set(page_nb))
                text = re.sub(r'###\d+###', '', text)
                data.append(row[1]['title'])
                data.append(page_nb)
                data.append(row[1]['text'] )
                shortened.append(data)

    df = pd.DataFrame(shortened, columns = ['title','page_number','text'])
    df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))
    return(df)

def emb_with_delay(text):
    time.sleep(0.5)
    return openai.Embedding.create(input=text, engine='text-embedding-ada-002-rfmanrique')['data'][0]['embedding']

def df_to_embed(df):
    df['embeddings'] = df.text.apply(emb_with_delay)
    df.to_csv(embeddings_directory+'embeddings.csv')

if __name__ == '__main__':
    process_to_txt()
    print('----process to text complete----')
    txt_to_scraped()
    print('----text to scraped complete----')
    df = scraped_shortened()
    print('----scraped shortened complete----')
    df_to_embed(df)
    print('----df to embeddings complete----')

    df_complete = pd.read_csv(embeddings_directory+'embeddings.csv')
    df_complete = df_complete.drop(['Unnamed: 0'], axis=1)

    path = "C:/Users/ambre/Desktop/INSA/5A/202320/Tesis_I/APP/front/src"
    chroma_client = chromadb.PersistentClient(path)
    print(chroma_client.list_collections())

    # Delete a collection
    # chroma_client.delete_collection(name="embedding_db_persist")

    collection = chroma_client.get_collection("embedding_db_persist")
    
    df_complete['embeddings'] = df_complete['embeddings'].apply(eval).apply(np.array)

    collection.add(
                embeddings=[arr.tolist() for arr in df_complete['embeddings'].to_list()],
                documents= df_complete['text'].to_list(),
                metadatas = df_complete.apply(lambda row: {"title": row['title'], "page": str(row['page_number']), "tokens": str(row['n_tokens'])}, axis=1).tolist(),
                ids=[str(i) for i in range(len(df_complete))]
            )
    
