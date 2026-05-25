-- =========================================================
-- examples.sql
-- 5 example queries demonstrating database usefulness
-- =========================================================

-- Example 1: Overview of annotation coverage per organism
-- Real-life question: “Which organisms are best-annotated, and how dense is their functional information?”
SELECT
    o.scientific_name,
    o.source_file,
    COUNT(a.annotation_id) AS total_annotations,
    COUNT(DISTINCT p.protein_id) AS proteins_annotated,
    ROUND(COUNT(a.annotation_id) / COUNT(DISTINCT p.protein_id), 2) AS avg_annotations_per_protein
FROM organism o
JOIN protein p ON p.organism_id = o.organism_id
JOIN annotation a ON a.protein_id = p.protein_id
GROUP BY o.organism_id, o.scientific_name, o.source_file
ORDER BY total_annotations DESC;


-- Example 2: Functional fingerprint comparison (Top GO terms) for a given organism
-- Real-life question: “What are the dominant biological functions/features in organism X?”
-- Replace the source_file filter as needed.
SELECT
    o.scientific_name,
    a.go_id,
    COUNT(*) AS assignments
FROM organism o
JOIN protein p ON p.organism_id = o.organism_id
JOIN annotation a ON a.protein_id = p.protein_id
WHERE o.source_file = 'Bacillus_subtilis_168-224308.gaf'
GROUP BY o.scientific_name, a.go_id
ORDER BY assignments DESC
LIMIT 15;


-- Example 3: Find proteins associated with a specific GO term across all organisms
-- Real-life question: “Which organisms/proteins are linked to function GO:0003677 (DNA binding)?”
SELECT
    o.scientific_name,
    p.db_object_id,
    p.db_object_symbol,
    p.db_object_name,
    a.go_id,
    a.evidence_code,
    a.assigned_by,
    a.annotation_date
FROM annotation a
JOIN protein p ON p.protein_id = a.protein_id
JOIN organism o ON o.organism_id = p.organism_id
WHERE a.go_id = 'GO:0003677'
ORDER BY o.scientific_name, p.db_object_symbol;


-- Example 4: Evidence quality / reliability profile by organism
-- Real-life question: “How strong is the evidence behind annotations for each organism?”
SELECT
    o.scientific_name,
    a.evidence_code,
    COUNT(*) AS n_annotations
FROM organism o
JOIN protein p ON p.organism_id = o.organism_id
JOIN annotation a ON a.protein_id = p.protein_id
GROUP BY o.scientific_name, a.evidence_code
ORDER BY o.scientific_name, n_annotations DESC;


-- Example 5: Identify organisms that may exhibit competence
-- Real-life question: “Which organisms show signals of competence for transformation (GO:0030420)?”
-- Note: This query uses only the term GO:0030420 directly (subterms require ontology relationships).
SELECT
    o.scientific_name,
    o.source_file,
    COUNT(*) AS competence_go_assignments,
    COUNT(DISTINCT p.protein_id) AS proteins_implicated
FROM organism o
JOIN protein p ON p.organism_id = o.organism_id
JOIN annotation a ON a.protein_id = p.protein_id
WHERE a.go_id = 'GO:0030420'
GROUP BY o.organism_id, o.scientific_name, o.source_file
ORDER BY competence_go_assignments DESC;