import json
import openai
import os
# import numpy as np
# from numpy import dot
# from numpy.linalg import norm
# import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import API_KEY

openai.api_key = API_KEY

def get_embedding(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    embedding = response['data'][0]['embedding']
    return embedding

def process_data(data):
    """Process each item in the JSON data to get embeddings."""
    for item in data:
        # Get the embedding for the issue
        issue_embedding = get_embedding(item['issue'])
        item['issue_embedding'] = issue_embedding
        
        # Ensure expected_solution is a list
        if isinstance(item['expected_solution'], str):
            item['expected_solution'] = [item['expected_solution']]
        
        # Get embeddings for each solution
        item['expected_solution_embeddings'] = [get_embedding(sol) for sol in item['expected_solution']]
    
    return data

def save_data(data, file_path):
    """Save the processed data to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

class DataChangeHandler(FileSystemEventHandler):
    def __init__(self, input_file_path, output_file_path):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path

    def on_modified(self, event):
        if event.src_path == self.input_file_path:
            print(f"{self.input_file_path} has been modified. Updating embeddings...")
            with open(self.input_file_path, "r", encoding='utf-8') as file:
                data = json.load(file)
            processed_data = process_data(data)
            save_data(processed_data, self.output_file_path)
            print("Data with embeddings has been updated successfully.")

def main():
    base_dir = os.path.dirname(__file__)
    input_file_path = os.path.join(base_dir, 'issues_data', 'data.json')
    output_file_path = os.path.join(base_dir, 'issues_data', 'embedding_data.json')
    
    event_handler = DataChangeHandler(input_file_path, output_file_path)
    # Auto Vector Embedding: 옵저버가 data.json파일에서 변경 사항이 감지되면 이벤트 핸들러가 트리거되어, embedding_data.json파일에 자동으로 업데이트가 진행된다.
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(input_file_path), recursive=False)
    observer.start()
    print(f"Watching for changes in {input_file_path}...")
    
    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()


# def get_embedding(text):
#     response = openai.Embedding.create(
#         input=text,
#         model="text-embedding-ada-002"
#     )
#     embedding = response['data'][0]['embedding']
#     return embedding

# def update_json_with_embeddings(input_file, output_file):
#     # Load the JSON data
#     with open(input_file, 'r', encoding='utf-8') as file:
#         data = json.load(file)
    
#     # Process each item to add the 'Embedding' field with embeddings
#     for item in data:
#         decoding = item.get('Decoding', {})
        
#         if 'issue' in decoding:
#             decoding['issue'] = get_embedding(decoding['issue'])
        
#         if 'expected_solution' in decoding:
#             decoding['expected_solution'] = [get_embedding(sol) if isinstance(sol, str) else sol for sol in decoding['expected_solution']]
        
#         item['Embedding'] = decoding
    
#     # Save the updated data to a new file
#     with open(output_file, 'w', encoding='utf-8') as file:
#         json.dump(data, file, ensure_ascii=False, indent=4)

# # Usage
# input_file = 'issues_data/data.json'
# output_file = 'issues_data/embedding_data.json'
# update_json_with_embeddings(input_file, output_file)