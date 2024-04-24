import chromadb
import pandas as pd
import numpy as np

embeddings_directory = "embeddings/"
path_chroma = "chroma-db"
collection_name = "embedding_db_persist_500"
embeddings_file = "embeddings_chunks500.csv"

# ---------------------------------------------------------------------------------------------------------------
# -------------------------------------------- Retrieve embeddings ----------------------------------------------
# ---------------------------------------------------------------------------------------------------------------
print("Retrieving embeddings...")
df_complete = pd.read_csv(embeddings_directory+embeddings_file)
df_complete = df_complete.drop(['Unnamed: 0'], axis=1)

df_complete['embeddings'] = df_complete['embeddings'].apply(eval).apply(np.array)

# ---------------------------------------------------------------------------------------------------------------
# ------------------------------------------ Initialize ChromaClient --------------------------------------------
# ---------------------------------------------------------------------------------------------------------------
print("Initialize ChromaClient...")
chroma_client = chromadb.PersistentClient(path_chroma)
print(chroma_client.list_collections())

# ---------------------------------------------------------------------------------------------------------------
# -------------------------------------------- Create a collection ----------------------------------------------
# ---------------------------------------------------------------------------------------------------------------
print("Creating Collection from "+embeddings_directory+embeddings_file+" named "+collection_name)
collection = chroma_client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

collection = chroma_client.get_collection(collection_name)

collection.add(
            embeddings=[arr.tolist() for arr in df_complete['embeddings'].to_list()],
            documents= df_complete['text'].to_list(),
            metadatas = df_complete.apply(lambda row: {"title": row['fname'], "page": str(row['page']), "coords": str(row['coords']), "tokens": str(row['n_tokens'])}, axis=1).tolist(),
            ids=[str(i) for i in range(len(df_complete))]
        )
print(chroma_client.list_collections())
# print(collection.get())

# ---------------------------------------------------------------------------------------------------------------
# -------------------------------------------- Delete a collection ----------------------------------------------
# ---------------------------------------------------------------------------------------------------------------
# print("Deleting collection...")
# print(chroma_client.list_collections())
# chroma_client.delete_collection(name=collection_name)
# print(chroma_client.list_collections())
