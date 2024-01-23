# Obstetric Chatbot first implementation

Ambre MYCHALSKI - 202326682 - 10/10/2023

## Description

This project consist in a ChatBot with a focus on the obstetric medical domain.

## How to use it ?

### Install
To launch the project, ensure you have Node.js and Python installed on your computer.
You will also need the Flask python module, openai, pandas, matplotlib, plotly, scipy, sklearn and the mui material library.

* To install the Flask module run:
pip install Flask

* To install the openai library run:
pip install openai

* To install the pandas library run:
pip install pandas

* To install the matplotlib library run:
pip install matplotlib

* To install the plotly library run:
pip install plotly

* To install the scipy library run:
pip install scipy

* To install the sklearn library run:
pip install sklearn

* To install the mui material library run:
npm install @mui/material

### Launch the project
Please add your openAI key in the files in the files 'back.py' and 'fileProcessing.py' in the variables 'openai.api_key'.
    
To launch the frontend, open a powershell terminal in the APP/front folder, and run the following command:
    npm start
A web windows will be automatically opened on the search bar view.

To launch the backend, open a python terminal in the APP folder and run:
    python3 front/src/app.py

### Use the project

To use the project, type a question related to the obstetric field in the search bar and press Enter or click on the Submit button. Wait few seconds and if the answer can be found with the given documents (processed in the backend), the answer will be prompt. If not, the application will return "I don't know."

Example of questions:
* What is oxytocin and what is it purpose in obstetric? 

Result: Oxytocin is a hormone that is naturally produced in the body, particularly in the hypothalamus and released by the pituitary gland. In obstetrics, oxytocin is commonly used to induce or augment labor, as it stimulates contractions of the uterus. It is also used after delivery to help prevent postpartum hemorrhage (PPH) by promoting uterine contraction and reducing bleeding.

* Can I pass the Tesis class?

Result: I don't know. The given context does not provide any information about passing a "Tesis" class or the requirements for passing it.
