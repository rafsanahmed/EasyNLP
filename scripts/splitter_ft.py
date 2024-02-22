# coding=utf-8
import json
import os
import requests
import shutil
import sys
from time import sleep
from random import random
from spacy.lang.en import English
from pathlib import Path

def extract_fulltext_data(data: dict, allowed_sections=[], ignored_sections=[]) -> dict:
    section_texts = {} # For each "INTRO" and other sections, save the paragraphs.
    if not "documents" in data:
        return None
    
    for document in data['documents']:
        #print("Passages:", len(document["passages"]))
        for passage in document['passages']:
            offset = passage['offset']
            infons = passage['infons']            
            infons_type = passage['infons']['type']
            section_type = infons['section_type']
            if infons_type == "ref":
                continue
            if section_type in ignored_sections:
                continue
            if allowed_sections == [] or section_type in allowed_sections:
                if infons_type.startswith("title"):
                    #print("title", passage)
                    #print(section_type+"/"+infons_type, passage["text"])
                    pass
                else:
                    if section_type in section_texts: # section_texts is our extracted text.
                        section_texts[section_type].append(passage["text"])
                    else:
                        section_texts[section_type] = [passage["text"]]
            #print()
        return section_texts

# Extract ID from JSON.
def extract_metadata(data: dict) -> str:
    if not "documents" in data:
        return "unknown"
    if "documents" in data:
        if len(data['documents']) > 0:
            id = data["documents"][0]["id"]
            return id

# Extract the title.
def extract_title(data: dict) -> str:
    if not "documents" in data:
        return "unknown"
    if "documents" in data:
        if len(data['documents']) > 0:
            passages = data["documents"][0]["passages"]
            if len(passages) > 0:
                if "text" in passages[0]:
                    return passages[0]["text"]
            return "unknown"
        
# Convert the result of extract_fulltext() to
# sentences.
def texts_to_sentences(section_texts: dict) -> dict:
    if not section_texts:
        return None
    data = {}
    nlp = English()
    nlp.add_pipe("sentencizer")
    for sec in section_texts:
        data[sec] = []
        for paragraph in section_texts[sec]:
            doc = nlp(paragraph) #nlp("This is a sentence. This is another sentence.")
            for sentence in doc.sents:
                data[sec].append(str(sentence))
    #return(json.dumps(data)) # string
    return data

# See above, but no spetence splitting
def texts_to_paragraphs(section_texts: dict) -> dict:
    if not section_texts:
        return None
    data = {}
    for sec in section_texts:
        data[sec] = []
        for paragraph in section_texts[sec]:
            data[sec].append(paragraph)
    #return(json.dumps(data)) # string
    return data

# Make a batch varsion?
# bulk_to_sentences which takes an array slice from the list
# to create batches?        

# Input is generated by downloader_ft.py which contains
# one key "fulltexts" which is a list with articles.
# The texts from ignored_sections are not included. Specific sections
# can be chosen with allowed_sections (default [] means all sections).
def bulk_to_sentences(filename, allowed_sections=[], ignored_sections=[], split="sentences", batch_size=0):
    with open(filename, "r") as fin:
        data = json.loads(fin.read())
    fulltexts = data["fulltexts"]

    # Calculate/create batches. batch_size==0 means
    # everything goes into one batch.
    current_batch_size = batch_size
    current_batch_number = 0
    
    full_output = {}
    full_batch_output = []
    for ft in fulltexts:
        #print(ft)
        # produces output like:
        # {'TITLE': ['Advances in mechanism and regulation of PANoptosis: Prospects in disease
        #             treatment'], 'ABSTRACT': ['PANoptosis, a new research ...
        st = extract_fulltext_data(ft, allowed_sections=allowed_sections, ignored_sections=ignored_sections)
        md = extract_metadata(ft)
        title = extract_title(ft)
        if split == "sentences":
            ss = texts_to_sentences(st)
        else:
            ss = texts_to_paragraphs(st)
        #print(ss)
        if not ss:
            continue
        output = {}
        output["title"] = title
        output["sentences"] = []
        for section in ss: # Filter sections here?
            sentences = ss[section]
            for sentence in sentences: # Also make a paragraph mode?
                text_json = {}
                text_json["text"] = sentence
                output["sentences"].append(text_json) #sentence)
        full_output[md] = output
        current_batch_size -= 1
        if current_batch_size == 0:
            full_batch_output.append(full_output)
            full_output = {}
            current_batch_size = batch_size
            current_batch_number += 1
    
    #return json.dumps(full_output)
    #full_batch_output.append(json.dumps(full_output)) # The left-overs.
    full_batch_output.append(full_output) # The left-overs.
    return full_batch_output

def run(input_file, output_file, split, batch_size):
    full_texts = bulk_to_sentences(input_file, allowed_sections=[],
                                   ignored_sections=["ACK_FUND", "AUTH_CONT", "COMP_INT", "FIG", "TABLE",
                                                     "ABBR", "REF"],
                                   split=split, batch_size=batch_size)
    output_dir = os.path.dirname(output_file)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem = Path(output_file).stem
    suffix = Path(output_file).suffix
    path = os.path.dirname(output_file)
    for i, ft in enumerate(full_texts):
        if len(ft) > 0:
            output_file = os.path.join(path, stem+"-{:02n}".format(i)+suffix)
            with open(output_file, "w") as fout:
                fout.write(json.dumps(ft))
        
if __name__ == "__main__":
    if len(sys.argv) == 2:
        full_texts = bulk_to_sentences(sys.argv[1], split="sentences")
        print(full_texts)
    elif len(sys.argv) == 4:
        run(sys.argv[1], sys.argv[2], sys.argv[3], 0)
    elif len(sys.argv) == 5:
        run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
