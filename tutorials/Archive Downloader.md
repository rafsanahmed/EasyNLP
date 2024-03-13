
The archive downloader downloads large zipped PUBMED archives. The archives are available at https://ftp.ncbi.nlm.nih.gov/pub/wilbur/BioC-PMC/. The downloader downloads one archive at a time (specified in config file), unzips and uncompresses the files and puts them in a config specified directory. The compressed files are between five and eight GB large, uncompressed larger than 25 GB. Archives can contain several hundred thousand full-text articles.

The following shows an example configuration.
```json
  "download_archive": {
    "archive": "PMC050XXXXX_json_unicode.tar.gz",
    "save_path": "/tmp",
    "extract_path": "results/dataloader/archive"
  },
```

After downloading, specific sections of the articles can be extracted and prepared for the NER task. The output i similar to that of the PUBMED splitter. Beside extracting relevant section text, the paragraphs of the extracted sections can be split into individual sentences.

Typical config of the extractor.
```json
  "extract_text": {
      "extract_path": "results/dataloader/archive",
      "output_path": "results/splitter/",
      "split": "sentences",
      "output_file": "output.json",
      "batch_size": 1000,
      "max_threads": 4
  },
```
To extract sentences, specify `sentences` after the `split` key.  Anything else will keep the paragraphs.

The `output_file` setting is used to generate filenames. For each batch, a number is inserted into the filename. The filename in the example would generate filenames like `output-0000.json` etc.

The downloader and extractor are specified as follows in the `ignore` section of the config file.
```json
    "download_archive": true,
    "extract_text": true,
```

