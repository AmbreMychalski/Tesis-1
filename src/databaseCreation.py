import chromadb

# Creation of the Collection to store the embeddings
path = "C:/Users/ambre/Desktop/INSA/5A/202320/Tesis_I/APP/front/src"
chroma_client = chromadb.PersistentClient(path)
collection = chroma_client.create_collection(name="embedding_db_persist", metadata={"hnsw:space": "cosine"})
