import os
from langchain.prompts import PromptTemplate
from langchain.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma


class CustomerSupportChatbot:
    """
    A class for creating an AI-powered customer support chatbot with persistent embeddings.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama3-8b-8192",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        overwrite_embeddings: bool = False,
    ):
        """
        Initializes the chatbot with Groq API key and settings for embedding persistence.

        Args:
            api_key (str): API key for Groq.
            overwrite_embeddings (bool): Whether to overwrite the existing embeddings file.
        """
        os.environ["GROQ_API_KEY"] = api_key
        self.llm = ChatGroq(model=model)
        self.overwrite_embeddings = overwrite_embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vector_store = None
        self.persist_directory = "Beem"
        self.collection_name = "chroma"
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "You are a highly skilled and empathetic customer support representative for Beem Company, "
                "the #1 Smart Wallet App that helps you stay on top of your finances. "
                "With Beem, you can get instant cash without interest and without credit checks through the Everdraft™. "
                "You can also send money online to anyone in the USA, file taxes for free, use a budget planner to plan, spend, and save money better, "
                "and avail credit monitoring and identity theft protection. "
                "Your goal is to provide short, friendly, and persuasive answers to customer questions, "
                "without being overly verbose. Focus on clarity and brevity while making the customer feel valued and supported. "
                "Always respond in a professional yet warm tone. "
                "Please structure your answer in 2 sentences, focusing on the most relevant points. "
                "Avoid unnecessary details. "
                "\n\nHere is the context you have about the product or service: {context} "
                "\n\nCustomer's Question: {question} "
                "\n\nYour Answer (very short, concise, and friendly):"
            ),
        )

    def load_documents(self, filepath: str):
        """
        Loads documents from the file.

        Args:
            filepath (str): Path to the text file containing documents.

        Returns:
            List of documents.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file {filepath} does not exist.")

        print(f"Loading documents from {filepath}...")
        loader = TextLoader(filepath, encoding="UTF-8")
        return loader.load()

    def generate_embeddings(self, load_documents: bool = False, filepath: str = None):
        """
        Generates or loads embeddings from the vector store. Optionally loads documents before generating embeddings.

        Args:
            load_documents (bool): If True, load documents and generate embeddings.
            filepath (str): Path to the file containing documents to load. Required if load_documents is True.
        """
        if os.path.exists(self.persist_directory) and not self.overwrite_embeddings:
            print("Loading existing Chroma vector store...")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
            )
        else:
            if load_documents:
                if not filepath:
                    raise ValueError("File path is required to load documents when load_documents=True.")
                print("Loading documents...")
                documents = self.load_documents(filepath)  # Ensure filepath is passed here
                print("Creating new Chroma vector store with embeddings...")
                self.vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory,
                    collection_name=self.collection_name,
                )
                print("Saving vector store to disk...")
                self.vector_store.persist()
            else:
                print("Using existing embeddings.")


    def query_chatbot(self, question: str, top_k: int = 2) -> str:
        """
        Queries the chatbot using the vector store for relevant context.

        Args:
            question (str): User's question.
            top_k (int): Number of top documents to retrieve. Default is 2.

        Returns:
            str: Response generated by the chatbot.
        """
        if self.vector_store is None:
            raise ValueError("Vector store is not initialized. Load or generate embeddings first.")

        # Search vector store for relevant context
        results = self.vector_store.similarity_search(question, k=top_k)
        context = " ".join([result.page_content for result in results])

        # Generate a response using the context
        prompt = self.prompt_template.format(context=context, question=question)
        response = self.llm.invoke(input=prompt).content.replace("Chatbot Response:", "").strip()
        return response


if __name__ == "__main__":
    # Get API key and settings
    api_key = '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'
    overwrite_embeddings = True  # Change to True to regenerate embeddings

    # Create the chatbot instance
    chatbot = CustomerSupportChatbot(api_key=api_key, overwrite_embeddings=overwrite_embeddings)

    # Call generate_embeddings with load_documents=True to load documents and generate embeddings
    path = 'beem.txt'

    # Generate embeddings from the loaded documents (or use existing ones if overwrite_embeddings=False)
    chatbot.generate_embeddings(load_documents=True,filepath=path)

    print("Chatbot is ready! You can ask your questions.")

    # Interact with the chatbot
    while True:
        question = input("Ask a question (or type 'exit' to quit): ")
        if question.lower() == "exit":
            print("Exiting. Goodbye!")
            break
        try:
            response = chatbot.query_chatbot(question)
            print(response)
        except ValueError as e:
            print(f"Error: {e}. Ensure embeddings are created by calling load_documents() with a valid file.")


