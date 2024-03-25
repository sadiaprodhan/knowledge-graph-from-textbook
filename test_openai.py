from neo4j import GraphDatabase
from openai import OpenAI

uri = "neo4j+s://b069e602.databases.neo4j.io"
username = "neo4j"
password = "I_0cs4pZSOyfY2LbVjTWqFV0BvJCkc45HdhwZMHBHqI"
driver = GraphDatabase.driver(uri, auth=(username, password))


def query_neo4j(query):
    with driver.session() as session:
        result = session.run(query)
        return result.data()

def get_chat_response(question):
    client = OpenAI(
    api_key="")
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=question
    )
    return response.choices[0].text.strip()

def chat_with_user():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        neo4j_query = "MATCH (n:Entity) WHERE n.name CONTAINS '" + user_input + "' RETURN n LIMIT 5"
        
        neo4j_results = query_neo4j(neo4j_query)
        
        chat_response = get_chat_response(user_input)
        
        print("Neo4j Results:", neo4j_results)
        print("ChatGPT Response:", chat_response)

chat_with_user()
driver.close()
