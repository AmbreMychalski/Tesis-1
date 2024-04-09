# Code created on the base of https://medium.com/@xuebinbin12/fine-tuning-chat-based-llm-with-multi-turn-conversational-data-part-i-d8c64d01a20d
# Bin Xue, Jan 17, 2024, Fine-Tuning chat-based LLM with Multi-Turn Conversational Data (Part I)

import os
import openai
import pandas as pd
import re
from transformers import AutoTokenizer
import json
from huggingface_hub import login

import torch
from datasets import Dataset
from trl import DataCollatorForCompletionOnlyLM

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


embeddings_directory = "front/embeddings/"
dialogues_directory = "front/dialogues/"

input_file = 'embeddings_complete_500_marine.csv'
output_file = 'dialogues_gpt35_chunks1500_marine.csv'
cleaned_dialogue_file = 'cleaned_dialogue_marine.csv'
json_formatted_dialogue_file = 'formatted_dialogue_marine.json'
llama_formatted_dialogue_file = 'llama_formatted_dialogue_marine.csv'


def generate_n_row_conversation(nb_turn=5):
    dialogue = []
    dialogue_template = """<chat><Doctor 1>asks a question \
        <Assistant 1>answers [+detailed explanation] \
        <Doctor 2>further asks from the perspective of real life \
        <Assistant 2>answers [+detailed explanation] \
        <Doctor 3>further asks a question \
        <Assistant 3>answers [+detailed explanation]</chat>"""

    print(nb_turn)
    df = pd.read_csv(embeddings_directory+input_file)
    i=0
    for index, row in df.iterrows():
        i+=1
        if (i%100 ==0):
            df = pd.DataFrame(dialogue, columns = ['dialogue'])
            if i == 100:
                df.to_csv(dialogues_directory+output_file)
            else:
                df.to_csv(dialogues_directory+output_file, mode='a', header=False)
            dialogue = []
        
        print(i)
        reference = row['text']

        response = openai.ChatCompletion.create(
            engine= deployment_name, # engine = "deployment_name".
            messages=[  
                {"role": "system", "content": "You are a specialized doctor in obstetrics."},

                {"role": "user", "content": f"""##Provided Information## {reference} Based on the ##Provided Information## above and its relevant \
                    topic, expand it into a multi-round conversation. The conversation requires you to act as as the chatbot Assistant \
                    specialized in obstetric and interact with a generalist doctor, helping to solve the requests raised by the doctor. The \
                    human will ask multiple various questions/requests to the physician based on the information above \
                    (but the conversation should not include expressions like 'according to the above information'), \
                    and the subsequent questions/requests will be a follow-up based on the previous conversation \
                    history. For every reasonable question/request posed by Human, assistant should provide as \
                    detailed an answer as possible, offering further explanations.  \
                    #Conversation Plan# Example: "<chat><Human 1>:(Word count requirement: x words)XXX <Assistant 1>: \
                    (Word count requirement: x words) XXX <Human 2>:(Word count requirement: x words)XXX <Assistant \
                    2>: (Word count requirement: x words) XXX </chat>", "XXX" is the requirement for the current \
                    conversation content of that role, and "(Word count requirement: x words)" specifies the minimum \
                    word count requirement for utterance of Human or Assistant. It must be noted: the conversation \
                    starts with <chat> as the beginning of the multi-round conversation and ends with </chat> as \
                    the end of the multi-round conversation. The following conversation follows this #Conversation \
                    Plan# and word count requirements: '{dialogue_template}', a total of {nb_turn} turns of \
                    conversation."""},
            ]          
        )
        dialogue.append(response['choices'][0]['message']['content'])
        print(response['choices'][0]['message']['content'])
        print("------------------------------------------------------")
    if dialogue:
        df = pd.DataFrame(dialogue, columns = ['dialogue'])
        df.to_csv(dialogues_directory+output_file, mode='a', header=False)

def clean_generated_dialogues(dialogue_csv_file):
    df = pd.read_csv(dialogues_directory+dialogue_csv_file)
    df = df.drop(columns=['Unnamed: 0'])
    print(df.head())
    print("\n-------------- Cleaning dialogues from non wanting patterns -------------")
    df = df.replace('\n', '', regex=True)
    df = df.replace('>: ', '>', regex=True)
    # df = df.replace('"<', '', regex=True)
    # df = df.replace('>"', '', regex=True)
    df = df.replace(r'\(Word count requirement: \d+ words\)', '', regex=True)
    df = df.replace(r'</Assistant \d+>', '', regex=True)
    df = df.replace(r'</Doctor \d+>', '', regex=True)
    df = df.replace(r'</chat><chat>', '', regex=True)
    df = df.replace(r'<chat><chat>', '<chat>', regex=True)
    df = df.replace(r'</chat></chat>', '</chat>', regex=True)
    # print(df.loc[[0]])
    for index, row in df.iterrows():
        if not row['dialogue'].endswith('</chat>'):
            df.at[index, 'dialogue'] += ' </chat>'
    print(df.head())
    df.to_csv(dialogues_directory+cleaned_dialogue_file, index=False)
    
