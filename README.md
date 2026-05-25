# Gene Ontology Annotation Database

This project designs and implements a relational MySQL database for storing and querying Gene Ontology (GO) annotations from bacterial Gene Annotation Format (GAF) files.

The database was developed as part of a Data Management and Cloud Technologies assignment. It focuses on transforming tab-delimited biological annotation files into a structured relational schema that supports organism comparison, protein-function analysis, evidence-code review, and competence-related GO term queries.

## Project Overview

A biopharmaceutical company requires a database to compare bacterial organisms based on protein features. Each input file represents one organism and contains protein annotations linked to GO terms.

The Python application reads the provided `.gaf` files and generates a SQL script that:

- Creates the database schema
- Defines primary keys, foreign keys, uniqueness constraints, and indexes
- Populates the database with organisms, proteins, GO terms, and annotations
- Supports reusable example queries through `examples.sql`

## Database Schema

The database contains five main tables:

- `organism`: stores bacterial organism metadata
- `protein`: stores protein identifiers and related organism information
- `go_term`: stores distinct Gene Ontology terms
- `annotation`: stores protein-to-GO annotation records with evidence metadata
- `go_relationship`: supports future modelling of GO term hierarchy relationships

The `annotation` table acts as the central junction table between proteins and GO terms, resolving the many-to-many relationship between them.

## Folder Structure

```text
gene_ontology_database/
│
├── input_files/              # Input GAF files; not submitted
│   ├── Bacillus_subtilis_168-224308.gaf
│   ├── Escherichia_coli_K-12_ecocyc_83333.gaf
│   └── ...
│
└── 24037169/                 # my student ID
    ├── app.py                # Main Python application
    ├── result.sql            # Generated schema and insert script
    ├── examples.sql          # Example analytical queries
    └── README.md

```
## How to Run

From the folder containing app.py, run:

```text
python app.py
```

This generates:
```text
result.sql
```
Open result.sql in MySQL Workbench and execute the script against your selected schema.

## Example Queries

The examples.sql file includes five analytical queries, such as:

- Annotation coverage per organism
- Most frequent GO terms per organism
- Proteins associated with a selected GO term
- Evidence-code distribution by organism
- Identification of organisms with competence-related annotations using GO:0030420

## Technologies Used
- Python
- MySQL
- MySQL Workbench

## Notes

The go_relationship table is included to support future integration of Gene Ontology hierarchy data. The provided GAF files contain annotation assignments but not GO parent-child relationships, so this table may initially be empty.

## How It Works

The application follows a simple ETL-style workflow:

- Reads all .gaf files from the input_files directory
- Extracts relevant fields such as protein ID, GO ID, evidence code, references, taxon, date, and assigned-by source
- Deduplicates organisms, proteins, and GO terms
- Generates CREATE TABLE statements
- Generates INSERT statements for data population
- Writes the final SQL output to result.sql


## Author

Sergio Araya
