import PyPDF2
import nltk
import spacy
nlp = spacy.load("en_core_web_sm")  
nlp.add_pipe("entityLinker", last=True)
import re
from spacy.matcher import Matcher
nltk.download('punkt')

def extract_sentences_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)

        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
        
    sentences = nltk.sent_tokenize(text)
    return sentences

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
    doc = nlp(ent1.strip())
    entity_linking1 = None
    if doc._.linkedEntities and doc._.linkedEntities[0] is not None and doc._.linkedEntities[0].get_url() is not None:
      entity_linking1 = doc._.linkedEntities[0].get_url()
      
    if entity_linking1 is None:
       entity_linking1 = 'Not Found'
    doc2 = nlp(ent2.strip())
    entity_linking2 = None
    if doc2._.linkedEntities and doc2._.linkedEntities[0] is not None and doc2._.linkedEntities[0].get_url() is not None:
      entity_linking2 = doc2._.linkedEntities[0].get_url()
    if entity_linking2 is None:
       entity_linking2 = 'Not found'
    return [ent1.strip(),  relation, ent2.strip()], [entity_linking1,entity_linking2]
  except NameError:
      print('error with sent {sent}',sent)
def remove_numeric_sentences(sentences):
    cleaned_sentences = [re.sub(r'\n', '', sentence) for sentence in sentences if not re.match(r'^[\d\s.]+$', sentence)]
    return cleaned_sentences
      
pdf_path = "KG_BOOK_CHAPTER_3.pdf"
sentences = extract_sentences_from_pdf(pdf_path)
sentences = remove_numeric_sentences(sentences)
triples = []
entity_linkings= []


for i, sentence in enumerate(sentences, 1):
    triple, entity_linking = extract_entities(sentence)
    triples.append(triple)
    entity_linkings.append(entity_linking)
print(triples)
print(entity_linkings)
