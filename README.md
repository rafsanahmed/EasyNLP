# EasyNER: A Customizable and Easy-to-Use Pipeline for Deep Learning- and Dictionary-based Named Entity Recognition from Medical Text

EasyNER is a customizable end-to-end pipeline for extracting named entities from medicine-related texts. The pipeline comes with pre-trained models and dictionaries that can retrieve many biomedical entities: cells, chemicals, diseases, genes/proteins, species, COVID-19-related terms.  

![](tutorials/imgs/pipeline3.png)

## How to use the pipeline

A detailed guide, including installation, configuration and inference tutorial can be found in this [collection of tutorials](tutorials/Tutorial-pipeline.md).

### Quick start guide

1. Before installation: Downnload and install anaconda from https://www.anaconda.com/


2. Clone the repository to your target folder


```console
git clone https://github.com/Aitslab/EasyNER

```

3. Set up an conda environment

```console
cd EasyNER
conda env create -f environment.yml
```

4. Load spacy

```console

python -m spacy download en_core_web_sm
```

5. After installation activate the environment:
```console

conda activate easyner_env

```


6. Provide input file: list of PubMed IDs, CORD19 metadata.csv file, or file with free text.


7. Add the correct paths to your input file in the [config file](config.json) and choose the modules you want to run in the “ignore” section in the beginning of the file. 


8. Run the pipeline with the following command:

```python
python main.py
```

9. The output will consist of a ranked list [(example)](results/sample_output/analysis_mtorandtsc1_chemical/mtorandtsc1_result_chemical.tsv) and a graph [(example)](results/sample_output/analysis_mtorandtsc1_chemical/mtorandtsc1_chemical_top_50.png) and files with the annotated text.




___

## Bulk Download PubMED

The EasyNER pipeline includes an additional script for bulk downloading PubMed abstracts. For that, simply open a terminal in the EasyNER folder and run the following script:
```console

conda activate easyner_env
cd pubmed_loader
python pubmed_main.py

```

The above script will download, process and convert (to json) PubMed abstract collection from the 2023 annual baseline (more insight here: https://ftp.ncbi.nlm.nih.gov/pubmed/). You can also specify the file numbers as follows to download files from 0 to 100:

```console
python pubmed_main.py -s 0 -e 100

```

To process the bulk PubMed files through the pipeline, all you need to do is to make the following changes in the config file:

1. In the ignore section, make sure that the downloader, cord_loader and text_loader parameters are set to true.
2. In the splitter section Specify the pubmed folder path in the "input_path" parameter.
3. In the splitter section, set "pubmed_pre_batched" to true.

Then run the pipeline as you would normally.

## NER 

### [BioBERT](https://github.com/dmis-lab/biobert-pytorch)-based NER

1. Cell-lines: biobert_huner_cell_v1 
2. Chemical: biobert_huner_chemical_v1
3. Disease: biobert_huner_disease_v1
4. Gene/protein: biobert_huner_gene_v1
5. Species: biobert_huner_species_v1

The BioBERT models above have been fine-tuned using the [HUNER corpora](https://github.com/hu-ner/huner) and uploaded to [huggingface hub](https://huggingface.co/aitslab). These and similar models can be loaded from the huggingface hub by setting the "model_path" to "aitslab" and "model_name" to the model intended for use in the NER section of the config file. For example:

```console
"model_type": "biobert_finetuned",
"model_path": "aitslab",
"model_name": "biobert_huner_chemical_v1"
```

### Dictionary-based NER
[Spacy Phrasematcher](https://spacy.io/api/phrasematcher) is used to load dictionaries and run NER. COVID-19 related disease and virus dictionaries are provided [here](dictionaries/). 
Dictionary based NER can be run by specifying model_type as "spacy_phrasematcher", "model_name" as the spacy model (like, "en_core_web_sm" model) and specifying the "vocab_path" (path_to_dictionary) in the NER section of the config file. For example:

```console
"model_type": "spacy_phrasematcher",
"model_path": "",
"model_name": "en_core_web_sm",
"vocab_path": "dictionaries/sars-cov-2_synonyms_v2.txt"
```

#### For BioBERT model training script follow this [tutorial](tutorials/Tutorial-BioBERT_model_training.ipynb)
#### All preprocessing scripts can be found [here](supplementary/preprocessing_scripts/)


## Citation
If you use any of the material in this repository, please cite the following article:

```bibtex
@article{ahmed2023easyner,
  title={EasyNER: A Customizable Easy-to-Use Pipeline for Deep Learning- and Dictionary-based Named Entity Recognition from Medical Text},
  author={Rafsan Ahmed and Petter Berntsson and Alexander Skafte and Salma Kazemi Rashed and Marcus Klang and Adam Barvesten and Ola Olde and William Lindholm and Antton Lamarca Arrizabalaga and Pierre Nugues and Sonja Aits},
  year={2023},
  eprint={2304.07805},
  archivePrefix={arXiv},
  primaryClass={q-bio.QM}
}
```
