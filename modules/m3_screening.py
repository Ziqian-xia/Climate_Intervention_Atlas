"""
Phase 3: Abstract Screening Module (Claude-based)

Replaces OpenAI-based LLMscreen with Claude API for abstract screening.
Maintains compatible interface for integration with Streamlit app.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from tqdm import tqdm
from utils.llm_providers import LLMProvider
from utils.logger import get_logger


class ClaudeScreener:
    """Abstract screening using Claude API (replaces OpenAI LLMscreen)."""

    # Stable output columns (matching LLMscreen contract)
    OUTPUT_COLUMNS = [
        "record_id",
        "mode",
        "judgement",
        "reason",
        "title",
        "abstract",
        "raw_response",
        "reasoning",
        "model",
        "error"
    ]

    def __init__(self, llm_provider: LLMProvider, config: Optional[Dict] = None):
        """
        Initialize Claude-based screener.

        Args:
            llm_provider: LLM provider instance (Bedrock/Anthropic)
            config: Optional config dict with:
                - mode: "simple" or "zeroshot" (default: "simple")
                - k_strictness: float in [0,1] for simple mode (default: 0.5)
                - thread_count: number of workers (default: 8)
                - max_tokens: max response tokens (default: 1000)
        """
        self.provider = llm_provider
        self.logger = get_logger()

        # Set defaults
        self.config = config or {}
        self.mode = self.config.get("mode", "simple")
        self.k_strictness = self.config.get("k_strictness", 0.5)
        self.thread_count = self.config.get("thread_count", 8)
        self.max_tokens = self.config.get("max_tokens", 1000)

    def _build_simple_prompt(self, title: str, abstract: str, criteria: str) -> tuple:
        """Build simple mode prompt (single-pass JSON decision)."""
        system_prompt = f"""You are an academic reviewer for systematic reviews.
Screen studies based on title and abstract.

Current inclusion strictness: k={self.k_strictness:.1f}
(k is in [0,1], where 0 = least strict, 1 = most strict)

Filter criteria:
{criteria}

Output a JSON object with:
- "judgement": boolean (true to include, false to exclude)
- "reason": brief explanation in English (max 150 words)

Output only valid JSON, no other text."""

        user_message = f"""Title: {title}

Abstract: {abstract}

Decision:"""

        return system_prompt, user_message

    def _build_zeroshot_reasoning_prompt(self, title: str, abstract: str, criteria: str) -> tuple:
        """Build zeroshot reasoning prompt (step 1: analysis)."""
        system_prompt = """You are an academic assistant evaluating studies for systematic reviews.
Write analysis in English only."""

        user_message = f"""Title: {title}

Abstract: {abstract}

Filter criteria:
{criteria}

Think in three steps:
1. Reasons to INCLUDE this study
2. Reasons to EXCLUDE this study
3. Final balanced conclusion

Provide detailed analysis (200-300 words):"""

        return system_prompt, user_message

    def _build_zeroshot_decision_prompt(self, title: str, abstract: str, criteria: str, reasoning: str) -> tuple:
        """Build zeroshot decision prompt (step 2: final judgement)."""
        system_prompt = f"""You are an academic reviewer for systematic reviews.
Screen studies based on title and abstract.

Filter criteria:
{criteria}

Based on the analysis provided, make a final decision.
Output a JSON object with:
- "judgement": boolean (true to include, false to exclude)
- "reason": brief summary of decision rationale (max 100 words)

Output only valid JSON, no other text."""

        user_message = f"""Title: {title}

Abstract: {abstract}

Previous analysis:
{reasoning}

