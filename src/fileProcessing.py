import os
import requests
import json
import openai
import re
import PyPDF2

openai.api_key = "cf0bd49030ed4aa6a6509be1cd9d604b"
openai.api_base = "https://invuniandesai.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2023-05-15'

def process_to_txt():

    input_directory = "front/rawDataset/"
    output_directory = "front/ProcessedDataset/"

    for filename in os.listdir(input_directory):
        # Ouvrir le fichier PDF en mode lecture binaire ('rb')
        with open(input_directory+filename, 'rb') as pdf_file:
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
        with open(output_directory+filename, 'w', encoding='utf-8') as txt_file:
            txt_file.write(raw_text)

if __name__ == '__main__':
    process_to_txt()
