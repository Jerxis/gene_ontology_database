#The following code is a Python script that processes Gene Ontology Annotation Files (GAF) to generate SQL statements for creating and populating a relational database. 
#The script reads multiple GAF files, extracts relevant information about organisms, proteins, GO terms, and annotations, and then constructs SQL DDL and DML 
#statements to create the database schema and insert the data. The resulting SQL is written to a file named result.sql. The script includes helper functions for 
#parsing GAF files, escaping SQL values, and determining file paths, as well as a main function that orchestrates the entire process.

#Author: Sergio Araya
#Student ID: 24037169
#Last edited: 2026-02-26

#-------------------------------------------------------------------------

import os
from typing import Dict, Iterable, List, Optional, Set, Tuple

# -----------------------------
# Configuration / Metadata

# Key = source filename, Value = scientific name. 
# Not needed but nice to have proper names in the database instead of just file names
ORGANISM_NAME_BY_FILE = {
    "Escherichia_coli_K-12_ecocyc_83333.gaf": "Escherichia coli K-12",
    "Bacillus_subtilis_168-224308.gaf": "Bacillus subtilis 168",
    "Bacillus_amyloliquefaciens_FZB42-326423.gaf": "Bacillus amyloliquefaciens FZB42",
    "Bacillus_licheniformis_ATCC_14580-279010.gaf": "Bacillus licheniformis ATCC 14580",
    "Bacillus_megaterium_DSM_319-592022.gaf": "Bacillus megaterium DSM 319",
    "Geobacillus_kaustophilus_HTA426-235909.gaf": "Geobacillus kaustophilus HTA426",
    "Geobacillus_thermodenitrificans_NG80_2-420246.gaf": "Geobacillus thermodenitrificans NG80",
}



# Helpers functions

#this function takes a string and returns a SQL-safe version of it, properly escaped and quoted for use in an SQL statement
def sql_escape(value: Optional[str]) -> str:
    """
    Escapes a Python string for safe inclusion in SQL single-quoted literals.
    Returns 'NULL' for None/empty.
    """
    if value is None:
        return "NULL"
    v = str(value)
    if v == "" or v.lower() == "nan":
        return "NULL"
    # Escape backslashes first, then single quotes
    v = v.replace("\\", "\\\\").replace("'", "''")
    return f"'{v}'"

# this function is a generator that yields parsed GAF rows as lists of strings, skipping comments and malformed lines
def iter_gaf_rows(file_path: str) -> Iterable[List[str]]:
    """
    Yields parsed GAF rows as a list of 17 columns (strings).
    Skips comment lines starting with '!'.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            if not line or line.startswith("!"):
                continue

            cols = line.split("\t")
            if len(cols) < 15:
                # Malformed row (should be 17). Skip safely
                continue

            # Pad to 17 to avoid index errors if shorter
            if len(cols) < 17:
                cols = cols + [""] * (17 - len(cols))

            yield cols

#helper functions to determine file paths for input and output, ensuring that the code can be run from any location without hardcoding paths
def get_project_base_dir(app_file: str) -> str:
    """
    Given __file__ of app.py in STUDENT_ID/, returns the project root (parent of STUDENT_ID/).
    """
    student_dir = os.path.dirname(os.path.abspath(app_file))
    base_dir = os.path.dirname(student_dir)
    return base_dir


def get_input_dir(app_file: str) -> str:
    return os.path.join(get_project_base_dir(app_file), "input_files")


def getInputFiles(app_file: str) -> List[str]:
    input_dir = get_input_dir(app_file)
    return sorted([
        f for f in os.listdir(input_dir)
        if f.endswith(".gaf")
        and not f.startswith(".")
        and os.path.isfile(os.path.join(input_dir, f))
    ])

# This function returns a string containing the SQL DDL statements to create the database schema for the project
def build_schema_sql() -> str:
    """
    MySQL 8 compatible DDL.
    """
    return """
-- ===============================
-- Project 1 Database Schema
-- ===============================

DROP TABLE IF EXISTS go_relationship;
DROP TABLE IF EXISTS annotation;
DROP TABLE IF EXISTS go_term;
DROP TABLE IF EXISTS protein;
DROP TABLE IF EXISTS organism;

