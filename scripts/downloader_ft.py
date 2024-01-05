# coding=utf-8
import json
import os
import pubmed_parser as pp
import requests
import shutil
import sys
from time import sleep
from random import random

from typing import Any, List

from queue import Queue
from threading import Thread

from pathlib import Path

def download_file(pmcid, queue, counter):
    """
    Download a file from the given URL with the specified PMCID and add it to a queue.

    Args:
    pmcid (str): The PubMed Central ID of the file to download.
    queue (Queue): The queue to add the downloaded file.
    """
    
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmcid}/unicode"

    # Random sleep to prevent killing the server.
    sleep(random())
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Check if the response contains an error key and it's not a normal JSON content
        if isinstance(data, dict) and 'error' in data and len(data) == 2 and 'pmcid' in data:
            print(f"Error downloading PMCID {pmcid}: {data['error']}")
            print(data)
        else:
            queue.put((pmcid, data, counter))
    except requests.RequestException as e:
        print(response.text)
        #print(f"Request exception for PMCID {pmcid}: {str(e)}")

def handle_queue(queue, output_file, counter):
    """
    Handle files in the queue and save them to disk.

    Args:
    queue (Queue): The queue containing downloaded files.
    """

    # We need to check for the isdir property because the file might
    # not exists (yet).
    if not os.path.isdir(output_file):
        output_dir = os.path.dirname(output_file)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as fout:
            fout.write("{\"fulltexts\": [\n");

    while True:
        pmcid, data, counter = queue.get()
        if pmcid is None:  # This is the signal to stop the handler
            break
    
        # Save (append) the data to a file.
        # If the output_file is a directory, we save individual files.
        if os.path.isdir(output_file):
            with open(output_file + f"{pmcid}.json", 'w') as file:
                file.write(json.dumps(data))
                file.write("\n")
                print(f"Wrote {counter}: {pmcid}")
        else:
            with open(output_file, 'a') as file: # TODO Create parent dirs if not exist.
                file.write(json.dumps(data))
                file.write(",\n")
                print(f"Appended {counter}: {pmcid}")
        
        queue.task_done()

    if os.path.isfile(output_file):
        with open(output_file, 'a') as fout:
            fout.write("{}\n");
            fout.write("]}\n");

def download_files_parallel(pmcids:list, output_file: str, max_threads:int):
    """
    Download multiple files in parallel with a limit on the number of concurrent downloads.

    Args:
    pmcids (list of str): List of PubMed Central IDs.
    max_threads (int): Maximum number of parallel downloads.
    """
    queue = Queue()
    threads = []
    
    # Start the queue handler thread
    handler_thread = Thread(target=handle_queue, args=(queue, output_file, 0))
    handler_thread.start()

    # Start threads for downloading files
    counter = len(pmcids)
    for pmcid in pmcids:
        thread = Thread(target=download_file, args=(pmcid, queue, counter))
        thread.start()
        threads.append(thread)
        counter -= 1
        
        # If max threads are running, wait for one to finish before starting another
        if len(threads) >= max_threads:
            thread_to_join = threads.pop(0)
            thread_to_join.join()

    # Wait for any remaining threads to finish
    for thread in threads:
        thread.join()

    # Stop the handler thread
    queue.put((None, None, None))
    handler_thread.join()

_tmp_dir = "tmp_dir_dl"

def run(input_file: str, output_file: str, max_threads: int):
    os.makedirs(_tmp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    pmcids = []
    for line in open(input_file, "r"):
        pmcids.append(line.strip())

    try:
        download_files_parallel(pmcids, output_file, max_threads)
    except KeyboardInterrupt:
        pass

    shutil.rmtree(_tmp_dir)


"""
———————————————————————————————————————————————————————————————————————————————
Get research full text from list of PMIDs.
Arguments:
    input_file: path to .txt file with list of newline-separated PMIDs.
    output_file: file to append to.
    max_threads: number of simultaneous downloads.
———————————————————————————————————————————————————————————————————————————————
"""
if __name__ == "__main__":
    if len(sys.argv) == 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        max_threads = 1  # Maximum number of parallel downloads
    elif len(sys.argv) == 4:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        max_threads = int(sys.argv[3])
    else:
        sys.exit(
            "usage: {} input_path output_path {max_threads}".format(sys.argv[0])
        )
    run(input_file, output_file, max_threads)