def format_cleaned_json_dialogues(clean_dialogue_csv):
    df = pd.read_csv(dialogues_directory+clean_dialogue_csv)

    processed_dialogue = []
    last_role = None
    pattern = r'<(Doctor|Assistant) (.*?)>(.*?)(?=<)'
    for index, row in df.iterrows():
        last_role = None
        json_diag = []
        dialogue = row['dialogue']
        for match in re.finditer(pattern, dialogue):
            role = match.group(1).strip()
            content = match.group(3).strip()
            if role == "Doctor" and role != last_role:
                content = content.replace('<chat>', '').replace('</chat>', '')
                json_diag.append({'role': 'user', 'content': content})
                last_role = role
            elif role == "Assistant" and role != last_role:
                content = content.replace('<chat>', '').replace('</chat>', '')
                json_diag.append({'role': 'assistant', 'content': content})
                last_role = role
        processed_dialogue.append(json_diag)

    final_processed_dialogue = []
    for instance in processed_dialogue:
        if len(instance) > 1:  # Suppress instances with only one question from the user or one response from the assistant
            final_processed_dialogue.append(instance)
    print(len(final_processed_dialogue))

    # Save in json format
    with open(dialogues_directory+json_formatted_dialogue_file, 'w') as f:
        json.dump(final_processed_dialogue, f)
    
def format_to_llama(formatted_json_dialogue_file):
    # Initialize the tokenizer with llama model
    checkpoint = 'meta-llama/Llama-2-7b-chat-hf'
    # tokenizer = AutoTokenizer.from_pretrained(checkpoint,
    #                                             max_length=1500,
    #                                             padding="max_length")
    tokenizer = AutoTokenizer.from_pretrained(checkpoint,
                                         padding='right')
    tokenizer.add_special_tokens({'pad_token':'[PAD]'})

    # Format the json dialogues into a pandas dataframe
    with open(dialogues_directory+formatted_json_dialogue_file, "r") as f:
        json_dialogue = json.load(f)

    formatted_conversations = []

    for conversation in json_dialogue:
        conv = {'dialogue': conversation}
        formatted_conversations.append(conv)

    df = pd.json_normalize(formatted_conversations)
    # print(df.head())
    # print(df.iloc[0]['dialogue'], type(df.iloc[0]['dialogue']))

    # Format the conversations in the dataframe with llama multi-turns conversation format
    print(repr(tokenizer.pad_token))
    df['template_formatted_conversation_turns'] = df['dialogue'].apply(lambda x: tokenizer.apply_chat_template(x,tokenize=False, padding=True))
    
    # print(df.head())
    # print(df.iloc[0]['template_formatted_conversation_turns'])

    # Save the formatted conversations into .csv file
    print(f"vocab length={len(tokenizer.get_vocab())}")
    df.to_csv(dialogues_directory+llama_formatted_dialogue_file, index=False)

    # Dataset Construction
    dataset = Dataset.from_list(df['template_formatted_conversation_turns'].apply(lambda x: tokenizer(x, return_length=True)).to_list()) 
    response_template = '[/INST]'
    instruction_template = '[INST]'
    collator = DataCollatorForCompletionOnlyLM(instruction_template=instruction_template, response_template=response_template, tokenizer=tokenizer)
    
    # Example of created batch
    print('Example of created batch:')
    dataloader = torch.utils.data.DataLoader(dataset=dataset, 
                                         collate_fn=collator, 
                                         batch_size=2)
    for batch in dataloader:
        print(batch)
        break
    print("Dataset size:", len(dataset))
    # Add to HuggingFace
    login()
    dataset.push_to_hub("Druluth/musicoterapy_qa_llama2-1046")
    # dataset.push_to_hub("Druluth/obstetric_qa_llama2-348")

if __name__ == '__main__':
    print("Generating conversations with", deployment_name)
    # generate_n_row_conversation(3)
    # clean_generated_dialogues(output_file)
    # format_cleaned_json_dialogues(cleaned_dialogue_file)
    format_to_llama(json_formatted_dialogue_file)
    # max_token_dataset()
    