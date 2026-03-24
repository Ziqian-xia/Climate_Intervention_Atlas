"""
Phase 3: Abstract Screening Module
Uses Claude for AI-assisted abstract screening with HITL review.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from utils.logger import get_logger


class ScreeningOrchestrator:
    """
    Orchestrates abstract screening workflow:
    1. Consolidate Phase 2 results from multiple databases
    2. Run Claude-based screening with user-defined criteria
    3. Save results with summary statistics
    """

    def __init__(self, config: dict):
        """
        Initialize screening orchestrator.

        Args:
            config: Dictionary with keys:
                - mode: "simple" or "detailed"
                - llm_provider: LLM provider instance (BedrockProvider, AnthropicProvider, or DummyProvider)
                - thread_count: int (default 4)
        """
        self.config = config
        self.logger = get_logger()
        self.llm_provider = config.get('llm_provider')

        if not self.llm_provider:
            raise ValueError("llm_provider is required in config")

    def consolidate_phase2_results(self, search_results_dir: str) -> pd.DataFrame:
        """
        Load and deduplicate results from Phase 2 database searches.

        Args:
            search_results_dir: Directory containing Phase 2 output subdirectories

        Returns:
            Consolidated DataFrame with unique records
        """
        results_path = Path(search_results_dir)
        if not results_path.exists():
            raise ValueError(f"Search results directory not found: {search_results_dir}")

        self.logger.info(f"Loading Phase 2 results from: {search_results_dir}")

        # Find all database result CSVs in subdirectories
        dfs = []
        for db in ['openalex', 'pubmed', 'scopus']:
            # Check subdirectory structure (new format)
            csv_path = results_path / db / "works_summary.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                dfs.append(df)
                self.logger.info(f"  Loaded {len(df)} records from {db}/works_summary.csv")
            else:
                # Fallback: check flat file structure (old format)
                csv_path = results_path / f"{db}_results.csv"
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    dfs.append(df)
                    self.logger.info(f"  Loaded {len(df)} records from {db}_results.csv")

        if not dfs:
            raise ValueError(f"No Phase 2 results found in {search_results_dir}. Expected 'works_summary.csv' in subdirectories or '<db>_results.csv' files.")

        # Combine all dataframes
        combined = pd.concat(dfs, ignore_index=True)
        self.logger.info(f"Combined {len(combined)} total records")

        # Deduplicate by DOI (case-insensitive)
        if 'doi' in combined.columns:
            combined['doi_normalized'] = combined['doi'].str.lower()
            before_dedup = len(combined)
            combined = combined.drop_duplicates(subset='doi_normalized', keep='first')
            after_dedup = len(combined)
            self.logger.info(f"Deduplicated by DOI: {before_dedup} → {after_dedup} records (removed {before_dedup - after_dedup} duplicates)")
            # Remove temporary column
            combined = combined.drop(columns=['doi_normalized'])
        else:
            self.logger.warning("No 'doi' column found - skipping deduplication")

        # Ensure required columns exist
        if 'title' not in combined.columns:
            self.logger.warning("No 'title' column found - adding empty column")
            combined['title'] = ""
        if 'abstract' not in combined.columns:
            self.logger.warning("No 'abstract' column found - adding empty column")
            combined['abstract'] = ""

        # Fill missing values with empty strings
        combined['title'] = combined['title'].fillna("")
        combined['abstract'] = combined['abstract'].fillna("")

        self.logger.info(f"✅ Consolidated {len(combined)} unique records ready for screening")
        return combined

    def _screen_single_paper(self, row: dict, criteria: str, mode: str) -> dict:
        """
        Screen a single paper using Claude.

        Args:
            row: Dictionary with 'title' and 'abstract' keys
            criteria: Inclusion/exclusion criteria
            mode: "simple" or "detailed"

        Returns:
            Dictionary with screening results
        """
        title = row.get('title', '')
        abstract = row.get('abstract', '')

        # Skip if both title and abstract are empty
        if not title.strip() and not abstract.strip():
            return {
                **row,
                'judgement': False,
                'reason': 'No title or abstract available',
                'confidence': 0,
                'error': ''
            }

        # Build prompt based on mode
        if mode == "simple":
            system_prompt = """You are an expert systematic review screener. Evaluate whether research papers should be included based on the given criteria.

Respond with a JSON object containing:
- "include": boolean (true/false)
- "reason": string (brief 1-2 sentence justification)
- "confidence": number (0-100, your confidence in this decision)

Be strict and precise. Only include papers that clearly meet ALL inclusion criteria."""

            user_message = f"""**Screening Criteria:**
{criteria}

