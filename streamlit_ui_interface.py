import streamlit as st
from neo4j import GraphDatabase
from typing import Dict, Any, List
from fuzzywuzzy import process
from ollama import chat

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

def map_sentence_to_keywords_fuzzy(keyword_list, sentence, top_n=3):
    matches = process.extract(sentence, keyword_list, limit=top_n)
    return [match[0] for match in matches]

def main():
    URI = "neo4j://localhost:7687"  
    USERNAME = "neo4j"              
    PASSWORD = "obinutriproject"     

    graph_manager = NutrientGraphManager(URI, USERNAME, PASSWORD)

    try:
        keywords = graph_manager.fetch_symptoms()    
        #print("Keywords:", keywords)
        user_symptom = st.text_input("Enter your symptom: ")
        submit_button = st.button("Enter")

        if submit_button:
            mapped_keywords = map_sentence_to_keywords_fuzzy(keywords, user_symptom)
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
