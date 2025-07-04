# Additional Information for Author Feedback

| index | table_name       | token_count | line_count |
|-------|------------------|-------------|------------|
| 0     | WHS6_150         | 1235        | 58         |
| 1     | SA_0000001423    | 13634       | 573        |
| 2     | SA_0000001455    | 17097       | 765        |
| 3     | PCV3             | 26856       | 1381       |
| 4     | MCV2             | 56745       | 2878       |
| 5     | WHOSIS_000001    | 64592       | 2329       |
| 6     | HRH_26           | 67251       | 1385       |
| 7     | MDG_0000000026   | 68961       | 3420       |
| 8     | MORT_MATERNALNUM | 70014       | 3420       |
| 9     | MDG_0000000025   | 71243       | 2030       |
| 10    | HIV_0000000026   | 79515       | 3829       |
| 11    | MDG_0000000020   | 85776       | 4282       |
| 12    | SDGMALARIA       | 102089      | 3021       |
| 13    | WHOSIS_000003    | 274290      | 9648       |
| 14    | WHS2_131         | 322649      | 11640      |
| 15    | NCD_DTH_TOT      | 324006      | 11640      |
| 17    | vdpt             | 389328      | 12294      |
| 18    | CM_01            | 849988      | 32862      |

We took the table WHS6_150 which is the only table that can be loaded into LLaMA 2 completely, randomly removed 50% of the values for the attribute _"Community health workers density (per 10 000 population)"_ and asked the LLM to fill in those values directly. We did 100 runs of which 95 failed to produce valid results (a repeat of the experiment did not yield any run with valid results):

| Error type                                  | #Runs | priority |
|---------------------------------------------|-------|----------|
| Failed to parse returned table to CSV       | 72    | 2.       |
| Returned table is shorter than the original | 12    | 3.       |
| Failed to find table in answer              | 8     | 1.       |
| Context attributes were changed             | 3     | 4.       |

Please note that the error types are not disjoint. If an error is encountered the run is aborted. This means that additional errors might occur in the same run that are not counted. The error type with lower priority is checked first (i.e., Failed to find table in answer).

When we repeated the experiment (first with 100 runs and then with 1000 runs) the LLM was not able to produce any valid results at all.

We also collected a random sample of 100 records from CM_01 and repeated the process. We computed 1000 runs of which none resulted in a valid result:

| Error type                                  | #Runs | priority |
|---------------------------------------------|-------|----------|
| Failed to parse returned table to CSV       | 340   | 2.       |
| Returned table is shorter than the original | 340   | 3.       |
| Failed to find table in answer              | 320   | 1.       |
| Context attributes were changed             | 0     | 4.       |

These experiments show that LLaMA 2 is not applicable as a replacement for established missing value imputation approaches.

# Proxy-Enriched Imputation

### Data Sets

We extracted the data sets used in our evaluation from the following sources:

1. Global Health Observatory (GHO): We used the API provided at https://www.who.int/data/gho/info/gho-odata-api to download the GHO data
2. HEAT Plus Data Repository: https://www.who.int/data/inequality-monitor/data

The witnesses we ultimately used for imputation can be found in the folder _Data Sets_.

### Narratives

The narratives used in our evaluation can be found in the folder _Narratives_. They have been extracted from the following WHO Data Stories:

- World Health Statistics 2023: https://www.who.int/data/stories/world-health-statistics-2023-a-visual-summary
- World Health Statistics 2021: https://www.who.int/data/stories/world-health-statistics-2021-a-visual-summary
- World Health Statistics 2020: https://www.who.int/data/gho/whs-2020-visual-summary
- Leading causes of death and disability: https://www.who.int/data/stories/leading-causes-of-death-and-disability-2000-2019-a-visual-summary

### Proxies

The ranked lists of proxy attributes identified by the LLM and by applying the Sentence Embedding can be found in the folder _ProxyLists_.

## Evaluation

### Identification of Proxies

The identification of proxy attributes requires

1) a list of attributes for which proxies should be computed (for our evaluation, we used the attributes in the _MatchedAttribute_ column of the _/Witnesses/IdentifiedWitnesses.csv_ file)
2) a list of proxy candidates (for our evaluation, we used the attribute list _/ProxyLists/WHOAttributes.txt_)

 The proxy identification of our evaluation can then be reproduced as follows:

- LLM: Provide each pair of attribute (i) and proxy candidate (p) to LLaMA 2 (https://www.llama.com/llama2/) using the prompt as shown in figure 4 of our paper. A subsequent ranking of the identified proxies can be achieved by using the prompt as shown in figure 5 (use all pairings of proxies p<sub>a</sub> and p<sub>b</sub>).
- Sentence Embedding: For each pair of attribute and proxy candidate compute the cosine similarity using SBERT (https://sbert.net/).
- Random: Compute a random subset of the provided proxy candidates.

### Imputation

The evaluation as described in our paper can be conducted by running the python script "evalScript_v2_10runs_all_modes.py" which can be found in the folder _Scripts_. It requires the following arguments:

  1) path to first table
  2) path to second table
  3) to-be-imputed attribute (surrounded by "")
  4) percentage of missing values
  5) missing pattern (_random_, _not_random_)

An example looks as follows:
python3 evalScript_v2_10runs_all_modes.py SDGMALARIA_j_1_real.csv SDGMALARIA_j_1_rand.csv "Malaria incidence (per 1 000 population at risk)" 10 random

Please note that in the version of the script provided in the _Scripts_ folder the arguments (4) and (5) are not relevant. A single call of the script will compute results for both missing patterns (MCAR, MNAR) and all percentages of missing values (10%, 20%, 30%, 40%, 50%) applied in our paper.

The script will generate a txt-file which contains the average MAE and RMSE over 10 runs for both missing patterns and all percentages of missing values for both tables provided as arguments. 

The tables used in our evaluation can be found in the folders _Data Sets_ (original data sets without proxies) and _JoinedTables_. The latter contains the original data sets joined with the identified proxy attributes (from 1 to 5 proxies). They are split into two folders, of which _SE_ contains those tables with proxies identified via sentence embedding, while _LLM_ contains those tables with proxies identified by the LLM and those with random proxies (filenames contain _real and _rand respectively, while j_n specifies the number of tables joined). The associated log-files list the WHO-tables that contain the joined proxy attributes, including unsuccesfull joins. 
