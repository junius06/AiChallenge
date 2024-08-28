import chromadb
from chromadb.utils import embedding_functions

class ChromaDBManager:
    def __init__(self, collection_name: str, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initializes the ChromaDBManager.
        
        :param collection_name: The name of the ChromaDB collection to use.
        :param embedding_model: The model name for generating embeddings. Default is "all-MiniLM-L6-v2".
        """
        self.client = chromadb.PersistentClient()
        self.collection_name = collection_name
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
        self.collection = self._initialize_collection()
        
    def _initialize_collection(self):
        """
        Initializes or retrieves the collection from ChromaDB.
        
        :return: The ChromaDB collection object.
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)
        except chromadb.CollectionNotFoundError:
            collection = self.client.create_collection(name=self.collection_name)
        return collection

    def add_data(self, data: list):
        """
        Adds data to the ChromaDB collection.
        
        :param data: A list of dictionaries where each dictionary contains 'issue' and 'solution' keys.
        """
        for item in data:
            embedding = self.embedding_function(item["issue"])
            self.collection.add(embedding=embedding, metadata={
                "issue": item["issue"],
                "solution": item["solution"]
            })

    def search(self, query: str, top_k: int = 3):
        """
        Searches for similar items in the collection based on the query.
        
        :param query: The query string to search for.
        :param top_k: The number of top results to return.
        :return: A list of dictionaries with search results.
        """
        query_embedding = self.embedding_function(query)
        search_results = self.collection.query(query_embedding=query_embedding, top_k=top_k)
        results = [{"issue": result["metadata"]["issue"], "solution": result["metadata"]["solution"]} for result in search_results["results"]]
        return results

# client = chromadb.PersistentClient()

# collection = client.create_collection(name="error_cases")

# sample_issues = [
#     {"issue": "Database connection failed", 
#      "solution": "Check database credentials"},
#     {"issue": "Failed to fetch API data", 
#      "solution": "Verify API endpoint and parameters"},
#     {"issue": "Timeout error on network request", 
#      "solution": "Increase timeout settings"}
# ]

# embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# for issue in sample_issues:
#     embedding = embedding_function(issue["issue"])
#     collection.add(embedding=embedding, metadata={"issue": issue["issue"], "solution": issue["solution"]})