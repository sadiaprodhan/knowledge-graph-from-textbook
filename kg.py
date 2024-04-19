import PyPDF2
import nltk
import spacy
nlp = spacy.load("en_core_web_sm")  
nlp.add_pipe("entityLinker", last=True)
import re
from spacy.matcher import Matcher
nltk.download('punkt')
import networkx as nx
import matplotlib.pyplot as plt
from neo4j import GraphDatabase


def generate_knowledge_graph(triples):
  G = nx.DiGraph()

  for triple in triples:
    subject, relation, object_, ent1,ent2 = triple
    G.add_node(subject)
    G.add_node(object_)
    G.add_edge(subject, object_, label=relation)

  plt.figure(figsize=(100, 100))
  pos = nx.spring_layout(G)  
  nx.draw(G, pos, with_labels=True, node_size=100, node_color='skyblue', font_size=12, font_weight='bold')  
  edge_labels = nx.get_edge_attributes(G, 'label') 
  nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=10) 
  plt.title("Knowledge Graph")
  plt.show()
def extract_sentences_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)

        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
        
    sentences = nltk.sent_tokenize(text)
    return sentences
def canonicalize_entity(entity_text):
     canonical_form = entity_text.lower()
    # Remove punctuation using regex
     canonical_form = re.sub(r'[^\w\s]', '', canonical_form)
     return canonical_form.strip()
def get_relation(sent):
    doc = nlp(sent)

    matcher = Matcher(nlp.vocab)

    pattern = [{'DEP':'ROOT'},
               {'DEP':'prep','OP':"?"},
               {'DEP':'agent','OP':"?"},
               {'POS':'ADJ','OP':"?"}]

    matcher.add("matching_1", [pattern])

    matches = matcher(doc)
    k = len(matches) - 1

    span = doc[matches[k][1]:matches[k][2]]

    return span.text
def connect_database():
   driver = GraphDatabase.driver(
    "neo4j+s://b68740ea.databases.neo4j.io",
    auth=("neo4j", "_lJbg6-mIWPdVXmtjTrAgcmBJFq7iHRJ8iHRBRDuDDc"))
   print(driver)
   return driver

   
   
def extract_entities(sent):

  try:
    
    ent1 = ""
    ent2 = ""
    prv_tok_dep = ""   
    prv_tok_text = ""   
    prefix = ""
    modifier = ""

    for tok in nlp(sent):
         if tok.dep_ != "punct":
          if tok.dep_ == "compound":
            prefix = tok.text
            if prv_tok_dep == "compound":
              prefix = prv_tok_text + " "+ tok.text

     
          if tok.dep_.endswith("mod") == True:
            modifier = tok.text
        
            if prv_tok_dep == "compound":
              modifier = prv_tok_text + " "+ tok.text

          if tok.dep_.find("subj") == True:
            ent1 = modifier +" "+ prefix + " "+ tok.text
            prefix = ""
            modifier = ""
            prv_tok_dep = ""
            prv_tok_text = ""

      
          if tok.dep_.find("obj") == True:
            ent2 = modifier +" "+ prefix +" "+ tok.text
      
          prv_tok_dep = tok.dep_
          prv_tok_text = tok.text
  
    relation = get_relation(sentence)
    ent1 = canonicalize_entity(ent1)
    doc = nlp(ent1.strip())
    entity_linking1 = None
    if doc._.linkedEntities and doc._.linkedEntities[0] is not None and doc._.linkedEntities[0].get_url() is not None:
      entity_linking1 = doc._.linkedEntities[0].get_url()
      
    if entity_linking1 is None:
       entity_linking1 = 'Not Found'
    doc2 = nlp(ent2.strip())
    ent2 = canonicalize_entity(ent2)
    
    entity_linking2 = None
    if doc2._.linkedEntities and doc2._.linkedEntities[0] is not None and doc2._.linkedEntities[0].get_url() is not None:
      entity_linking2 = doc2._.linkedEntities[0].get_url()
    if entity_linking2 is None:
       entity_linking2 = 'Not found'
    if ent1 and ent2 and relation:
      return [ent1.strip(),  relation, ent2.strip(), entity_linking1,entity_linking2]
    else:
       return []
  except NameError:
      print('error with sent {sent}',sent)
def remove_numeric_sentences(sentences):
    cleaned_sentences = [re.sub(r'\n', '', sentence) for sentence in sentences if not re.match(r'^[\d\s.]+$', sentence)]
    return cleaned_sentences

def add_entity_node(tx,entity_text, wikipedia_url):
    tx.run("MERGE (n:Entity {name: $entity_text, wikipedia_url: $wikipedia_url})", entity_text=entity_text, wikipedia_url=wikipedia_url)


def add_triple(tx, subject, predicate, obj):
    tx.run("MERGE (s:Entity {name: $subject}) "
           "MERGE (o:Entity {name: $obj}) "
           "MERGE (s)-[:RELATIONSHIP {type: $predicate}]->(o)", 
           subject=subject, predicate=predicate, obj=obj)

pdf_path = "KG_BOOK_CHAPTER_3.pdf"
sentences = extract_sentences_from_pdf(pdf_path)
sentences = remove_numeric_sentences(sentences)
triples = []
entity_linkings= []


for i, sentence in enumerate(sentences, 1):
    triple = extract_entities(sentence)
    if triple:
      triples.append(triple)
print(triples)
#generate_knowledge_graph(triples)
driver = connect_database()
with driver.session() as session:
    for triple in triples:
        subject, predicate, object, ent1_link, ent2_link = triple
        session.write_transaction(add_triple, subject,predicate,object)

        session.write_transaction(add_entity_node, subject, ent1_link)
        session.write_transaction(add_entity_node,object,ent2_link)


