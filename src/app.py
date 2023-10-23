from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from back import *

app = Flask(__name__)
cors = CORS(app)

# Definition of the API returning GPT answer to an obstetric related question
@app.route('/api/query', methods=['POST'])
def receive_question():
    try:
        # Recovering of the question data from front
        data = request.get_json()
        question = data.get('query')
        print(question)

        # Recovering the embeddings
        df_embeddings=pd.read_csv('front/embeddings/embeddings2.csv', index_col=0)
        df_embeddings['embeddings'] = df_embeddings['embeddings'].apply(eval).apply(np.array)
        # Generation of the answer
        (answer, sources) =  generate_answer(question,df_embeddings, deployment=deployment_name)
# Example of question: What is oxytocin and what is it purpose in obstetric?
        print(answer,set(sources))
        # Creation of the json answer
        response = {
            'message': f"{question}",
            'answer': f"{answer}",
            'sources':f"{json.dumps(list(set(sources)))}",
        }
        
        return jsonify({'message': response})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=3001, debug=True) 