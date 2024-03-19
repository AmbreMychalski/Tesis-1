import pandas as pd
from back import *
import time

path_questionEval = "c:/Users/ambre/Desktop/INSA/5A/202320/Tesis_I/EVALUATION/"
questions_file = "questions.csv"
answer_file = "evaluation_gpt4_chunks500_nchunk50.xlsx"
encoding = 'utf-8'
History = []

print(deployment_name)

def read_QuestionCSV(file_path):
    questions_df = pd.read_csv(file_path)
    return questions_df

def receive_question(question_es):
    print(question_es)
    try:
        (answer_es, answer_en, question_en, sources) =  generate_answer(question_es, History, deployment=deployment_name)    
        src = ''
        if len(sources)>0:
            for i in range(len(sources)):
                s = sources[i][0] +' page: '+ sources[i][1].replace('(', '').replace(')', '')
                if i==0:
                    src += s
                else:
                    src += '| '+s
        return (answer_es, src)
    except Exception as e:
        print("An error occurred:", e)
        return(e, '')


if __name__ == '__main__':
    questions_df = read_QuestionCSV(path_questionEval+questions_file)
    answers_df = questions_df.copy()
    for index, row in questions_df.iterrows():
        print(index)
        (answer, sources) = receive_question(row['Questions'])

        answers_df.at[index, 'Answers'] = answer
        answers_df.at[index, 'Sources'] = sources

        time.sleep(2)
    answers_df.to_excel(path_questionEval+answer_file, encoding=encoding, index=False)