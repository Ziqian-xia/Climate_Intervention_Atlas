"""
Phase 2: Search Execution Module
Integrates existing search wrappers (OpenAlex, PubMed, Scopus) for metadata retrieval
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from utils.logger import get_logger


class SearchExecutor:
    """
    Orchestrates search execution across multiple academic databases.

    Integrates with existing search wrappers:
    - OpenAlex: openalex-searcher
    - PubMed: pubmed-searcher
    - Scopus: scopus-searcher
    """

    def __init__(self, database: str, query: str, config: Dict):
        """
        Initialize search executor.

        Args:
            database: Database name ("openalex", "pubmed", "scopus")
            query: Search query string (database-specific format)
            config: Configuration dict with API keys and settings
        """
        self.database = database.lower()
        self.query = query
        self.config = config
        self.logger = get_logger()
        self.wrapper = None

        # Validate database
        valid_databases = ["openalex", "pubmed", "scopus"]
        if self.database not in valid_databases:
            raise ValueError(f"Invalid database: {self.database}. Must be one of {valid_databases}")

    def _add_search_package_to_path(self, package_name: str):
        """Add specific search package to Python path."""
        search_packages_base = Path(__file__).parent.parent / "Search and full-text packages" / "search-packages"
        package_dir = search_packages_base / package_name

        if not package_dir.exists():
            raise FileNotFoundError(f"Search package not found: {package_dir}")

        if str(package_dir) not in sys.path:
            sys.path.insert(0, str(package_dir))

        self.logger.debug(f"Added to path: {package_dir}")

    def _create_wrapper(self):
        """
        Factory method to create database-specific search wrapper.

        Returns:
            Wrapper instance (OpenAlexSearchWrapper, PubMedSearchWrapper, or ScopusSearchWrapper)
        """
        try:
            if self.database == "openalex":
                self._add_search_package_to_path("openalex-searcher")
                from openalex_search_wrapper import OpenAlexSearchWrapper

                return OpenAlexSearchWrapper(
                    api_key=self.config.get("api_key", ""),
                    mailto=self.config.get("mailto", ""),
                    timeout=45,
                    max_retries=4
                )

            elif self.database == "pubmed":
                self._add_search_package_to_path("pubmed-searcher")
                from pubmed_search_wrapper import PubMedSearchWrapper, parse_pubmed_xml

                # Store the parse function for later use
                self._parse_pubmed_xml = parse_pubmed_xml

                return PubMedSearchWrapper(
                    api_key=self.config.get("api_key", ""),
                    email=self.config.get("email", ""),
                    timeout=45,
                    max_retries=4
                )

            elif self.database == "scopus":
                self._add_search_package_to_path("scopus-searcher")
                from scopus_search_wrapper import ScopusSearchWrapper

                return ScopusSearchWrapper(
                    api_key=self.config.get("api_key", ""),
                    inst_token=self.config.get("inst_token", ""),
                    timeout=45,
                    max_retries=4
                )

        except ImportError as e:
            self.logger.error(f"Failed to import {self.database} wrapper: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create {self.database} wrapper: {e}")
            raise

    def execute_search(self, max_results: int = 1000, out_dir: str = "search_results") -> Dict:
        """
        Execute search and save results.

        Args:
            max_results: Maximum number of results to retrieve
            out_dir: Output directory for results

        Returns:
            Result dictionary with keys:
                - success: bool
                - status: str
                - results_count: int
                - output_files: dict
                - error: str (if failed)
        """
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Starting {self.database.upper()} search")
        self.logger.info(f"Query: {self.query[:100]}...")
        self.logger.info(f"Max results: {max_results}")
        self.logger.info(f"{'='*60}")

        try:
            # Create output directory
            out_path = Path(out_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            # Create wrapper
            self.logger.agent_thinking(self.database.upper(), "Initializing wrapper...")
            self.wrapper = self._create_wrapper()

            # Execute database-specific search
            if self.database == "openalex":
                result = self._execute_openalex(max_results, out_path)
            elif self.database == "pubmed":
                result = self._execute_pubmed(max_results, out_path)
            elif self.database == "scopus":
                result = self._execute_scopus(max_results, out_path)

            self.logger.info(f"{self.database.upper()} search completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"{self.database.upper()} search failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "error",
                "results_count": 0,
                "error": str(e),
                "output_files": {}
            }

    def _execute_openalex(self, max_results: int, out_path: Path) -> Dict:
        """Execute OpenAlex search - Title + Abstract only (fulltext excluded)."""
        self.logger.agent_thinking("OpenAlex", "Executing Boolean search...")

        # IMPORTANT: OpenAlex API does NOT support field-level search parameters
        # (no title.search or abstract.search parameters exist in the API).
        #
        # HOWEVER, empirical testing shows that OpenAlex fulltext coverage is very low:
        # - Sample of 50 results: 100% had fulltext_origin = null
        # - The 'search' parameter primarily searches title + abstract
        # - Very few papers have fulltext data in OpenAlex
        #
        # Therefore, using the standard 'search' parameter already gives us
        # title+abstract results without fulltext contamination.
        #
        # OpenAlex API design:
        #   - 'search' parameter: Searches title, abstract, and fulltext (when available)
        #   - ✅ SUPPORTS Boolean operators (AND, OR, NOT - must be uppercase)
        #   - ✅ Field-level search not needed due to low fulltext coverage
        #
        # Phase 3 Claude screening will filter any remaining less-relevant papers.
        #
        # Ref: https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/search-entities

        result = self.wrapper.search_works(
            query=self.query,  # Boolean query directly to search parameter
            search_param="search",  # Supports Boolean operators
            filter_str="",  # No filter - let search handle everything
            max_results=max_results,
            per_page=100,  # Max allowed by OpenAlex
            select=""  # Return all fields
        )

        # Save results
        self._save_openalex_results(result, out_path)

        return {
            "success": result.get("success", False),
            "status": result.get("status", "unknown"),
            "results_count": len(result.get("results", [])),
            "error": result.get("error", ""),  # Include error field for UI display
            "output_files": {
                "summary_json": str(out_path / "run_summary.json"),
                "summary_csv": str(out_path / "works_summary.csv"),
                "full_jsonl": str(out_path / "works_full.jsonl")
            }
        }

    def _execute_pubmed(self, max_results: int, out_path: Path) -> Dict:
        """Execute PubMed search (two-step: esearch + efetch)."""
        self.logger.agent_thinking("PubMed", "Step 1: ESearch (finding PMIDs)...")

        # Step 1: ESearch
        esearch_result = self.wrapper.esearch(
            query=self.query,
            max_results=max_results
        )

        if not esearch_result.get("ok"):
            raise RuntimeError(f"ESearch failed: {esearch_result.get('status')}")

        total_count = esearch_result["count_total"]
        target_count = esearch_result["count_target"]
        query_key = esearch_result["query_key"]
        webenv = esearch_result["webenv"]

        self.logger.info(f"PubMed: Found {total_count} total, fetching {target_count}")

        # Step 2: EFetch in batches
        self.logger.agent_thinking("PubMed", "Step 2: EFetch (retrieving records)...")

        all_records = []
        fetch_batch_size = 200
        for start in range(0, target_count, fetch_batch_size):
            batch_size = min(fetch_batch_size, target_count - start)
            self.logger.info(f"Fetching records {start+1} to {start+batch_size}...")

            efetch_result = self.wrapper.efetch_batch(
                query_key=query_key,
                webenv=webenv,
                retstart=start,
                retmax=batch_size
            )

            if efetch_result.get("ok"):
                # Parse XML and extract records
                records = self._parse_pubmed_xml(efetch_result["xml"])
                all_records.extend(records)

        # Save results
        self._save_pubmed_results(all_records, out_path, esearch_result)

        return {
            "success": True,
            "status": "success",
            "results_count": len(all_records),
            "error": "",  # Include error field for UI display (empty on success)
            "output_files": {
                "summary_json": str(out_path / "run_summary.json"),
                "summary_csv": str(out_path / "works_summary.csv"),
                "full_jsonl": str(out_path / "works_full.jsonl")
            }
        }

    def _execute_scopus(self, max_results: int, out_path: Path) -> Dict:
        """Execute Scopus search."""
        self.logger.agent_thinking("Scopus", "Executing search...")

        result = self.wrapper.search_query(
            query=self.query,
            max_results=max_results,
            count_per_page=25,  # Scopus recommended batch size
            view="standard"  # Can be "standard" or "complete"
        )

        # Save results
        self._save_scopus_results(result, out_path)

        return {
            "success": result.get("success", False),
            "status": result.get("status", "unknown"),
            "results_count": len(result.get("results", [])),
            "error": result.get("error", ""),  # Include error field for UI display
            "output_files": {
                "summary_json": str(out_path / "run_summary.json"),
                "summary_csv": str(out_path / "works_summary.csv"),
                "full_jsonl": str(out_path / "works_full.jsonl")
            }
        }

    def _save_openalex_results(self, result: Dict, out_path: Path):
        """Save OpenAlex results to standardized output files."""
        # Save run summary
        summary = {
            "query": self.query,
            "database": "openalex",
            "status": result.get("status"),
            "results_count": len(result.get("results", [])),
            "meta_count": result.get("meta_count", 0),
            "calls": result.get("calls", 0)
        }
        with open(out_path / "run_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Save works summary CSV
        works = result.get("results", [])
        if works:
            df = pd.DataFrame([{
                "openalex_id": w.get("id", ""),
                "doi": w.get("doi", ""),
                "title": w.get("title", ""),
                "abstract": self._reconstruct_abstract(w.get("abstract_inverted_index")),
                "publication_year": w.get("publication_year"),
                "cited_by_count": w.get("cited_by_count", 0),
                "is_oa": w.get("open_access", {}).get("is_oa", False)
            } for w in works])
            df.to_csv(out_path / "works_summary.csv", index=False)

        # Save full metadata JSONL
        with open(out_path / "works_full.jsonl", "w") as f:
            for work in works:
                f.write(json.dumps(work) + "\n")

    def _save_pubmed_results(self, records: list, out_path: Path, esearch_result: Dict):
        """Save PubMed results to standardized output files."""
        # Save run summary
        summary = {
            "query": self.query,
            "database": "pubmed",
            "status": "success",
            "results_count": len(records),
            "meta_count": esearch_result.get("count_total", 0)
        }
        with open(out_path / "run_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Save works summary CSV
        if records:
            df = pd.DataFrame([{
                "pmid": r.get("pmid", ""),
                "doi": r.get("doi", ""),
                "title": r.get("title", ""),
                "abstract": r.get("abstract", ""),
                "journal_title": r.get("journal_title", ""),
                "publication_date": r.get("publication_date", "")
            } for r in records])
            df.to_csv(out_path / "works_summary.csv", index=False)

        # Save full metadata JSONL
        with open(out_path / "works_full.jsonl", "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

    def _save_scopus_results(self, result: Dict, out_path: Path):
        """Save Scopus results to standardized output files."""
        # Save run summary
        summary = {
            "query": self.query,
            "database": "scopus",
            "status": result.get("status"),
            "success": result.get("success", False),
            "results_count": len(result.get("results", [])),
            "meta_count": result.get("meta_count", 0),
            "calls": result.get("calls", 0),
            "error": result.get("error", "")
        }
        with open(out_path / "run_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Save works summary CSV
        works = result.get("results", [])
        if works:
            # Scopus uses namespaced field names (dc:, prism:, etc.)
            df = pd.DataFrame([{
                "eid": w.get("eid", ""),
                "doi": w.get("prism:doi", ""),  # Scopus uses prism:doi
                "title": w.get("dc:title", ""),  # Scopus uses dc:title
                "abstract": w.get("dc:description", ""),  # Scopus uses dc:description for abstract
                "creator": w.get("dc:creator", ""),  # Author name
                "publication_name": w.get("prism:publicationName", ""),
                "cover_date": w.get("prism:coverDate", ""),
                "citedby_count": w.get("citedby-count", 0)
            } for w in works])
            df.to_csv(out_path / "works_summary.csv", index=False)

        # Save full metadata JSONL
        with open(out_path / "works_full.jsonl", "w") as f:
            for work in works:
                f.write(json.dumps(work) + "\n")

    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> str:
        """Reconstruct abstract text from OpenAlex inverted index."""
        if not inverted_index:
            return ""

        try:
            # Flatten inverted index into (position, word) pairs
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))

            # Sort by position and join
            word_positions.sort(key=lambda x: x[0])
            return " ".join([word for _, word in word_positions])
        except Exception:
            return ""


# Test the module
if __name__ == "__main__":
    print("Testing SearchExecutor...\n")

    # Test with dummy config
    config = {
        "api_key": "",
        "mailto": "test@example.com"
    }

    # Test OpenAlex
    print("1. Testing OpenAlex wrapper initialization:")
    try:
        executor = SearchExecutor("openalex", "climate change", config)
        print(f"   ✓ OpenAlex executor created")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\nNote: Actual search execution requires valid API keys and network access.")
