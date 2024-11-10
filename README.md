# BSRD data
We have backed up the sRNA data provided in the BSRD database in BSRD_data, please cite the paper first if you want to use it.[Li L, Huang D, Cheung M K, et al. BSRD: a repository for bacterial small regulatory RNA[J]. Nucleic acids research, 2013, 41(D1): D233-D238.](https://academic.oup.com/nar/article/41/D1/D233/1072873)

# sRNAdeep

This repository includes the code used in our sRNAdeep method.To use or refer to the sRNAdeep method, cite [Qian W, Sun J, Liu T, et al. sRNAdeep: a novel tool for bacterial sRNA prediction based on DistilBERT encoding mode and deep learning algorithms[J]. BMC genomics, 2024, 25(1): 1021.](https://link.springer.com/article/10.1186/s12864-024-10951-6)

## Code overview

### 0. 00-do_blastn.py
Use ` python 00-do_blastn.py fasta_folder ` to filter the test set for matches to the training set.

### 0. 00-csv2fasta.ipynb
Convert sequences in csv files to fasta

### 1. 01-data_process.ipynb 
This includes (1) filtering out sequences from blastn results that match the training set; (2) calculating the %GC content of fasta sequences; and (3) converting fasta into the appropriate input format for sRNAdeep.

### 2. 02-rna-identify-bert.ipynb
This file contains the construction, training and prediction of the sRNAdeep model. Just replace the path_of_data and test_path in it with the paths to the training set and test set files after the fasta transformation in step 3 of 01-data_process.ipynb. The required dependencies are listed below:
* pandas 2.1.4
* numpy 1.24.3
* matplotlib 3.7.4
* scikit-learn 1.2.2
* torch 2.0.0
* transformers 4.36.0

### 3. 03-enrichment.R
It's for R. BP, CC, MF, KEGG downloaded from David.

