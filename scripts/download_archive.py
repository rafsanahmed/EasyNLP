import requests
import tarfile
import os, sys
from tqdm import tqdm
import json
from spacy.lang.en import English
from pathlib import Path
import random
from threading import Thread

# Hardcoded for now.
URLBASE = "https://ftp.ncbi.nlm.nih.gov/pub/wilbur/BioC-PMC"

# Download the archive.
def download_file(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024
        print("Downloading", total_size, "bytes")
        with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
            with open(save_path, "wb") as f:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    f.write(data)
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

# Extract the gzipped files into extract_path.
def extract_tar_gz(tar_path, extract_path):
    if tarfile.is_tarfile(tar_path):
        with tarfile.open(tar_path, "r:gz") as tar:
            #tar.extractall(Path=extract_path)
            for member in tqdm(iterable=tar.getmembers(), total=len(tar.getmembers())):
                tar.extract(member=member, path=extract_path)
    else:
        print(f"The file at {tar_path} is not a valid tar.gz file.")

# Disassemble a single JSON article. Return a dict with allowed/reuqested section texts.
def extract_fulltext_data(data: dict, allowed_sections=[], ignored_sections=[]) -> dict:
    section_texts = {} # For each "INTRO" and other sections, save the paragraphs.
    if not "documents" in data:
        return None
    
    for document in data['documents']:
        #print("Passages:", len(document["passages"]))
        for passage in document['passages']:
            try:
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
            except KeyError:
                print("Error in document!")
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
        
# Convert the result of extract_fulltext_data() to
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

# See text_to_sentences(), but no sentence splitting.
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

# Processes the files in filelist. Extracts the texts from each file, oprionally
# converts to it to sentences, and creates a new JSON structure.
# The JSON structs for all files are written to the output_file.
# Output is a list: [PMID:{title:{}, sentences:[text:{...}]}, ...]
def process_files(filelist, output_file, allowed_sections=[], ignored_sections=[],
                  split="sentences", progress_bar=None):
    full_output = {}
    full_batch_output = []
    for filename in filelist:
        with open(filename, "r") as fin:
            ft = json.loads(fin.read())
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
        if progress_bar:
            progress_bar.update(1)
    full_batch_output.append(full_output)
    #Return json.dumps(full_output)
    #full_batch_output.append(json.dumps(full_output)) # The left-overs.
    if len(full_batch_output) > 0:
        with open(output_file, "w") as fout:
            fout.write(json.dumps(full_batch_output)) 

def chunks(lst, n):
    # Yield successive n-sized chunks from lst.
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Should check for existing archives? (But we delete them afterwards...)
'''
    downloader_ft.run(
        input_file=dl_ft_config["input_path"],
        output_file=dl_ft_config["output_path"],
        max_threads=dl_ft_config["max_threads"],
    )
    splitter_ft.run(
        input_file=dl_ft_config["input_path"],
        output_file=dl_ft_config["output_path"],
        split=dl_ft_config["split"],
        batch_size=dl_ft_config["batch_size"],

'''
# Called from main.py.
def run_full_text_downloader(filename, save_dir, extract_dir):
    # Ensure the extraction directory exists
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    url = URLBASE + "/" + filename
    save_file = save_dir + "/" + filename
    download_file(url, save_file)
    extract_tar_gz(save_file, extract_dir)

# Called from main.py.
def run_extract_text(extract_dir, output_dir, split="sentences", output_file="output.json",
                     batch_size=1000, random_sel=0, max_threads=1):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem = Path(output_file).stem
    suffix = Path(output_file).suffix
    path = os.path.dirname(output_file)
    #
    # os.path.join(extract_dir, f)
    files = [os.path.join(extract_dir, f)
             for f in os.listdir(extract_dir)
             if os.path.isfile(os.path.join(extract_dir, f))]
    if random_sel > 0:
        files = random.sample(files, random_sel)
    threads = []
    with tqdm(total=len(files), unit="#") as progress_bar:
        # allow and ignore should be parameters.
        allow = []
        ignore = ["ACK_FUND", "AUTH_CONT", "COMP_INT", "FIG", "TABLE", "ABBR", "REF"]
        for i, batch in enumerate(chunks(files, batch_size)):
            output_file = os.path.join(path, stem+"-{:03n}".format(i)+suffix)
            output_file = os.path.join(output_dir, output_file)
            thread = Thread(target=process_files, args=(batch, output_file),
                            kwargs={'allowed_sections':allow,
                                    'ignored_sections':ignore,
                                    'split':split, 'progress_bar':progress_bar}
                            )
            thread.start()
            threads.append(thread)
            # If max threads are running, wait for one to finish before starting another
            # They should take approx'ly the same time...
            if len(threads) >= max_threads:
                thread_to_join = threads.pop(0)
                thread_to_join.join()
        # Wait for any remaining threads to finish
        for thread in threads:
            thread.join()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        filename = sys.argv[1]
        save_dir = sys.argv[2]
        extract_dir = sys.argv[3]
        run_full_text_downloader(filename, save_dir, extract_dir)
    if len(sys.argv) == 3:
        extract_dir = sys.argv[1]
        output_dir = sys.argv[2]
        # Testing with a random selection of 100000 and 12 threads.
        run_extract_text(extract_dir, output_dir, max_threads=4, random_sel=100000)
    
