from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from back import *
import json
import io
import atexit
import logging

#app = Flask(__name__)
app = Flask(__name__, static_folder='react_build')
cors = CORS(app)

logging.basicConfig(level=logging.INFO)

History = []

history_path = "Front_React/public/"

def load_history():
    global History
    file_path = history_path+"History.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            History = json.load(f)
            print("load history------------")
            print(History)
    else:
        with io.open(os.path.join(history_path, 'History.json'), 'w') as history_file:
            history_file.write(json.dumps([]))

@app.route('/api/save', methods=['POST'])
def save_history():
    # if (History != []):
    #     print("\nSaving history to file...")
    #     with open("front/public/History.json", "w") as f:
    #         print("-----------------------")
    #         print(History)
    #         json.dump(History, f)
    #     print("History saved successfully.")
    try: 
        History = request.get_json().get('history')
        if (History != [[]]):
            print("\nSaving history to file...")
            print(History)
            with open("front/public/History.json", "w") as f:
                print("-----------------------")
                print(History)
                json.dump(History, f)
            print("History saved successfully.")
        return jsonify({'message': 'succesfully saved'})
    except Exception as e:
        print("erreur")
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/generate-pdf/<int:message_id>/<pdf_name>', methods=['POST', 'GET'])
def generate_pdf(message_id, pdf_name):
    data = request.get_json()
    history = data.get('history')
    for message in history:
        if message['id'] == message_id:
            highlight = message['highlight']
            pages = highlight[pdf_name][0][0]
            coords = highlight[pdf_name][0][1]
            if pages[0] == pages[1]:
                pages = [pages[0]]
    if len(pages) != 0:
        modified_pdf_bytes = highlight_context(pdf_name, pages, coords)
        app.logger.info(f"Generating PDF for message ID: {highlight}. {pages}, {coords}")
        return send_file(
                modified_pdf_bytes,
                mimetype='application/pdf',
                download_name=f'{pdf_name}.pdf',
                as_attachment=False
            )
    else:
        return 'PDF not found'

# Definition of the API returning GPT answer to an obstetric related question
@app.route('/api/query', methods=['POST'])
def receive_question():
    
    try:
        # Recovering of the question data from front
        data = request.get_json()
        question_es = data.get('query')
        print('\n------------------------- query -------------------------\n')
        print(question_es)
        if len(question_es)==0 or question_es.isspace():
            return jsonify({'error': 'La pregunta esta vacia'}), 204
        history = data.get('history')
        if history is None:
            history=[]
        if len(question_es)==0:
            question_es.append(" ")
        # Generation of the answer
        #(answer_es, answer_en, question_en, sources) =  generate_answer(question_es, History, deployment=deployment_name)
        print("\n------------------------- history -------------------------\n", history)
        (answer_es, answer_en, question_en, sources) =  generate_answer(question_es, history, deployment=deployment_name)
        print('\n------------------------- answer -------------------------\n')
        print(answer_es)
        sources_to_print = {}
        sources_to_highlight = {}
        for src in sources:
            if src[0] in sources_to_print:
                sources_to_print[src[0]].append(src[1].replace("[","").replace("]","").replace("(", '').replace(")", '').replace("'","").split(', '))
                pages = src[1].replace("[","").replace("]","").replace("(", '').replace(")", '').replace("'","").split(', ')
                pages = [ int(p) for p in pages]
                coords = src[2].replace('(', '').replace(')', '').split(', ')
                coords = [ float(c) for c in coords]
                sources_to_highlight[src[0]].append([pages, coords])
            else:
                sources_to_print[src[0]] = [src[1].replace("[","").replace("]","").replace("(", '').replace(")", '').replace("'","").split(', ')]
                pages = src[1].replace("[","").replace("]","").replace("(", '').replace(")", '').replace("'","").split(', ')
                pages = [ int(p) for p in pages]
                coords = src[2].replace('(', '').replace(')', '').split(', ')
                coords = [ float(c) for c in coords]
                sources_to_highlight[src[0]] = [[pages, coords]]
            
        # Creation of the json answer
        if "I don\'t know" in answer_en:
            sources_to_print={}
        if len(history)==0:
            q_id = 0
        else:
            q_id = history[-1]['id']+1
        response = {
            'id': q_id,
            'query_es': f"{question_es}",
            'query_en': f'{question_en}',
            'answer_es': f"{answer_es}",
            'answer_en': f"{answer_en}",
            'sources':sources_to_print,
            'highlight':sources_to_highlight,
        }
        
        return jsonify({'message': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    load_history()
    atexit.register(save_history)
                    
    app.run(port=3001, debug=True) 