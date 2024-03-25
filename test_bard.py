from neo4j import GraphDatabase
from bardapi import Bard

bard = Bard(token="")

uri = "neo4j+s://b069e602.databases.neo4j.io"
driver = GraphDatabase.driver(uri, auth=("neo4j", "I_0cs4pZSOyfY2LbVjTWqFV0BvJCkc45HdhwZMHBHqI"))
print(driver)

def query_neo4j(user_question):
    
    query = "MATCH (n:Entity) WHERE n.name CONTAINS '" + user_question + "' RETURN n LIMIT 5"
    print(query)

    try:
        with driver.session() as session:
            results = session.run(query)
            print(results)
            answer = [record["n"] for record in results]
            print(answer)
            response = "Here's what I found in the database: \n"
            for record in results:
                response += str(record) + "\n"
            summary = bard.ask("Summarize the retrieved information: " + response)
            return summary.text if summary else response

    except Exception as e:
        return f"Error querying Neo4j: {str(e)}"


def main():
    
    while True:
        user_question = input("Ask me a question: ")
        response = query_neo4j(user_question)
        print(response)

        if input("Ask another question? (y/n): ").lower() != "y":
            break


if __name__ == "__main__":
    main()

driver.close()