**Paper to Evaluate:**
Title: {title}

Abstract: {abstract}

Should this paper be INCLUDED in the systematic review? Respond with JSON only."""

        else:  # detailed mode
            system_prompt = """You are an expert systematic review screener. Evaluate research papers through careful reasoning.

First, analyze the paper against each criterion. Then make a final decision.

Respond with a JSON object containing:
- "reasoning": string (step-by-step analysis of how the paper matches/fails each criterion)
- "include": boolean (true/false)
- "reason": string (concise summary of decision)
- "confidence": number (0-100, your confidence in this decision)

Be thorough in your reasoning but concise in your final summary."""

            user_message = f"""**Screening Criteria:**
{criteria}

**Paper to Evaluate:**
Title: {title}

Abstract: {abstract}

Analyze this paper carefully and decide if it should be INCLUDED. Respond with JSON only."""

        try:
            # Call Claude
            response = self.llm_provider.call_model(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=1000,
                temperature=0.0  # Deterministic for consistency
            )

            # Parse JSON response
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.strip()
            if response_text.startswith('```'):
                # Remove markdown code block markers
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()

            result = json.loads(response_text)

            return {
                **row,
                'judgement': result.get('include', False),
                'reason': result.get('reason', ''),
                'confidence': result.get('confidence', 0),
                'reasoning': result.get('reasoning', '') if mode == 'detailed' else '',
                'error': ''
            }

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON for paper: {title[:50]}... Error: {e}")
            return {
                **row,
                'judgement': False,
                'reason': f'JSON parsing error: {str(e)}',
                'confidence': 0,
                'error': f'JSON parse error: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"Error screening paper: {title[:50]}... Error: {e}")
            return {
                **row,
                'judgement': False,
                'reason': f'Screening error: {str(e)}',
                'confidence': 0,
                'error': str(e)
            }

    def run_screening(self, df: pd.DataFrame, criteria: str) -> pd.DataFrame:
        """
        Run Claude-based screening on consolidated abstracts.

        Args:
            df: DataFrame with 'title' and 'abstract' columns
            criteria: Inclusion/exclusion criteria text

        Returns:
            DataFrame with screening results (judgement, reason, confidence, error)
        """
        mode = self.config.get('mode', 'simple')
        thread_count = self.config.get('thread_count', 4)

        self.logger.info(f"Starting Claude screening with {mode} mode...")
        self.logger.info(f"  Records to screen: {len(df)}")
        self.logger.info(f"  Threads: {thread_count}")

        # Convert dataframe rows to list of dicts
        papers = df.to_dict('records')
        results = []

        # Process papers in parallel with progress bar
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = {
                executor.submit(self._screen_single_paper, paper, criteria, mode): paper
                for paper in papers
            }

            with tqdm(total=len(papers), desc="Screening papers") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    pbar.update(1)

        # Convert results to DataFrame
        result_df = pd.DataFrame(results)

        # Count results
        included = len(result_df[result_df['judgement'] == True])
        excluded = len(result_df[result_df['judgement'] == False])
        errors = len(result_df[result_df['error'] != ""])

        self.logger.info(f"✅ Screening complete!")
        self.logger.info(f"  Included: {included}")
        self.logger.info(f"  Excluded: {excluded}")
        self.logger.info(f"  Errors: {errors}")

        return result_df

    def save_results(self, df: pd.DataFrame, output_dir: str):
        """
        Save screening results and summary statistics.

        Args:
            df: Screening results DataFrame
            output_dir: Output directory path
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # Save full results
        csv_path = out_path / "screening_results.csv"
        df.to_csv(csv_path, index=False)
        self.logger.info(f"Saved screening results: {csv_path}")

        # Calculate summary statistics
        summary = {
            'total_papers': len(df),
            'included': int(df['judgement'].sum()),
            'excluded': int((~df['judgement']).sum()),
            'errors': int((df['error'] != "").sum()),
            'avg_confidence': float(df['confidence'].mean()) if 'confidence' in df.columns else 0,
            'low_confidence_count': int((df['confidence'] < 70).sum()) if 'confidence' in df.columns else 0,
            'mode': self.config.get('mode', 'simple')
        }

        # Save summary
        summary_path = out_path / "screening_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        self.logger.info(f"Saved summary: {summary_path}")

        # Save included papers only
        included_df = df[df['judgement'] == True]
        if len(included_df) > 0:
            included_path = out_path / "included_papers.csv"
            included_df.to_csv(included_path, index=False)
            self.logger.info(f"Saved {len(included_df)} included papers: {included_path}")

        self.logger.info("✅ All screening results saved successfully")
