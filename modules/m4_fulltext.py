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

    def __init__(self, config: dict, api_credentials: Optional[dict] = None):
        """
        Initialize full-text retriever.

        Args:
            config: Dictionary with keys:
                - out_dir: Output directory path
                - convert_to_md: bool (always convert to markdown)
                - use_playwright: bool (enable browser fallback)
                - max_retries: int (retry count for failed downloads)
                - timeout: int (timeout in seconds)
            api_credentials: Optional dictionary with API keys:
                - openalex_api_key: str
                - openalex_mailto: str
                - elsevier_api_key: str
                - elsevier_inst_token: str
                - wiley_tdm_token: str
        """
        self.config = config
        self.api_credentials = api_credentials or {}
        self.logger = get_logger()
        self._validate_credentials()

    def _validate_credentials(self):
        """Validate API credentials."""
        recommended_creds = {
            'openalex_mailto': 'OpenAlex polite pool (recommended)',
            'elsevier_api_key': 'Elsevier full-text',
            'wiley_tdm_token': 'Wiley TDM service'
        }

        for cred, purpose in recommended_creds.items():
            if not self.api_credentials.get(cred):
                self.logger.warning(f"{cred} not provided - {purpose} may be unavailable")

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
            sys.executable,
            str(wrapper_path),
            "--doi-file", doi_file,
            "--out-dir", self.config['out_dir'],
            "--max-retries", str(self.config['max_retries']),
            "--timeout", str(self.config['timeout'])
        ]

        # Optional flags — only add those the wrapper actually supports
        if self.config.get('convert_to_md') and not self.config.get('openalex_only'):
            cmd.append("--convert-to-md")
        if self.config.get('use_playwright') and not self.config.get('openalex_only'):
            cmd.append("--use-playwright-fallback")

        self.logger.info(f"  Running command: {' '.join(cmd)}")

        # Prepare environment with API credentials.
        # In openalex_only mode, omit publisher keys so the wrapper naturally
        # skips Elsevier/Wiley (it checks for missing keys internally).
        env = os.environ.copy()
        # Always clear publisher keys from inherited env first
        for _k in ('ELSEVIER_API_KEY', 'ELSEVIER_INST_TOKEN', 'WILEY_TDM_CLIENT_TOKEN'):
            env.pop(_k, None)

        if self.api_credentials.get('openalex_api_key'):
            env['OPENALEX_API_KEY'] = self.api_credentials['openalex_api_key']
        if self.api_credentials.get('openalex_mailto'):
            env['OPENALEX_MAILTO'] = self.api_credentials['openalex_mailto']

        if not self.config.get('openalex_only'):
            if self.api_credentials.get('elsevier_api_key'):
                env['ELSEVIER_API_KEY'] = self.api_credentials['elsevier_api_key']
            if self.api_credentials.get('elsevier_inst_token'):
                env['ELSEVIER_INST_TOKEN'] = self.api_credentials['elsevier_inst_token']
            if self.api_credentials.get('wiley_tdm_token'):
                env['WILEY_TDM_CLIENT_TOKEN'] = self.api_credentials['wiley_tdm_token']

        try:
            # Run subprocess with API credentials in environment
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
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
                # Include first meaningful stderr line to surface argparse/import errors
                _stderr_hint = next(
                    (l.strip() for l in result.stderr.splitlines() if l.strip()),
                    ""
                )
                self.logger.error(f"Fulltext chain failed with return code {result.returncode}: {_stderr_hint}")
                return {
                    "success": 0,
                    "total": len(doi_list),
                    "status": "error",
                    "message": f"Subprocess failed (code {result.returncode}): {_stderr_hint}"
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
