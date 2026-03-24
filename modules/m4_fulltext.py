"""
Phase 4: Full-Text Retrieval Module
Integrates fulltext chain wrapper for multi-source PDF/XML retrieval.
"""

import os
import sys
import json
import subprocess
import tempfile
import pandas as pd
from pathlib import Path
from typing import List, Optional
from utils.logger import get_logger


class FullTextRetriever:
    """
    Orchestrates full-text retrieval workflow:
    1. Extract DOIs from Phase 3 approved papers
    2. Run fulltext chain (OpenAlex → Publishers → Playwright)
    3. Parse and return results
    """

    def __init__(self, config: dict):
        """
        Initialize full-text retriever.

        Args:
            config: Dictionary with keys:
                - out_dir: Output directory path
                - convert_to_md: bool (always convert to markdown)
                - use_playwright: bool (enable browser fallback)
                - max_retries: int (retry count for failed downloads)
                - timeout: int (timeout in seconds)
        """
        self.config = config
        self.logger = get_logger()
        self._validate_env()

    def _validate_env(self):
        """Validate environment variables for API access."""
        recommended_vars = {
            'OPENALEX_API_KEY': 'OpenAlex content API',
            'OPENALEX_MAILTO': 'OpenAlex polite pool',
            'ELSEVIER_API_KEY': 'Elsevier full-text',
            'WILEY_TDM_CLIENT_TOKEN': 'Wiley TDM service'
        }

        for var, purpose in recommended_vars.items():
            if not os.environ.get(var):
                self.logger.warning(f"{var} not set - {purpose} may be unavailable")

    def prepare_doi_list(self, screening_df: pd.DataFrame) -> List[str]:
        """
        Extract DOIs from approved papers (judgement=True).

        Args:
            screening_df: DataFrame from Phase 3 screening results

        Returns:
            List of DOIs to retrieve
        """
        self.logger.info("Preparing DOI list from Phase 3 results...")

        # Filter to included papers only
        if 'judgement' not in screening_df.columns:
            raise ValueError("Screening results missing 'judgement' column")

        included = screening_df[screening_df['judgement'] == True]
        self.logger.info(f"  Found {len(included)} papers with judgement=True")

        # Extract DOIs
        if 'doi' not in included.columns:
            raise ValueError("Screening results missing 'doi' column")

        dois = included['doi'].dropna().unique().tolist()
        self.logger.info(f"  Extracted {len(dois)} unique DOIs")

        if len(dois) == 0:
            self.logger.warning("⚠️ No DOIs found in approved papers!")

        return dois

    def run_fulltext_chain(self, doi_list: List[str]) -> dict:
        """
        Run fulltext chain wrapper as subprocess.

        Args:
            doi_list: List of DOIs to retrieve

        Returns:
            Summary dict with success counts and file paths
        """
        if len(doi_list) == 0:
            return {
                "success": 0,
                "total": 0,
                "status": "no_dois",
                "message": "No DOIs provided for retrieval"
            }

        self.logger.info(f"Starting full-text retrieval for {len(doi_list)} DOIs...")

        # Write DOIs to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            doi_file = f.name
            f.write("\n".join(doi_list))
        self.logger.info(f"  Wrote DOIs to: {doi_file}")

        # Build command
        wrapper_path = Path(__file__).parent.parent / "Search and full-text packages" / "fulltext-packages" / "fulltext_chain_wrapper.py"
        if not wrapper_path.exists():
            raise FileNotFoundError(f"Fulltext chain wrapper not found at: {wrapper_path}")

        cmd = [
            sys.executable,  # Use current Python interpreter
            str(wrapper_path),
            "--doi-file", doi_file,
            "--out-dir", self.config['out_dir'],
            "--max-retries", str(self.config['max_retries']),
            "--timeout", str(self.config['timeout'])
        ]

        # Add optional flags
        if self.config['convert_to_md']:
            cmd.append("--convert-to-md")
        if self.config['use_playwright']:
            cmd.append("--use-playwright-fallback")

        self.logger.info(f"  Running command: {' '.join(cmd)}")

        try:
            # Run subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config['timeout'] * len(doi_list)  # Scale timeout by number of DOIs
            )

            # Log output
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.logger.info(f"  [fulltext-chain] {line}")

            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.logger.warning(f"  [fulltext-chain] {line}")

            if result.returncode != 0:
                self.logger.error(f"Fulltext chain failed with return code {result.returncode}")
                return {
                    "success": 0,
                    "total": len(doi_list),
                    "status": "error",
                    "message": f"Subprocess failed with code {result.returncode}"
                }

            # Parse results
            return self._parse_run_summary()

        except subprocess.TimeoutExpired:
            self.logger.error("Fulltext chain timed out")
            return {
                "success": 0,
                "total": len(doi_list),
                "status": "timeout",
                "message": "Subprocess timed out"
            }
        except Exception as e:
            self.logger.error(f"Fulltext chain failed: {e}", exc_info=True)
            return {
                "success": 0,
                "total": len(doi_list),
                "status": "error",
                "message": str(e)
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(doi_file)
            except:
                pass

    def _parse_run_summary(self) -> dict:
        """Parse run_summary.json from output directory."""
        summary_path = Path(self.config['out_dir']) / "run_summary.json"

        if not summary_path.exists():
            self.logger.warning("run_summary.json not found - using default summary")
            return {
                "success": 0,
                "total": 0,
                "status": "missing_summary",
                "message": "run_summary.json not found"
            }

        try:
            with open(summary_path, 'r') as f:
                summary = json.load(f)
            self.logger.info(f"✅ Parsed run summary from: {summary_path}")
            return summary
        except Exception as e:
            self.logger.error(f"Failed to parse run_summary.json: {e}")
            return {
                "success": 0,
                "total": 0,
                "status": "parse_error",
                "message": str(e)
            }

    def parse_results(self, out_dir: str) -> pd.DataFrame:
        """
        Parse results.csv from output directory.

        Args:
            out_dir: Output directory path

        Returns:
            DataFrame with retrieval results
        """
        results_path = Path(out_dir) / "results.csv"

        if not results_path.exists():
            self.logger.warning("results.csv not found - returning empty DataFrame")
            return pd.DataFrame()

        try:
            df = pd.read_csv(results_path)
            self.logger.info(f"✅ Loaded {len(df)} results from: {results_path}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to parse results.csv: {e}")
            return pd.DataFrame()
