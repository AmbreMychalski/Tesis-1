import os
import openai
import chromadb
import pandas as pd

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
output_file = 'dialogues_gpt35_chunks500_marine.csv'

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


if __name__ == '__main__':
    print("Generating conversations with", deployment_name)
    generate_n_row_conversation(3)
    