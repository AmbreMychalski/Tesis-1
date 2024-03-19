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
import fitz
import re

path_dataset = './front/public/RawDataset/'

openai.api_key = os.getenv("OpenAIKey")
openai.api_base = "https://invuniandesai.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2023-05-15'

MAX_TOKENS = 1000

# Know if the last file is in english or not
last_file = ''
last_file_en = True
tokenizer = tiktoken.get_encoding("cl100k_base")

rawDataset = "front/rawDataset/"
txt_directory = "front/ProcessedDataset/txt/"
scraped_directory = "front/ProcessedDataset/scraped/"
embeddings_directory = "front/embeddings/"

deployment_name='gpt-35-turbo-rfmanrique'

def extract_text_with_coordinates():
    raw_text = []
    processed_text = []
    for filename in os.listdir(rawDataset):
        doc = fitz.open(path_dataset+filename)
        print(filename)
        fname = filename.replace('.pdf', '')
        for page in doc:

            blocklist = page.get_text("blocks")
            for i in range(len(blocklist)):
                rect = blocklist[i][0:4]
                text = blocklist[i][4].replace(",",' ').replace(";", " ").replace("\n", " ").replace("  ", " ")
                if '. ' in text:
                    end_sentence = re.split(r'(?<=[.!?])\s+', text)
                    end_sentence = [s.strip() for s in end_sentence]
                    for sent in end_sentence:
                        if len(sent)>0:
                            if 'downloaded' in sent.lower() or 'copyright' in sent.lower() or '©' in sent.lower() or 'http' in sent.lower():
                                continue
                            raw_text.append((fname, sent, rect, page.number+1))
                # print('\n', blocklist[i],'---', rect, ' - ', text, '\n')
                else:
                    if 'downloaded' in text.lower() or 'copyright' in text.lower() or '©' in text.lower() or 'http' in text.lower():
                        continue
                    raw_text.append((fname, text, rect, page.number+1)) 
    current_sent = ''
    coord_init_sent = raw_text[1][2][0:2]
    coord_end_sent = raw_text[1][2][2:4]
    page_init_sent = raw_text[1][3]
    page_end_sent = raw_text[1][3]
    for tuple in raw_text:
        current_sent += tuple[1]
        if tuple[1].endswith('.') or tuple[1].endswith('!') or tuple[1].endswith('?'):
            coord_end_sent = tuple[2][2:4]
            page_end_sent = tuple[3]
            processed_text.append((tuple[0], current_sent, coord_init_sent+coord_end_sent, (page_init_sent,page_end_sent)))
            current_sent = ''
            coord_init_sent = tuple[2][0:2]
            page_init_sent = tuple[3]

    df = pd.DataFrame(processed_text, columns = ['fname', 'text', 'coords', 'page'])
    df.to_csv(scraped_directory+'scraped_test.csv')
    return df

def make_chunks(df):
    global MAX_TOKENS
    global tokenizer
    # df = pd.read_csv(scraped_directory+'/scraped_test.csv', index_col=0)
    # df.columns = ['fname', 'text', 'coords', 'page']
    
    df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))

    tokens_so_far = 0
    chunks_text = []
    fname = df.iloc[0]['fname']
    current_chunk = ''
    coord_init_chunk = df.iloc[0]['coords'][0:2]
    coord_end_chunk = df.iloc[0]['coords'][2:4]
    page_init_chunk = df.iloc[0]['page'][0]
    page_end_chunk = df.iloc[0]['page'][1]
    for row in df.iterrows():
        # If the text is None, go to the next row
        if row[1]['text'] is None:
            continue

        if row[1]['n_tokens']>MAX_TOKENS:
            # Do something
            continue
        # if row[1]['fname']!=fname:
        #     print(row[1]['fname'])

        if tokens_so_far + row[1]['n_tokens'] > MAX_TOKENS or row[1]['fname']!=fname:
            
            chunks_text.append((fname, current_chunk, coord_init_chunk+coord_end_chunk, (page_init_chunk,page_end_chunk), tokens_so_far))
            fname = row[1]['fname']
            current_chunk = row[1]['text']
            coord_init_chunk = row[1]['coords'][0:2]
            page_init_chunk = row[1]['page'][1]
            coord_end_chunk = row[1]['coords'][2:4]
            page_end_chunk = row[1]['page'][1]   
            tokens_so_far = row[1]['n_tokens']
            
        else:
            current_chunk+= ' '
            current_chunk += row[1]['text']
            tokens_so_far += row[1]['n_tokens'] + 1   
            coord_end_chunk = row[1]['coords'][2:4]
            page_end_chunk = row[1]['page'][1]         

    df2 = pd.DataFrame(chunks_text, columns = ['fname', 'text', 'coords', 'page', 'n_tokens'])
    df2.to_csv(scraped_directory+'scraped_chunks.csv')
    return df2