CREATE TABLE organism (
    organism_id INT AUTO_INCREMENT PRIMARY KEY,
    scientific_name VARCHAR(255) NOT NULL,
    source_file VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE protein (
    protein_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    organism_id INT NOT NULL,
    db_object_id VARCHAR(64) NOT NULL,
    db_object_symbol VARCHAR(64) NOT NULL,
    db_object_name VARCHAR(255) NULL,
    db_object_type VARCHAR(32) NOT NULL,
    taxon VARCHAR(64) NOT NULL,

    CONSTRAINT fk_protein_organism
        FOREIGN KEY (organism_id)
        REFERENCES organism (organism_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT uq_protein_org_object
        UNIQUE (organism_id, db_object_id)
) ENGINE=InnoDB;

CREATE TABLE go_term (
    go_id CHAR(10) PRIMARY KEY,
    aspect CHAR(1) NOT NULL,

    CONSTRAINT chk_go_aspect
        CHECK (aspect IN ('F','P','C'))
) ENGINE=InnoDB;

CREATE TABLE annotation (
    annotation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    protein_id BIGINT NOT NULL,
    go_id CHAR(10) NOT NULL,
    db VARCHAR(32) NOT NULL,
    qualifier VARCHAR(255) NULL,
    db_reference VARCHAR(255) NOT NULL,
    evidence_code VARCHAR(8) NOT NULL,
    with_from TEXT NULL,
    assigned_by VARCHAR(64) NOT NULL,
    annotation_date CHAR(8) NOT NULL,

    CONSTRAINT fk_annotation_protein
        FOREIGN KEY (protein_id)
        REFERENCES protein (protein_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_annotation_go
        FOREIGN KEY (go_id)
        REFERENCES go_term (go_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_annotation_natural
        UNIQUE (protein_id, go_id, db_reference, evidence_code, assigned_by, annotation_date),

    INDEX idx_annotation_go (go_id),
    INDEX idx_annotation_protein (protein_id)
) ENGINE=InnoDB;

-- Optional: supports recursive "subterm" analysis if ontology relations are imported later
CREATE TABLE go_relationship (
    parent_go_id CHAR(10) NOT NULL,
    child_go_id CHAR(10) NOT NULL,
    rel_type VARCHAR(32) NOT NULL DEFAULT 'is_a',

    PRIMARY KEY (parent_go_id, child_go_id, rel_type),

    CONSTRAINT fk_go_rel_parent
        FOREIGN KEY (parent_go_id)
        REFERENCES go_term (go_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_go_rel_child
        FOREIGN KEY (child_go_id)
        REFERENCES go_term (go_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ===============================
-- End of Schema
-- ===============================

"""

#note: the go_relationship table is included in the schema for potential future use if we want to import GO ontology relationships, 
#but it's not populated since the input files don't contain that information. It allows for recursive queries to find parent/child terms if needed later on

# Main generator function


def generate_sql():
    """
    Generates result.sql containing DDL + INSERT statements.
    """
    app_file = __file__
    input_dir = get_input_dir(app_file)
    files = getInputFiles(app_file)

    # ---- ID maps (explicit IDs make FK inserts deterministic) ----
    organism_id_by_file: Dict[str, int] = {}
    protein_id_by_key: Dict[Tuple[int, str], int] = {}  # (organism_id, db_object_id) -> protein_id

    # ---- Dedup structures ----
    go_terms: Dict[str, str] = {}  # go_id -> aspect
    annotations: List[Tuple[int, str, str, Optional[str], str, str, Optional[str], str, str]] = []
    # tuple = (protein_id, go_id, db, qualifier, db_reference, evidence_code, with_from, assigned_by, date)

    # ---- Counters ----
    next_organism_id = 1
    next_protein_id = 1

    # 1) Parse input files
    for fname in files:
        fpath = os.path.join(input_dir, fname)

        # Assign organism id
        if fname not in organism_id_by_file:
            organism_id_by_file[fname] = next_organism_id
            next_organism_id += 1
        organism_id = organism_id_by_file[fname]

        for cols in iter_gaf_rows(fpath):
            # GAF 2.0 columns (0-based):
            # 0 DB
            # 1 DB Object ID
            # 2 DB Object Symbol
            # 3 Qualifier
            # 4 GO ID
            # 5 DB:Reference
            # 6 Evidence Code
            # 7 With/From
            # 8 Aspect
            # 9 DB Object Name
            # 11 DB Object Type
            # 12 Taxon
            # 13 Date
            # 14 Assigned By

            db = cols[0].strip()
            db_object_id = cols[1].strip()
            db_object_symbol = cols[2].strip()
            qualifier = cols[3].strip() or None
            go_id = cols[4].strip()
            db_reference = cols[5].strip()
            evidence_code = cols[6].strip()
            with_from = cols[7].strip() or None
            aspect = cols[8].strip()
            db_object_name = cols[9].strip() or None
            db_object_type = cols[11].strip()
            taxon = cols[12].strip()
            date = cols[13].strip()
            assigned_by = cols[14].strip()

            # Basic validity checks
            if not (db_object_id and go_id and db_reference and evidence_code and aspect and date and assigned_by and db_object_type and taxon and db):
                continue

            # Protein ID assignment (dedupe within organism)
            protein_key = (organism_id, db_object_id)
            if protein_key not in protein_id_by_key:
                protein_id_by_key[protein_key] = next_protein_id
                next_protein_id += 1

            protein_id = protein_id_by_key[protein_key]

            # Record GO term (dedupe)
            # If the same GO appears with different aspects (unlikely), keep the first.
            if go_id not in go_terms:
                go_terms[go_id] = aspect

            # Record annotation row (keep as-is; dedupe handled by UNIQUE constraint too)
            annotations.append(
                (protein_id, go_id, db, qualifier, db_reference, evidence_code, with_from, assigned_by, date)
            )

    # 2) Build SQL (DDL + INSERTs)
    ddl_sql = build_schema_sql()

    # INSERT: organism
    organism_inserts: List[str] = []
    for source_file, org_id in sorted(organism_id_by_file.items(), key=lambda x: x[1]):
        sci_name = ORGANISM_NAME_BY_FILE.get(source_file)

        # Fallback: derive readable name from filename if not in mapping
        if not sci_name:
            sci_name = source_file.replace(".gaf", "").replace("_", " ")

        organism_inserts.append(
            "INSERT INTO organism (organism_id, scientific_name, source_file) VALUES "
            f"({org_id}, {sql_escape(sci_name)}, {sql_escape(source_file)});"
        )

    # INSERT: protein
    # We need protein attributes, we only stored IDs so far.
    # Re-scan to capture stable attributes for each protein_id.
    # (This keeps parsing logic simple + avoids storing huge dicts per row.)
    protein_attrs: Dict[int, Tuple[int, str, str, Optional[str], str, str]] = {}
    # protein_id -> (organism_id, db_object_id, db_object_symbol, db_object_name, db_object_type, taxon)

    # Build reverse map for faster lookup of organism by file while rescanning
    file_by_organism_id = {v: k for k, v in organism_id_by_file.items()}

    for organism_id, fname in sorted(file_by_organism_id.items(), key=lambda x: x[0]):
        fpath = os.path.join(input_dir, fname)
        for cols in iter_gaf_rows(fpath):
            db_object_id = cols[1].strip()
            db_object_symbol = cols[2].strip()
            db_object_name = cols[9].strip() or None
            db_object_type = cols[11].strip()
            taxon = cols[12].strip()

            if not (db_object_id and db_object_symbol and db_object_type and taxon):
                continue

            protein_id = protein_id_by_key.get((organism_id, db_object_id))
            if protein_id is None:
                continue

            # Only set once (first occurrence wins)
            if protein_id not in protein_attrs:
                protein_attrs[protein_id] = (
                    organism_id, db_object_id, db_object_symbol, db_object_name, db_object_type, taxon
                )

    protein_inserts: List[str] = []
    for protein_id in sorted(protein_attrs.keys()):
        organism_id, db_object_id, db_object_symbol, db_object_name, db_object_type, taxon = protein_attrs[protein_id]
        protein_inserts.append(
            "INSERT INTO protein (protein_id, organism_id, db_object_id, db_object_symbol, db_object_name, db_object_type, taxon) VALUES "
            f"({protein_id}, {organism_id}, {sql_escape(db_object_id)}, {sql_escape(db_object_symbol)}, {sql_escape(db_object_name)}, {sql_escape(db_object_type)}, {sql_escape(taxon)});"
        )


    # INSERT: go_term
    go_inserts: List[str] = []
    for go_id in sorted(go_terms.keys()):
        aspect = go_terms[go_id]
        go_inserts.append(
            "INSERT INTO go_term (go_id, aspect) VALUES "
            f"({sql_escape(go_id).strip()}, {sql_escape(aspect).strip()});"
        )

    # INSERT: annotation
    annotation_inserts: List[str] = []
    for (protein_id, go_id, db, qualifier, db_reference, evidence_code, with_from, assigned_by, date) in annotations:
        annotation_inserts.append(
            #here I needed to use INSERT IGNORE to avoid duplicates that violate the UNIQUE constraint, since Im not doing deduplication in Python for simplicity
            "INSERT IGNORE INTO annotation (protein_id, go_id, db, qualifier, db_reference, evidence_code, with_from, assigned_by, annotation_date) VALUES "
            f"({protein_id}, {sql_escape(go_id)}, {sql_escape(db)}, {sql_escape(qualifier)}, {sql_escape(db_reference)}, {sql_escape(evidence_code)}, {sql_escape(with_from)}, {sql_escape(assigned_by)}, {sql_escape(date)});"
        )

    # Combine DDL and DML with comments for clarity
    dml_sql = "\n".join([
        "-- ===============================",
        "-- Data population",
        "-- ===============================",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "",
        "-- Organisms",
        *organism_inserts,
        "",
        "-- Proteins",
        *protein_inserts,
        "",
        "-- GO Terms",
        *go_inserts,
        "",
        "-- Annotations",
        *annotation_inserts,
        "",
        "SET FOREIGN_KEY_CHECKS = 1;",
        "-- ===============================",
        "-- End of data population",
        "-- ===============================",
        ""
    ])

    final_sql = ddl_sql + "\n" + dml_sql

    # 3) Write result.sql
    current_dir = os.path.dirname(os.path.abspath(app_file))
    output_path = os.path.join(current_dir, "result.sql")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_sql)

    print(f"Processed {len(files)} input files from: {input_dir}")
    print(f"Organisms: {len(organism_id_by_file)}")
    print(f"Proteins: {len(protein_attrs)}")
    print(f"GO terms: {len(go_terms)}")
    print(f"Annotations: {len(annotations)}")
    print(f"SQL written to: {output_path}")


if __name__ == "__main__":
    generate_sql()