Final decision:"""

        return system_prompt, user_message

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON response, handling common edge cases."""
        # Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            try:
                return json.loads(response[start:end].strip())
            except json.JSONDecodeError:
                pass
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            try:
                return json.loads(response[start:end].strip())
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass

        # Fallback: return error
        return {
            "judgement": False,
            "reason": "Failed to parse response",
            "error": f"Invalid JSON: {response[:200]}"
        }

    def _screen_single_simple(self, record: Dict, criteria: str) -> Dict:
        """Screen single record in simple mode."""
        record_id = record.get("record_id", "unknown")
        title = record.get("title", "")
        abstract = record.get("abstract", "")

        result = {
            "record_id": record_id,
            "mode": "simple",
            "title": title,
            "abstract": abstract,
            "raw_response": "",
            "reasoning": "",
            "model": self.provider.get_model_name(),
            "error": ""
        }

        try:
            # Build prompt
            system_prompt, user_message = self._build_simple_prompt(title, abstract, criteria)

            # Call LLM
            response = self.provider.call_model(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=self.max_tokens
            )

            result["raw_response"] = response

            # Parse response
            parsed = self._parse_json_response(response)
            result["judgement"] = bool(parsed.get("judgement", False))
            result["reason"] = str(parsed.get("reason", ""))

            if "error" in parsed:
                result["error"] = parsed["error"]

        except Exception as e:
            self.logger.error(f"Screening failed for record {record_id}: {e}")
            result["judgement"] = False
            result["reason"] = ""
            result["error"] = str(e)

        return result

    def _screen_single_zeroshot(self, record: Dict, criteria: str) -> Dict:
        """Screen single record in zeroshot mode (two-step)."""
        record_id = record.get("record_id", "unknown")
        title = record.get("title", "")
        abstract = record.get("abstract", "")

        result = {
            "record_id": record_id,
            "mode": "zeroshot",
            "title": title,
            "abstract": abstract,
            "raw_response": "",
            "reasoning": "",
            "model": self.provider.get_model_name(),
            "error": ""
        }

        try:
            # Step 1: Generate reasoning
            system_prompt_1, user_message_1 = self._build_zeroshot_reasoning_prompt(
                title, abstract, criteria
            )

            reasoning = self.provider.call_model(
                system_prompt=system_prompt_1,
                user_message=user_message_1,
                max_tokens=self.max_tokens
            )

            result["reasoning"] = reasoning

            # Step 2: Make decision based on reasoning
            system_prompt_2, user_message_2 = self._build_zeroshot_decision_prompt(
                title, abstract, criteria, reasoning
            )

            response = self.provider.call_model(
                system_prompt=system_prompt_2,
                user_message=user_message_2,
                max_tokens=500
            )

            result["raw_response"] = response

            # Parse response
            parsed = self._parse_json_response(response)
            result["judgement"] = bool(parsed.get("judgement", False))
            result["reason"] = str(parsed.get("reason", ""))

            if "error" in parsed:
                result["error"] = parsed["error"]

        except Exception as e:
            self.logger.error(f"Screening failed for record {record_id}: {e}")
            result["judgement"] = False
            result["reason"] = ""
            result["error"] = str(e)

        return result

    def screen_records(self, records: List[Dict], criteria: str, progress_callback=None) -> pd.DataFrame:
        """
        Screen multiple records with threading.

        Args:
            records: List of dicts with 'title' and 'abstract' keys
            criteria: Inclusion/exclusion criteria
            progress_callback: Optional function(completed, total, included, excluded) for progress updates

        Returns:
            DataFrame with screening results
        """
        self.logger.info(f"Starting Claude screening: {len(records)} records, mode={self.mode}")

        results = []
        included_count = 0
        excluded_count = 0
        screen_func = self._screen_single_zeroshot if self.mode == "zeroshot" else self._screen_single_simple

        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            # Submit all tasks
            future_to_record = {
                executor.submit(screen_func, record, criteria): record
                for record in records
            }

            # Collect results with progress bar
            completed = 0
            for future in tqdm(
                as_completed(future_to_record),
                total=len(records),
                desc="Screening"
            ):
                try:
                    result = future.result()
                    results.append(result)

                    # Track statistics
                    if result.get("judgement"):
                        included_count += 1
                    else:
                        excluded_count += 1

                except Exception as e:
                    record = future_to_record[future]
                    self.logger.error(f"Task failed for record {record.get('record_id')}: {e}")
                    results.append({
                        "record_id": record.get("record_id", "unknown"),
                        "mode": self.mode,
                        "judgement": False,
                        "reason": "",
                        "title": record.get("title", ""),
                        "abstract": record.get("abstract", ""),
                        "raw_response": "",
                        "reasoning": "",
                        "model": self.provider.get_model_name(),
                        "error": str(e)
                    })
                    excluded_count += 1

                # Progress callback
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(records), included_count, excluded_count)

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Ensure column order
        for col in self.OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        # Log summary
        included = df["judgement"].sum()
        excluded = len(df) - included
        errors = (df["error"] != "").sum()

        self.logger.info(f"Screening complete: {included} included, {excluded} excluded, {errors} errors")

        return df[self.OUTPUT_COLUMNS]


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
                - mode: "simple" or "zeroshot" (default: "simple")
                - k_strictness: float in [0,1] (default: 0.5)
                - llm_provider: LLM provider instance (BedrockProvider, AnthropicProvider, or DummyProvider)
                - thread_count: int (default: 8)
        """
        self.config = config
        self.logger = get_logger()
        self.llm_provider = config.get('llm_provider')

        if not self.llm_provider:
            raise ValueError("llm_provider is required in config")

        # Initialize Claude screener
        self.screener = ClaudeScreener(self.llm_provider, config)

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

        # Fallback: check for imported_papers.csv (from file import portal)
        if not dfs:
            imported_csv = results_path / "imported_papers.csv"
            if imported_csv.exists():
                df = pd.read_csv(imported_csv)
                dfs.append(df)
                self.logger.info(f"  Loaded {len(df)} records from imported_papers.csv (imported data)")

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

    def run_screening(self, df: pd.DataFrame, criteria: str, progress_callback=None) -> pd.DataFrame:
        """
        Run Claude-based screening on consolidated abstracts using ClaudeScreener.

        Args:
            df: DataFrame with 'title' and 'abstract' columns (plus metadata)
            criteria: Inclusion/exclusion criteria text
            progress_callback: Optional function(completed, total, included, excluded) for progress updates

        Returns:
            DataFrame with screening results (judgement, reason, error, plus metadata)
        """
        self.logger.info(f"Starting screening with {self.screener.mode} mode...")
        self.logger.info(f"  Records to screen: {len(df)}")
        self.logger.info(f"  Threads: {self.screener.thread_count}")

        # Add record IDs
        df['record_id'] = range(1, len(df) + 1)

        # Convert to records for screening
        records = df.to_dict('records')

        # Run screening via ClaudeScreener
        results_df = self.screener.screen_records(records, criteria, progress_callback=progress_callback)

        # Merge back with original metadata (preserving all original columns)
        # Get metadata columns (exclude the ones that screening returns)
        metadata_cols = [col for col in df.columns
                        if col not in self.screener.OUTPUT_COLUMNS]

        if metadata_cols:
            metadata_df = df[['record_id'] + metadata_cols]
            results_df = results_df.merge(metadata_df, on='record_id', how='left')

        self.logger.info("✅ Screening complete")

        return results_df

    def _legacy_screen_single_paper(self, row: dict, criteria: str, mode: str) -> dict:
        """
        DEPRECATED: Legacy screening method (kept for compatibility).
        Use ClaudeScreener instead.
        """
        # This method is no longer used but kept for reference
        raise NotImplementedError("Use ClaudeScreener.screen_records() instead")


    def save_results(self, df: pd.DataFrame, output_dir: str):
        """
        Save screening results and summary statistics.

        Args:
            df: Screening results DataFrame (from ClaudeScreener)
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
            'mode': self.screener.mode,
            'model': self.screener.provider.get_model_name(),
            'k_strictness': self.screener.k_strictness,
            'timestamp': datetime.now().isoformat()
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