def suppress_after_reference(text):
    lower_text = text.lower()
    search_term = 'references 1.'

    index = lower_text.find(search_term)
    if index != -1:
        res = text[:index]
        return res
    else:
        search_term = 'referencias 1.'
        index = lower_text.find(search_term)
        if index != -1:
            res = text[:index]
            return res
        else:
            return text
    
def extract_references(df):
    last_file_ref = ''
    index_to_drop = []
    for index, row in df.iterrows():
        if row['fname'] != 'FIGO recommendations on the management of postpartum hemorrhage 2022':
            if 'references 1.' in row['text'].lower() or 'referencias 1.' in row['text'].lower():
                last_file_ref = row['fname']
                df.at[index, 'text'] = suppress_after_reference(row['text'])
                # print(last_file_ref)
                # print(row['page'], df.at[index, 'text'])
                # print('-----------------')
            elif row['fname'] == last_file_ref:
                # print(row['fname'], last_file_ref)
                # print(row['page'], df.at[index, 'text'])
                # print('-----------------')
                index_to_drop.append(index)
    # print(index_to_drop)
    df = df.drop(index=index_to_drop)
    df.to_csv(scraped_directory+'scraped_without_ref.csv')
    return df

def make_traductions(df):
    global tokenizer
    last_file = ''
    last_file_en = True
    for index, row in df.iterrows():
        if last_file != row['fname']:
            last_file_en = True
            last_file = row['fname']
            translated = openai.ChatCompletion.create(
                    engine= deployment_name, 
                    messages=[
                        {"role": "system", "content": "You're a translator, and you translate between Spanish and English ."},
                        # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                        # scientifically-grounded answers to common consumer search queries about 
                        # obstetric health.
                        # If the text is written in spanish translate it in english. Write the translation after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible:

                        {"role": "user", "content": f"Analyse the differents words of the following text./\n\n---\n\n/Text: {row['fname']}\n\n/Is this written in spanish? Answer by yes or no"},
                    ]          
                )
            # print("\n-------------- FIRST RESPONSE --------------\n", translated['choices'][0]['message']['content'])
            # print("TITLE", row[1]['fname'], "\n")
            if 'yes' in translated['choices'][0]['message']['content'].lower():
                last_file_en = False
        if last_file_en == False:
            # print("TITLE", row['fname'], last_file_en, "\n")
            # print("\n***********To translate***********\n")
            # print(df.at[index, 'text'])
            # print(row[1]['text'])
            translated = openai.ChatCompletion.create(
                engine= deployment_name, 
                messages=[
                    {"role": "system", "content": "You're a translator, and you translate between Spanish and English ."},
                    # You are a helpful medical knowledge assistant. Provide useful, complete, and 
                    # scientifically-grounded answers to common consumer search queries about 
                    # obstetric health.
                    # If the text is written in spanish translate it in english. Write the translation after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible:

                    {"role": "user", "content": f"Translate the following text in english./\n\n---\n\n/{df.at[index, 'text']}\n\n/Write the translation only after the colons. You have to keep the translated text as close semantically and syntactically to its original version as possible. Keep any character you don't understand unmodified:"},
                ]          
            )
            # print("\n-----------------ORIGINAL---------------:", row['text'], '\n')
            # print("-----------------TRANSLATION---------------:\n", translated['choices'][0]['message']['content'], '\n')
            
            df.at[index, 'text'] = translated['choices'][0]['message']['content'] # ' '
    df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))
    df.to_csv(scraped_directory+'shorteneds.csv')
    return df

def emb_with_delay(text):
    time.sleep(0.5)
    return openai.Embedding.create(input=text, engine='text-embedding-ada-002-rfmanrique')['data'][0]['embedding']

def make_embed(df):
    df['embeddings'] = df.text.apply(emb_with_delay)
    df.to_csv(embeddings_directory+'embeddings.csv')


if __name__ == '__main__':
    
    # text_with_coordinates = extract_text_with_coordinates()
    # text_in_chunks = make_chunks(text_with_coordinates)
    # text_without_ref = extract_references(text_in_chunks)
    # text_trad = make_traductions(text_without_ref)
    # make_embed(text_trad)
    
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
                metadatas = df_complete.apply(lambda row: {"title": row['fname'], "page": str(row['page']), "coords": str(row['coords']), "tokens": str(row['n_tokens'])}, axis=1).tolist(),
                ids=[str(i) for i in range(len(df_complete))]
            )
