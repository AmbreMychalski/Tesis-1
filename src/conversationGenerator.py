import os
import openai
import chromadb
import pandas as pd

# openai.api_key = os.getenv("OpenAIKey") #gpt 3.5
openai.api_key = os.getenv("OpenAIKey_gpt4") #gpt 4
openai.api_base = "https://invuniandesai-2.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2023-05-15'

deployment_name='gpt-4-rfmanrique'

# deployment_name='gpt-35-turbo-rfmanrique'
embeddings_directory = "front/embeddings/"
dialogues_directory = "front/dialogues/"

dialogue = []

def generate_n_row_conversation(nb_turn=5):

    dialogue_template = """<chat><Doctor 1>:(word count: 100 words)asks a question <Obstetrician 1>:(word
        count: 200 words)answers [+detailed explanation] <Doctor 2>:(word count: 150 words)further asks
        from the perspective of real life <Obstetrician 2>:(word count: 100 words)answers [+detailed
        explanation] <Doctor 3>:(word count: 50 words)further asks a question <Obstetrician 3>:(word count:
        150 words)answers [+detailed explanation] </chat>"""

    print(nb_turn)
    df = pd.read_csv(embeddings_directory+'embeddings.csv')
    i=0
    for index, row in df.iterrows():
        i+=1
        if (i>3):
            break

        # print(row['text'])
        reference = row['text']

        response = openai.ChatCompletion.create(
            engine= deployment_name, # engine = "deployment_name".
            messages=[  
                {"role": "system", "content": "You are a specialized doctor in obstetrics."},

                {"role": "user", "content": f"""##Provided Information## {reference} Based on the ##Provided Information## above and its relevant
                    topic, expand it into a multi-round conversation. The conversation requires you to act as the
                    physician specialized in obstetric and interact with a generalist doctor, helping to solve the requests raised by the doctor. The
                    human will ask multiple various questions/requests to the physician based on the information above
                    (but the conversation should not include expressions like 'according to the above information'),
                    and the subsequent questions/requests will be a follow-up based on the previous conversation
                    history. For every reasonable question/request posed by Human, physician should provide as
                    detailed an answer as possible, offering further explanations. For unreasonable
                    requests from Human (those that are harmful to society, immoral, or illegal), obstetric physician will
                    refuse to answer and explain the reason for not answering, while also providing reasonable advice
                    to avoid such actions.
                    #Conversation Plan# Example: '<chat><Human 1>:(Word count requirement: x words)XXX <physician 1>:
                    (Word count requirement: x words) XXX <Human 2>:(Word count requirement: x words)XXX <physician
                    2>: (Word count requirement: x words) XXX </chat>', 'XXX' is the requirement for the current
                    conversation content of that role, and '(Word count requirement: x words)' specifies the minimum
                    word count requirement for utterance of Human or physician. It must be noted: the conversation
                    starts with <chat> as the beginning of the multi-round conversation and ends with </chat> as
                    the end of the multi-round conversation. The following conversation follows this #Conversation
                    Plan# and word count requirements: '{dialogue_template}', a total of {nb_turn} turns of
                    conversation."""},
            ]          
        )
        dialogue.append(response['choices'][0]['message']['content'])
        print(dialogue)
    df = pd.DataFrame(dialogue, columns = ['dialogue'])
    df.to_csv(dialogues_directory+'dialogues.csv')

if __name__ == '__main__':
    print("Generating conversations with", deployment_name)
    generate_n_row_conversation(3)