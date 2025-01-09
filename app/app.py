import streamlit as st
from neo4j import GraphDatabase
# from typing import Dict, Any, List
# from fuzzywuzzy import process
from ollama import chat
from sentence_transformers import SentenceTransformer
# import numpy as np
from annoy import AnnoyIndex

st.set_page_config(layout="wide", page_title="nutrition_Asst_interface")

class NutrientGraphManager:

    def __init__(self, uri: str, username: str, password: str):
        """Initialize the Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
          
    # fetch symptoms in Neo4j database
    def fetch_symptoms(self):
        """Clear all nodes and relationships in the database."""
        with self.driver.session() as session:
            symptoms_fetched = session.run("MATCH (s:Symptom) RETURN COLLECT(s.name)").values()[0][0]
            return symptoms_fetched
        
    # fetch nutrients in Neo4j database
    def fetch_nutrients(self, keywords):
        """Clear all nodes and relationships in the database."""
        with self.driver.session() as session:
            nutrients_fetched = session.run("""MATCH (n:Vitamin)-[:HAS_CATEGORY]->(cat:SymptomCategory)-[:INCLUDES]->(s:Symptom)
            MATCH (n)-[:HAS_CATEGORY]->(scat:SourceCategory)-[:INCLUDES]->(sc:Source)
            MATCH (n)-[:HAS_CATEGORY]->(dc:DailyIntakeCategory)-[:INCLUDES]->(d:Daily_intake_recommendation)
            MATCH (n)-[:HAS_CATEGORY]->(bc:BenefitCategory)-[:INCLUDES]->(b:Benefit)
            WHERE s.name IN $keywords
            RETURN n.name AS Nutrient, COLLECT(DISTINCT n.paper_source) AS Paper_Source, COLLECT(DISTINCT sc.name) AS Source,
            COLLECT(DISTINCT d.name) AS Daily_Intake, COLLECT(DISTINCT b.name) AS Benefit """, keywords=keywords).values()
            return nutrients_fetched

# def map_sentence_to_keywords_fuzzy(keyword_list, sentence, top_n=3):
#     matches = process.extract(sentence, keyword_list, limit=top_n)
#     return [match[0] for match in matches]

def setup_sentence_transformer_matcher(keyword_list):
    # Load the model
    """
    Setup the SentenceTransformer model and the Annoy index for matching keywords.

    Args:
        keyword_list (list): A list of keywords to match against.

    Returns:
        tuple: A tuple containing the SentenceTransformer model, the Annoy index, and the keyword vectors.
    """
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    keyword_sentences = [f"symptoms of {keyword.lower()}" for keyword in keyword_list]
    keyword_vectors = model.encode(keyword_sentences)
    
    # Setup Annoy index
    vector_dimension = keyword_vectors.shape[1]  # Get dimensionality from the model output
    index = AnnoyIndex(vector_dimension, 'angular')
    
    for i, vec in enumerate(keyword_vectors):
        index.add_item(i, vec)
    index.build(10)
    
    return model, index, keyword_vectors

def map_sentence_to_keywords_transformer(model, index, keyword_list, sentence, top_n=3):
    # Convert input to proper sentence format
    """
    Maps a sentence to the closest matching symptom in the keyword_list.

    This function is based on the SentenceTransformer model and the Annoy index.
    The input sentence is converted to a proper sentence format, and an embedding
    is generated for the sentence. The nearest neighbors in the Annoy index
    are then fetched, and the corresponding symptom keywords are returned.

    Args:
        model (SentenceTransformer): The SentenceTransformer model to use.
        index (AnnoyIndex): The Annoy index of the keyword_list.
        keyword_list (List[str]): The list of symptom keywords to map to.
        sentence (str): The user input sentence to map to a symptom.
        top_n (int, optional): The number of nearest neighbors to return. Defaults to 3.

    Returns:
        List[str]: The list of closest matching symptom keywords.
    """
    input_sentence = f"patient describes symptoms: {sentence.lower()}"
    
    # Get embedding for the sentence
    sentence_vector = model.encode(input_sentence)
    
    # Find nearest neighbors
    nearest = index.get_nns_by_vector(sentence_vector, top_n)
    return [keyword_list[i] for i in nearest]

def main():
    """
    The main entry point of the script. It connects to the Neo4j graph database, 
    fetches the symptom keywords, takes a user input, maps the input to the 
    closest matching symptom, fetches the corresponding nutrient information, 
    and generates a response based on the nutrient information.

    The response is generated using a chatbot model from the llm library.

    Args:
        None

    Returns:
        None
    """
    URI = "neo4j://192.168.50.97:7687"  
    USERNAME = "neo4j"              
    PASSWORD = "obinutriproject"     

    # URI = "neo4j+s://af4bec42.databases.neo4j.io"  
    # USERNAME = "neo4j"              
    # PASSWORD = "vFz0dJgS3Lv-NQjK82zIuSiQGWWzsUS_ek-Xm32CZ0k" 

    graph_manager = NutrientGraphManager(URI, USERNAME, PASSWORD)

    try:
        keywords = graph_manager.fetch_symptoms()    
        #print("Keywords:", keywords)
        user_symptom = st.text_input("Enter your symptom: ")
        submit_button = st.button("Enter")

        if submit_button:
            model,index,_ = setup_sentence_transformer_matcher(keywords)
            mapped_keywords = map_sentence_to_keywords_transformer(model, index, keywords, user_symptom)
            # mapped_keywords = map_sentence_to_keywords_fuzzy(keywords, user_symptom)
            st.write(mapped_keywords)
            #print("Mapped Keywords:", mapped_keywords)

            nutrients = graph_manager.fetch_nutrients(mapped_keywords)
            st.write(nutrients)
            #print("Nutrients:", nutrients)
            prompt =f"""
            Based on the nutients and the nutrient source. Generate the response strictly in the following format provided:
            

            users input:
            {user_symptom}

            defficient nutrients:
            {nutrients} 

            Required format:
            ### Analysis:
            <description>based on the Symptom provided by you [symptoms provided by user] I suspect you have the defficiency of [nutrient names].</description>
            
            ### Recommendations:
            <recommended-foods>I advice that you consider these [name of food sources].</recommended-foods>
            
            """

            message = [{'role': 'user', 'content': prompt}]
            response = chat(
                model='llama3.2',
                messages = message)
            st.markdown(response.message.content)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        graph_manager.close()


main()
