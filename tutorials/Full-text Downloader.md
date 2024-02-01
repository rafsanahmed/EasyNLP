
The full-text downloader downloads articles by PMID which it reads from a text-file.  The typical workflow is to search for articles in the PubMed interface, save the resulting PMIDs in a text file, and then use EasyNLP to download and process the articles. This is explained in more detail in the following sections.

## Search Papers

Link to free full text search: https://pubmed.ncbi.nlm.nih.gov/?term=pubmed+pmc+open+access%5Bfilter%5D&filter=simsearch2.ffrft&filter=years.1980-1989&sort=date&size=50.

![[PubMedSearch.png]]

Note that the `pubmed pmc open access[filter]` text needs to be present in the search field. More search terms can be added after the `[filter]` term. 

Once you have your results on the screen you need to save them by clicking on the save button under the search field. Choose "All Results" and "PMID" in the dialog.

This results in a file which you can save and feed into the downloader. The file should only contain PMIDs, one per line. it should look like this.
```text
34286689
29566442
37528399
32341686
36830172
```

The EasyNLP `config.json` file needs to be updated with the filename. The relevant section is this one.
```json
"downloader_ft": {
    "input_path": "data/pmid-lyme-set.txt",
    "output_path": "results/dataloader/pmid-example.txt.json",
    "max_threads": 8
  },
```
 The `input_path`needs to point to the filename with the PMIDs. The downloader downloads in parallel, the number of parallel jobs can be specified with the `max_threads` parameter. There is a hardcoded delay (less than one second) between the download requests in each thread to prevent spamming the PubMed server. Note that if the `max_threads`parameter is greater than one, the downloaded papers will not be in the same order as in the file with PMIDs.

The output will be a file with the articles in JSON format.
```json
{
  "fulltexts": [
    {
      "source": "PMC",
      "date": "20230228",
      "key": "pmc.key",
      "infons": {},
      "documents": [
        {
          "id": "9952438",
          "infons": {
            "license": "CC BY"
          },
```

The documents have labelled sections -- unfortunately the labelling is not consistent across documents. The following shows the section names and counts from a selection of 100 papers.
```shell
cat results/dataloader/pmid-example.txt.json |jq |rg section_type | sort | uniq -c
 243                 "section_type": "ABBR",
 226                 "section_type": "ABSTRACT",
  77                 "section_type": "ACK_FUND",
   5                 "section_type": "APPENDIX",
 107                 "section_type": "AUTH_CONT",
 112                 "section_type": "CASE",
 129                 "section_type": "COMP_INT",
 262                 "section_type": "CONCL",
 743                 "section_type": "DISCUSS",
 222                 "section_type": "FIG",
2138                 "section_type": "INTRO",
 892                 "section_type": "METHODS",
7267                 "section_type": "REF",
 587                 "section_type": "RESULTS",
  52                 "section_type": "SUPPL",
 644                 "section_type": "TABLE",
 100                 "section_type": "TITLE",
```

The splitter combines texts into paragraphs, and discards a lot of the meta-data (like IDs and dates). The section labels are also discarded. The contents of the following sections are also discarded by the splitter.
```python
ignored_sections=["ACK_FUND", "AUTH_CONT", "COMP_INT", "FIG", "TABLE", "ABBR", "REF"]
```
 These are hard-coded at the moment.

The following example shows what the the resulting JSON looks like.
```json
{
  "9952438": {
    "title": "Disulfiram—Mitigating Unintended Effects",
    "sentences": [
      {
        "text": "Disulfiram—Mitigating Unintended Effects"
      },
      {
        "text": "Lyme disease caused by infection with a multitude of vector-borne organisms can sometimes be successfully treated in its very early stages. However, if diagnosis is delayed, this infection can become disseminated and, ...[cut for brevity]... This paper outlines the results of that research to help avoid some of the pitfalls inherent in this novel use of an old and established medication in the practice of clinical medicine."
      },
```

The relevant config file section looks as follows.
```json
  "splitter_ft": {
    "input_path": "results/dataloader/pmid-example.txt.json",
    "output_path": "results/splitter/pmid-example.paragraphs.json",
    "split": "paragraphs",
    "batch_size": 100
  },
```
The `input_path` should point to the `output_path` of the downloader. The resulting output file, specified in `output_path`, can be divided into smaller files by specifying the `batch_size` parameter. This parameter specifies the maximum number of papers in each file. The splitter will append a counter after the file name and before the json extension, resulting in filenames like the following; `splitter/pmid-example.paragraphs-00.json`. Setting `batch_size` to zero puts all papers in a single file-

The output of the splitter can be used in the NER and other scripts.
