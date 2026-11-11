# GraphRAG_MOF


A work-in-progress project exploring the use of knowledge graphs and retrieval-augmented generation (RAG) for Metal-Organic Framework (MOF) research.

The aim is to connect crystallographic data from CIF files with information extracted from scientific literature, creating a structured source of information that can support more complex scientific queries.

## Current Progress

### CIF Processing
- Extracting crystallographic information from CIF files using [Gemmi](https://gemmi.readthedocs.io/).
- Processing structural information, including chemical formulae, unit cell parameters, symmetry and atomic sites.
- Linking crystallographic structures to their associated research papers.
- Saving extracted information in structured JSON format.

### Scientific Literature Processing
- Extracting PDF content and document structure using [Marker](https://github.com/datalab-to/marker).
- Cleaning and organising extracted text, including references, headings and captions.
- Caching processed documents to avoid repeated PDF conversion.
- Developing NER-based methods to identify scientific entities, followed by LLM-assisted entity resolution and agent-based linking.

## Project Structure

```text
GraphRAG_MOF/
├── data/
│   ├── tracking/
│   ├── raw/
│   ├── ready/
│   ├── processed/
│   └── markercache/
├── src/
│   └── mof_rag/
│       ├── cache/
│       ├── config/
│       ├── extractors/
│       ├── pipelines/
│       └── processors/
├── tests/
├── main.py
└── pyproject.toml
```

## Planned Work

- Improve scientific information extraction from research papers.
- Develop a structured representation linking MOFs, properties, synthesis information and literature.
- Build a knowledge graph from the extracted information.
- Implement graph-based retrieval and RAG for scientific question answering.
- Evaluate extraction accuracy and retrieval performance.

## Technologies

Python · Gemmi · Marker · Pydantic · PydanticAI · Ollama

## Status

This project is under active development. The current focus is on reliable extraction and processing of crystallographic and scientific literature data before developing the knowledge graph and retrieval components.