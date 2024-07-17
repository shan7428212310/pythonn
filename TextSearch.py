# from flask import Flask, request, jsonify
# import tempfile
# import shutil
# import os
# import re
# from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
# from whoosh.index import create_in, open_dir, EmptyIndexError
# from whoosh.fields import Schema, TEXT, ID
# from whoosh.qparser import QueryParser
# from whoosh.analysis import StemmingAnalyzer
# import docx2txt
# import PyPDF2
# import logging

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return "Hello, world!"

# # Hardcoded Azure Blob Storage connection string and container name
# connection_string = 'DefaultEndpointsProtocol=https;AccountName=kbhdocumentstorage;AccountKey=doSuaslyxCWTQRhiKeyTQEIaT+wVsx4upRJmmNOicvGcb5vJCb1S5d+0bsNQitQxI4uVbYtTwcT1+AStUfrp0Q==;EndpointSuffix=core.windows.net'
# container_name = 'kbhdocumentcontainer'

# def create_index_and_upload(connection_string, container_name):
#     schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True, analyzer=StemmingAnalyzer()))
    
#     with tempfile.TemporaryDirectory() as temp_index_dir:
#         ix = create_in(temp_index_dir, schema)
#         writer = ix.writer()

#         blob_service_client = BlobServiceClient.from_connection_string(connection_string)
#         container_client = blob_service_client.get_container_client(container_name)

#         for blob in container_client.list_blobs():
#             blob_client = container_client.get_blob_client(blob.name)
#             if blob.name.startswith('~$') or not (blob.name.lower().endswith(".docx") or blob.name.lower().endswith(".pdf")):
#                 continue

#             try:
#                 with tempfile.NamedTemporaryFile(delete=False) as temp_file:
#                     download_stream = blob_client.download_blob()
#                     temp_file.write(download_stream.readall())
#                     temp_file_path = temp_file.name

#                 if blob.name.lower().endswith(".docx"):
#                     text = docx2txt.process(temp_file_path)
#                 elif blob.name.lower().endswith(".pdf"):
#                     with open(temp_file_path, 'rb') as f:
#                         pdf_reader = PyPDF2.PdfReader(f)
#                         text = ""
#                         for page in pdf_reader.pages:
#                             text += page.extract_text()

#                 writer.add_document(title=blob.name, path=blob_client.url, content=text)
#                 os.remove(temp_file_path)

#             except Exception as e:
#                 logging.error(f"Failed to process {blob.name}: {e}")

#         writer.commit()

#         for root, _, files in os.walk(temp_index_dir):
#             for file in files:
#                 local_file_path = os.path.join(root, file)
#                 blob_name = os.path.relpath(local_file_path, temp_index_dir).replace("\\", "/")
#                 blob_client = container_client.get_blob_client(blob_name)

#                 with open(local_file_path, "rb") as data:
#                     blob_client.upload_blob(data, overwrite=True)

# def download_index_from_blob(connection_string, container_name, temp_index_dir):
#     blob_service_client = BlobServiceClient.from_connection_string(connection_string)
#     container_client = blob_service_client.get_container_client(container_name)
#     os.makedirs(temp_index_dir, exist_ok=True)

#     for blob in container_client.list_blobs():
#         blob_client = container_client.get_blob_client(blob)
#         download_file_path = os.path.join(temp_index_dir, blob.name)
#         os.makedirs(os.path.dirname(download_file_path), exist_ok=True)
#         with open(download_file_path, "wb") as download_file:
#             download_file.write(blob_client.download_blob().readall())

# def search_index(query_str, connection_string, container_name, temp_index_dir):
#     try:
#         download_index_from_blob(connection_string, container_name, temp_index_dir)
#         ix = open_dir(temp_index_dir)
#         searcher = ix.searcher()
#         query = QueryParser("content", schema=ix.schema).parse(query_str)

#         results = searcher.search(query, limit=None)
#         hits = []
#         for hit in results:
#             matched_para = re.sub('<.*?>', '', hit.highlights("content", top=4))
#             hits.append({"path": hit['path'], "paragraphs": matched_para.replace('\n', '').replace('\t', '')})

#         searcher.close()
#         ix.close()

#         return hits

#     except EmptyIndexError as e:
#         logging.error(f"EmptyIndexError: {e}")
#         return []

# @app.route('/search', methods=['GET'])
# def search():
#     query_str = request.args.get('q', '')
#     with tempfile.TemporaryDirectory() as temp_index_dir:
#         results = search_index(query_str, connection_string, container_name, temp_index_dir)
#         return jsonify(results)

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 8000))
#     app.run(host='0.0.0.0', port=port)
from flask import Flask, request, jsonify
import tempfile
import shutil
import os
import re
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from whoosh.index import create_in, open_dir, EmptyIndexError
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from whoosh.analysis import StemmingAnalyzer
import docx2txt
import PyPDF2
import logging

from __init__ import connection_string, container_name  # Use absolute import

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, world!"

def create_index_and_upload(connection_string, container_name):
    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True, analyzer=StemmingAnalyzer()))

    with tempfile.TemporaryDirectory() as temp_index_dir:
        ix = create_in(temp_index_dir, schema)
        writer = ix.writer()

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        for blob in container_client.list_blobs():
            blob_client = container_client.get_blob_client(blob.name)
            if blob.name.startswith('~$') or not (blob.name.lower().endswith(".docx") or blob.name.lower().endswith(".pdf")):
                continue

            try:
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    download_stream = blob_client.download_blob()
                    temp_file.write(download_stream.readall())
                    temp_file_path = temp_file.name

                if blob.name.lower().endswith(".docx"):
                    text = docx2txt.process(temp_file_path)
                elif blob.name.lower().endswith(".pdf"):
                    with open(temp_file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text()

                writer.add_document(title=blob.name, path=blob_client.url, content=text)
                os.remove(temp_file_path)

            except Exception as e:
                logging.error(f"Failed to process {blob.name}: {e}")

        writer.commit()

        for root, _, files in os.walk(temp_index_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                blob_name = os.path.relpath(local_file_path, temp_index_dir).replace("\\", "/")
                blob_client = container_client.get_blob_client(blob_name)

                with open(local_file_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)

def download_index_from_blob(connection_string, container_name, temp_index_dir):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    os.makedirs(temp_index_dir, exist_ok=True)

    for blob in container_client.list_blobs():
        blob_client = container_client.get_blob_client(blob)
        download_file_path = os.path.join(temp_index_dir, blob.name)
        os.makedirs(os.path.dirname(download_file_path), exist_ok=True)
        with open(download_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())

def search_index(query_str, connection_string, container_name, temp_index_dir):
    try:
        download_index_from_blob(connection_string, container_name, temp_index_dir)
        ix = open_dir(temp_index_dir)
        searcher = ix.searcher()
        query = QueryParser("content", schema=ix.schema).parse(query_str)

        results = searcher.search(query, limit=None)
        hits = []
        for hit in results:
            matched_para = re.sub('<.*?>', '', hit.highlights("content", top=4))
            hits.append({"path": hit['path'], "paragraphs": matched_para.replace('\n', '').replace('\t', '')})

        searcher.close()
        ix.close()

        return hits

    except EmptyIndexError as e:
        logging.error(f"EmptyIndexError: {e}")
        return []

@app.route('/search', methods=['GET'])
def search():
    query_str = request.args.get('q', '')
    with tempfile.TemporaryDirectory() as temp_index_dir:
        results = search_index(query_str, connection_string, container_name, temp_index_dir)
        return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

