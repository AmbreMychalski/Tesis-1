from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from back import *
import json
import ast
import io
import atexit

app = Flask(__name__)
cors = CORS(app)

History = []

def load_history():
    global History
    file_path = "front/public/History.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            History = json.load(f)
            print("load history------------")
            print(History)
    else:
        with io.open(os.path.join("front/public/", 'History.json'), 'w') as history_file:
            history_file.write(json.dumps([]))


def save_history():
    if (History != []):
        print("\nSaving history to file...")
        with open("front/public/History.json", "w") as f:
            print("-----------------------")
            print(History)
            json.dump(History, f)
        print("History saved successfully.")

# Definition of the API returning GPT answer to an obstetric related question
@app.route('/api/query', methods=['POST'])
def receive_question():
    try:
        # Recovering of the question data from front
        data = request.get_json()
        question = data.get('query')
        if len(question)==0:
            question.append(" ")
        print("question:", question)

        # Recovering the embeddings
        df_embeddings=pd.read_csv('front/embeddings/embeddings.csv', index_col=0)
        df_embeddings['embeddings'] = df_embeddings['embeddings'].apply(eval).apply(np.array)
        #print(df_embeddings.head())
        # Generation of the answer
        print(History)
        (answer, sources) =  generate_answer(question,df_embeddings, History, deployment=deployment_name)
        sources_to_print = {}
        for src in sources:
            if src[0] in sources_to_print:
                sources_to_print[src[0]].append(src[1].replace("[","").replace("]","").replace("'","").split(', '))
            else:
                sources_to_print[src[0]] = [src[1].replace("[","").replace("]","").replace("'","").split(', ')]

        print(sources_to_print)
        
# Example of question: What is oxytocin and what is it purpose in obstetric?
        # print(answer,set(sources))
        # Creation of the json answer
        if "I don\'t know" in answer:
            sources_to_print={}
        response = {
            'query': f"{question}",
            'answer': f"{answer}",
            'sources':sources_to_print,
        }
        print("RESPONSE---------\n", response)
        History.append(response)
        print("\n\nANSWER", History)
        return jsonify({'message': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    load_history()
    atexit.register(save_history)
    app.run(port=3001, debug=True) 