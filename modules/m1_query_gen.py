"""
Phase 1: Multi-Agent Query Generation Team
Four sequential agents: Pulse → Formulator → Sentinel → Refiner
"""

import json
import os
import re
import time
from typing import Dict, List, Optional

from utils.logger import get_logger
from utils.llm_providers import LLMProvider


class QueryGenerationTeam:
    """
    Multi-agent team for generating database-specific Boolean search queries.

    Agents:
    1. Pulse: Keyword expansion and synonym generation
    2. Formulator: Database-specific Boolean query construction
    3. Sentinel: Quality control and validation
    4. Refiner: Final polish and issue resolution
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Initialize query generation team.

        Args:
            llm_provider: Optional LLM provider instance. If None, uses dummy mode.
        """
        self.logger = get_logger()
        self.provider = llm_provider

        if self.provider is None:
            self.logger.warning("No LLM provider specified. Using dummy mode.")
        elif not self.provider.is_available():
            self.logger.warning(f"LLM provider not available: {self.provider.get_model_name()}. Using dummy mode.")
        else:
            self.logger.info(f"LLM provider initialized: {self.provider.get_model_name()}")

    def _call_agent(
        self,
        agent_name: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        max_retries: int = 3
    ) -> str:
        """
        Call an agent with retry logic.

        Returns:
            Agent response text or fallback dummy data
        """
        if not self.provider or not self.provider.is_available():
            self.logger.warning(f"{agent_name}: Using dummy response (provider not available)")
            return self._get_dummy_response(agent_name, user_message)

        for attempt in range(max_retries):
            try:
                humorous_messages = [
                    "🤔 Pondering the mysteries of the universe (and your query)...",
                    "⚡ Channeling the power of Claude through the cloud...",
                    "🎯 Aiming for research query perfection...",
                    "🧠 Engaging neural networks (the artificial kind)...",
                    "📚 Consulting the ancient texts of systematic review methodology..."
                ]
                self.logger.agent_thinking(
                    agent_name,
                    humorous_messages[attempt % len(humorous_messages)]
                )

                response_text = self.provider.call_model(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    max_tokens=max_tokens
                )

                success_messages = [
                    "✨ Eureka! Response received!",
                    "🎉 Mission accomplished!",
                    "💡 Brilliant insights acquired!",
                    "🏆 Query crafting success!",
                    "🚀 Knowledge transmitted successfully!"
                ]
                self.logger.info(f"{agent_name}: {success_messages[attempt % len(success_messages)]}")
                return response_text

            except Exception as e:
                self.logger.error(f"{agent_name}: LLM error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"{agent_name}: All retries exhausted, using dummy response")
                    return self._get_dummy_response(agent_name, user_message)

        return self._get_dummy_response(agent_name, user_message)

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that may be wrapped in markdown code blocks.

        Args:
            text: Raw text that may contain JSON

        Returns:
            Extracted JSON string
        """
        # Try direct parsing first
        text = text.strip()
        if text.startswith('{') or text.startswith('['):
            return text

        # Try to extract from markdown code blocks
        # Pattern: ```json ... ``` or ``` ... ```
        json_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()

        # Try to find JSON object in text (between first { and last })
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        if matches:
            # Return the longest match (most likely the complete JSON)
            return max(matches, key=len)

        # Return original if no patterns match
        return text

    def _get_dummy_response(self, agent_name: str, user_message: str) -> str:
        """Generate high-quality dummy responses for testing without API."""
        if agent_name == "Pulse":
            return json.dumps({
                "pico": {
                    "population": ["general population", "vulnerable groups", "urban residents"],
                    "intervention": ["climate change", "global warming", "extreme weather", "heat waves"],
                    "comparison": [],
                    "outcome": ["mental health", "psychological distress", "anxiety", "depression", "PTSD", "well-being"]
                },
                "study_design": ["adaptation", "resilience", "coping mechanisms", "intervention"],
                "expanded_keywords": [
                    "climate change", "global warming", "climate crisis",
                    "extreme weather", "heat waves", "temperature extremes",
                    "mental health", "psychological distress", "anxiety",
                    "depression", "PTSD", "trauma", "well-being",
                    "adaptation", "resilience", "coping mechanisms",
                    "general population", "vulnerable groups", "urban residents"
                ],
                "pico_statement": "In general populations (P), what is the impact of climate change and extreme weather events (I) on mental health outcomes (O)?",
                "reasoning": "Applied PICO framework: Population identified as general/vulnerable populations, Intervention as climate exposures, Outcome as mental health indicators. No explicit comparison in this observational research question."
            }, indent=2)

        elif agent_name == "Formulator":
            return json.dumps({
                "elsevier_query": 'TITLE-ABS-KEY(("general population" OR "vulnerable groups") AND ("climate change" OR "global warming" OR "extreme weather" OR "heat wave*") AND ("mental health" OR "psychological distress" OR "anxiety" OR "depression") AND (adapt* OR resilien* OR coping))',
                "pubmed_query": '(("climate change"[Title/Abstract] OR "global warming"[Title/Abstract] OR "extreme weather"[Title/Abstract] OR "heat wave"[Title/Abstract]) AND ("mental health"[Title/Abstract] OR "psychological distress"[Title/Abstract] OR "anxiety"[Title/Abstract]) AND ("general population"[Title/Abstract] OR "vulnerable groups"[Title/Abstract]))',
                "openalex_query": '"climate change" "mental health" adaptation population',
                "pico_structure": {
                    "population": "general population, vulnerable groups, urban residents",
                    "intervention": "climate change, global warming, extreme weather, heat waves",
                    "comparison": "Not applicable",
                    "outcome": "mental health, psychological distress, anxiety, depression, PTSD"
                },
                "reasoning": "Created PICO-structured queries with (P) AND (I) AND (O) format. Used OR within each PICO block for synonyms and AND to connect blocks. Included adaptation/resilience terms as methodological context."
            }, indent=2)

        elif agent_name == "Sentinel":
            return json.dumps({
                "elsevier_query": 'TITLE-ABS-KEY((("general population" OR "vulnerable groups" OR "urban residents") AND ("climate change" OR "global warming" OR "extreme weather" OR "heat wave*") AND ("mental health" OR "psychological distress" OR "anxiety" OR "depression" OR "PTSD") AND (adapt* OR resilien* OR intervention)))',
                "pubmed_query": '((("general population"[Title/Abstract] OR "vulnerable groups"[Title/Abstract] OR "urban residents"[Title/Abstract]) AND ("climate change"[Title/Abstract] OR "global warming"[Title/Abstract] OR "extreme weather"[Title/Abstract] OR "heat wave"[Title/Abstract]) AND ("mental health"[Title/Abstract] OR "psychological distress"[Title/Abstract] OR "anxiety"[Title/Abstract] OR "depression"[Title/Abstract]) AND (adapt*[Title/Abstract] OR resilien*[Title/Abstract])))',
                "openalex_query": '"general population" OR "vulnerable groups" AND "climate change" OR "extreme weather" AND "mental health" OR "psychological distress" AND adaptation OR resilience',
                "validation_notes": "✅ PICO structure validated: (P) AND (I) AND (O). ✅ Syntax validated. ✅ Parentheses balanced. ✅ Field restrictions applied. ✅ Wildcard operators properly used. Queries are ready for execution.",
                "warnings": []
            }, indent=2)

        elif agent_name == "Refiner":
            # Refiner returns same queries as Sentinel with refinement notes
            return json.dumps({
                "elsevier_query": 'TITLE-ABS-KEY((("general population" OR "vulnerable groups" OR "urban residents") AND ("climate change" OR "global warming" OR "extreme weather" OR "heat wave*") AND ("mental health" OR "psychological distress" OR "anxiety" OR "depression" OR "PTSD") AND (adapt* OR resilien* OR intervention)))',
                "pubmed_query": '((("general population"[Title/Abstract] OR "vulnerable groups"[Title/Abstract] OR "urban residents"[Title/Abstract]) AND ("climate change"[Title/Abstract] OR "global warming"[Title/Abstract] OR "extreme weather"[Title/Abstract] OR "heat wave"[Title/Abstract]) AND ("mental health"[Title/Abstract] OR "psychological distress"[Title/Abstract] OR "anxiety"[Title/Abstract] OR "depression"[Title/Abstract]) AND (adapt*[Title/Abstract] OR resilien*[Title/Abstract])))',
                "openalex_query": '"general population" OR "vulnerable groups" AND "climate change" OR "extreme weather" AND "mental health" OR "psychological distress" AND adaptation OR resilience',
                "refinement_notes": "✅ Final polish applied. PICO structure maintained with optimal Boolean logic. All queries validated and ready for execution.",
                "issues_resolved": []
            }, indent=2)

        return json.dumps({"error": "Unknown agent"})

    def _agent_pulse(self, topic: str, variation_seed: Optional[int] = None) -> Dict:
        """
        Agent 1: Pulse - Keyword Expansion using PICO Framework
        Expands research topic with synonyms, related terms, and domain vocabulary.
        Uses PICO framework for structured keyword generation.
        """
        self.logger.info("=" * 60)
        self.logger.info("PULSE AGENT - PICO-Based Keyword Expansion")
        self.logger.info("=" * 60)
        self.logger.agent_thinking("Pulse", "🔍 Applying PICO framework to structure your research question...")

        system_prompt = """You are Pulse, an expert research librarian specializing in systematic literature reviews using evidence-based frameworks.

Your role is to analyze research topics using the **PICO Framework** and expand them into comprehensive keyword sets.

**PICO FRAMEWORK** (from UNC Health Sciences Library):

**P - Population/Patient/Problem**:
- Who is the study about? (demographics, conditions, settings)
- What problem is being addressed?
- Examples: elderly, urban residents, vulnerable populations, heat-exposed workers

**I - Intervention/Exposure**:
- What is being done or what exposure is being studied?
- Examples: cooling centers, early warning systems, climate adaptation programs, heat waves

**C - Comparison/Control** (if applicable):
- What is the alternative or comparison?
- Examples: no intervention, standard care, pre-intervention period, control group
- Note: Not all studies have explicit comparisons

**O - Outcome**:
- What are you trying to accomplish, measure, or change?
- Examples: mortality, hospitalization, health outcomes, behavioral changes

**YOUR TASK**:

1. **Identify PICO elements** in the research topic
2. **Expand each PICO element** with:
   - Synonyms (British vs American spelling)
   - Related terms (hyponyms, hypernyms)
   - Domain-specific vocabulary (MeSH terms, technical jargon)
   - Truncation opportunities (e.g., "mortalit*" → mortality, mortalities)

3. **Add study design terms** (if relevant):
   - randomized, quasi-experimental, controlled, trial, evaluation
   - cohort, case-control, cross-sectional, longitudinal
   - impact, causal, effect, association

**EXAMPLE**:
Topic: "cooling centers and heat-related mortality"

PICO Analysis:
- P (Population): general population, elderly, urban residents
- I (Intervention): cooling center, cooling shelter, heat refuge, air-conditioned space
- C (Comparison): no intervention, areas without centers (implicit)
- O (Outcome): heat-related mortality, death, excess mortality, heat-related death

**SYSTEMATIC REVIEW BEST PRACTICES**:
- Balance sensitivity (recall) and precision
- Include methodological terms for study design
- Consider multiple disciplinary perspectives
- Aim for 20-35 keywords across all PICO elements

**CRITICAL**: Return ONLY valid JSON, no markdown formatting, no code blocks.

Return JSON:
{
    "pico": {
        "population": ["keyword1", "keyword2", ...],
        "intervention": ["keyword1", "keyword2", ...],
        "comparison": ["keyword1", "keyword2", ...],
        "outcome": ["keyword1", "keyword2", ...]
    },
    "study_design": ["keyword1", "keyword2", ...],
    "expanded_keywords": ["all_keywords_combined_in_flat_list"],
    "pico_statement": "Structured research question using PICO format",
    "reasoning": "Brief explanation of PICO identification and expansion strategy"
}

If comparison is not applicable, use empty array for "comparison"."""

        variation_instruction = ""
        if variation_seed:
            variation_instruction = f"""

VARIATION REQUEST (Seed #{variation_seed}):
Create an ALTERNATIVE keyword expansion that explores different angles or emphasizes different aspects of the topic.
- Variation 1: Emphasize primary intervention/exposure terms and direct outcomes
- Variation 2: Focus on methodological terms and study design vocabulary
- Variation 3: Expand with broader synonyms and related concepts
- Variation 4+: Mix approaches and explore different disciplinary perspectives

Be creative and comprehensive, but maintain systematic review rigor."""

        user_message = f"""Research topic: {topic}{variation_instruction}

Please expand this topic into a comprehensive keyword list for systematic literature review searching."""

        response_text = self._call_agent("Pulse", system_prompt, user_message)

        try:
            json_text = self._extract_json(response_text)
            result = json.loads(json_text)
            keyword_count = len(result.get('expanded_keywords', []))
            self.logger.agent_thinking("Pulse", f"🎨 Successfully expanded to {keyword_count} carefully curated keywords!")
            return result
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Pulse: Failed to parse JSON response: {e}")
            self.logger.error(f"Raw response: {response_text[:500]}...")
            return {
                "expanded_keywords": [topic],
                "reasoning": "Fallback: using original topic"
            }

    def _agent_formulator(self, pulse_result: Dict) -> Dict:
        """
        Agent 2: Formulator - PICO-Based Boolean Query Construction
        Creates database-specific Boolean search strings using PICO structure.
        """
        self.logger.info("=" * 60)
        self.logger.info("FORMULATOR AGENT - PICO-Structured Query Construction")
        self.logger.info("=" * 60)
        self.logger.agent_thinking("Formulator", "🧙 Building PICO-structured Boolean queries with precision...")

        system_prompt = """You are Formulator, an expert in database search syntax for systematic literature reviews using the PICO framework.

Your role is to construct rigorous Boolean search strings that leverage PICO structure for optimal sensitivity and specificity.

**DATABASE-SPECIFIC SYNTAX**:

1. **Elsevier/Scopus**:
   - Use TITLE-ABS-KEY() wrapper
   - Example: TITLE-ABS-KEY((P_terms) AND (I_terms) AND (O_terms))
   - Wildcards: * for truncation
   - Full example: TITLE-ABS-KEY(("elderly" OR "older adults") AND ("cooling center*" OR "heat refuge") AND (mortalit* OR death*))

2. **PubMed**:
   - Use [Title/Abstract] or [MeSH Terms] field tags
   - Example: (P_terms[Title/Abstract]) AND (I_terms[Title/Abstract]) AND (O_terms[Title/Abstract])
   - Consider MeSH for biomedical concepts
   - Full example: (("heat wave"[Title/Abstract] OR "extreme heat"[Title/Abstract]) AND ("cooling center"[Title/Abstract] OR "heat refuge"[Title/Abstract]))

3. **OpenAlex**:
   - Simpler syntax, quoted phrases and keywords
   - Example: "P_term" "I_term" "O_term"
   - OpenAlex handles field searching internally

**PICO-BASED QUERY CONSTRUCTION**:

**Structure**: (P) AND (I) AND (O)

- **P Block**: (population_term1 OR population_term2 OR ...)
- **I Block**: (intervention_term1 OR intervention_term2 OR ...)
- **C Block**: (comparison_term1 OR comparison_term2 OR ...) [Optional - include if applicable]
- **O Block**: (outcome_term1 OR outcome_term2 OR ...)
- **Study Design**: Optionally add AND (design_term1 OR design_term2) for methodological filtering

**Best Practices**:
- Group PICO elements with OR within each block
- Connect PICO blocks with AND
- Use quotes for phrases: "cooling center", "heat-related mortality"
- Use wildcards: mortalit* → mortality, mortalities
- Proper parentheses for Boolean precedence

**Sensitivity vs Precision**:
- High sensitivity: Include all PICO synonyms, broader terms
- High precision: Use specific combinations, narrow terms
- **Recommended**: Moderate sensitivity (include key synonyms) + post-hoc screening

**CRITICAL**: Return ONLY valid JSON, no markdown formatting, no code blocks.

Return JSON:
{
    "elsevier_query": "TITLE-ABS-KEY query string",
    "pubmed_query": "PubMed query string with [Title/Abstract] tags",
    "openalex_query": "OpenAlex simple query string",
    "pico_structure": {
        "population": "P terms used",
        "intervention": "I terms used",
        "comparison": "C terms used (or 'Not applicable')",
        "outcome": "O terms used"
    },
    "reasoning": "Explain PICO-based query structure and strategic choices"
}"""

        # Extract PICO structure from pulse result
        pico = pulse_result.get('pico', {})
        keywords = pulse_result.get('expanded_keywords', [])
        pico_statement = pulse_result.get('pico_statement', '')

        # Format PICO structure for LLM
        pico_str = json.dumps({
            "pico_statement": pico_statement,
            "population": pico.get('population', []),
            "intervention": pico.get('intervention', []),
            "comparison": pico.get('comparison', []),
            "outcome": pico.get('outcome', []),
            "study_design": pulse_result.get('study_design', [])
        }, indent=2)

        keywords_str = ", ".join(keywords)

        user_message = f"""PICO-Structured Keywords:

{pico_str}

All keywords (flat list): {keywords_str}

Please create three optimized Boolean search strings using the PICO structure above for Elsevier/Scopus, PubMed, and OpenAlex."""

        response_text = self._call_agent("Formulator", system_prompt, user_message, max_tokens=3000)

        try:
            json_text = self._extract_json(response_text)
            result = json.loads(json_text)
            self.logger.agent_thinking("Formulator", "🎯 Crafted 3 database-optimized Boolean masterpieces!")
            return result
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Formulator: Failed to parse JSON response: {e}")
            self.logger.error(f"Raw response: {response_text[:500]}...")
            return {
                "elsevier_query": " OR ".join([f'"{kw}"' for kw in keywords[:5]]),
                "pubmed_query": " OR ".join([f'"{kw}"[Title/Abstract]' for kw in keywords[:5]]),
                "openalex_query": " ".join(keywords[:5]),
                "reasoning": "Fallback: simple OR queries"
            }

    def _agent_sentinel(self, queries: Dict) -> Dict:
        """
        Agent 3: Sentinel - Query Validation
        Reviews and validates Boolean queries for syntax and quality.
        """
        self.logger.info("=" * 60)
        self.logger.info("SENTINEL AGENT - Quality Control")
        self.logger.info("=" * 60)
        self.logger.agent_thinking("Sentinel", "🛡️ Inspecting queries with a magnifying glass and a touch of perfectionism...")

        system_prompt = """You are Sentinel, a quality control expert for systematic literature review search strategies.

Your role is to validate and refine Boolean queries according to systematic review best practices (PRISMA, Cochrane standards).

VALIDATION CHECKLIST:

1. **Syntax Correctness**:
   - Parentheses balanced and properly nested
   - Field tags correctly formatted ([Title/Abstract], TITLE-ABS-KEY())
   - Wildcards (*) used appropriately (not at beginning of words)
   - Boolean operators (AND, OR) properly capitalized

2. **Concept Structure**:
   - Related synonyms grouped with OR
   - Different concepts connected with AND
   - Proper nesting: (synonym1 OR synonym2) AND (concept2)

3. **Search Strategy Quality**:
   - Not overly broad (e.g., single common words without context)
   - Not overly narrow (missing important synonyms)
   - Includes methodological terms if study design matters
   - Field restrictions applied (Title/Abstract focus)

4. **Database-Specific Optimization**:
   - Scopus: Proper TITLE-ABS-KEY() wrapper
   - PubMed: Consider MeSH terms for biomedical concepts
   - OpenAlex: Simplified but still precise

5. **Systematic Review Rigor**:
   - Captures both intervention/exposure AND outcome
   - Includes study design terms if causal inference is the goal
   - Balances sensitivity (finding all relevant studies) vs. precision

EXAMPLE SYSTEMATIC REVIEW QUERY STRUCTURE:
"I am interested in research on [INTERVENTION/EXPOSURE] impacts on [OUTCOME]. I specifically want studies with [STUDY DESIGN CRITERIA, e.g., causal research designs, experimental or quasi-experimental studies, randomized controlled trials]."

YOUR TASK:
- FIX any syntax errors you find
- IMPROVE query structure if needed
- ENSURE all three queries are valid and executable
- If queries are already good, return them as-is

CRITICAL: Return ONLY valid JSON, no markdown formatting, no explanations outside the JSON.

Return JSON:
{
    "elsevier_query": "VALIDATED_AND_REFINED_QUERY",
    "pubmed_query": "VALIDATED_AND_REFINED_QUERY",
    "openalex_query": "VALIDATED_AND_REFINED_QUERY",
    "validation_notes": "Summary of validation checks and refinements made",
    "warnings": ["list of any remaining concerns"] or []
}"""

        queries_str = json.dumps(queries, indent=2)
        user_message = f"""Please validate and improve these Boolean queries:

{queries_str}

Return the final validated versions."""

        response_text = self._call_agent("Sentinel", system_prompt, user_message, max_tokens=3000)

        try:
            json_text = self._extract_json(response_text)
            result = json.loads(json_text)
            warnings = result.get('warnings', [])
            if warnings:
                self.logger.warning(f"⚠️ Sentinel spotted {len(warnings)} potential issues to review")
            else:
                self.logger.info("Sentinel: ✅ All queries passed the rigorous quality inspection!")
            return result
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Sentinel: Failed to parse JSON response: {e}")
            self.logger.error(f"Raw response: {response_text[:500]}...")
            return {
                **queries,
                "validation_notes": "Fallback: using Formulator queries without validation",
                "warnings": ["Could not validate queries due to parsing error"]
            }

    def _agent_refiner(self, sentinel_result: Dict) -> Dict:
        """
        Agent 4: Refiner - Final Polish
        Takes Sentinel's validation report and produces final, issue-free queries.
        """
        self.logger.info("=" * 60)
        self.logger.info("REFINER AGENT - Final Polish")
        self.logger.info("=" * 60)
        self.logger.agent_thinking("Refiner", "💎 Polishing queries to perfection and resolving all issues...")

        system_prompt = """You are Refiner, the final quality assurance expert for systematic literature review search strategies.

Your role is to take validated queries and their validation reports, then produce the FINAL, PERFECT, ISSUE-FREE versions.

YOUR MISSION:
1. **Address ALL Warnings**: If the validation report contains any warnings, FIX them completely
2. **Optimize Structure**: Ensure optimal Boolean operator hierarchy and parentheses nesting
3. **Enhance Precision**: Remove any remaining ambiguities or potential syntax errors
4. **Final Verification**: Confirm all three queries are ready for immediate execution

SPECIFIC FIXES TO MAKE:
- If parentheses are unbalanced → Balance them
- If field tags are missing → Add them (TITLE-ABS-KEY(), [Title/Abstract])
- If synonyms are poorly grouped → Regroup with proper OR logic
- If query is too broad → Add more specific combinations
- If query is too narrow → Add important missing synonyms
- If methodological terms are missing → Add them (for causal studies)
- If wildcards are misplaced → Fix placement (should be at end: adapt*, not *adapt)

QUALITY CHECKLIST:
✅ Syntax: Perfect, no errors
✅ Structure: Logical grouping with proper nesting
✅ Coverage: Comprehensive synonyms and methodological terms
✅ Precision: Focused on relevant studies
✅ Executability: Ready to run immediately in each database

CRITICAL: Return ONLY valid JSON, no markdown formatting, no code blocks, no explanations outside the JSON.

Return JSON:
{
    "elsevier_query": "FINAL_PERFECT_QUERY",
    "pubmed_query": "FINAL_PERFECT_QUERY",
    "openalex_query": "FINAL_PERFECT_QUERY",
    "refinement_notes": "Summary of improvements made and confirmation that all issues are resolved",
    "issues_resolved": ["list of specific issues fixed"] or []
}"""

        queries_str = json.dumps({
            "elsevier_query": sentinel_result.get('elsevier_query', ''),
            "pubmed_query": sentinel_result.get('pubmed_query', ''),
            "openalex_query": sentinel_result.get('openalex_query', ''),
            "validation_notes": sentinel_result.get('validation_notes', ''),
            "warnings": sentinel_result.get('warnings', [])
        }, indent=2)

        user_message = f"""Please refine these validated queries into their FINAL, PERFECT versions:

{queries_str}

Address any warnings and produce issue-free, execution-ready queries."""

        response_text = self._call_agent("Refiner", system_prompt, user_message, max_tokens=3000)

        try:
            json_text = self._extract_json(response_text)
            result = json.loads(json_text)
            issues_resolved = result.get('issues_resolved', [])
            if issues_resolved:
                self.logger.info(f"Refiner: ✅ Resolved {len(issues_resolved)} issues - queries are now perfect!")
            else:
                self.logger.info("Refiner: ✅ Queries were already excellent - final polish applied!")
            return result
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Refiner: Failed to parse JSON response: {e}")
            self.logger.error(f"Raw response: {response_text[:500]}...")
            return {
                "elsevier_query": sentinel_result.get('elsevier_query', ''),
                "pubmed_query": sentinel_result.get('pubmed_query', ''),
                "openalex_query": sentinel_result.get('openalex_query', ''),
                "refinement_notes": "Fallback: using Sentinel queries without refinement",
                "issues_resolved": []
            }

    def generate_queries(self, topic: str, variation_seed: Optional[int] = None) -> Dict:
        """
        Main workflow: Run all four agents in sequence.

        Args:
            topic: Research topic string
            variation_seed: Optional seed for generating query variations (1, 2, 3, etc.)

        Returns:
            Dict containing:
                - pulse_keywords: Expanded keyword list
                - pulse_reasoning: Pulse's reasoning
                - formulator_queries: Initial queries from Formulator
                - formulator_reasoning: Formulator's reasoning
                - sentinel_queries: Validated queries from Sentinel
                - sentinel_validation: Sentinel's validation notes
                - sentinel_warnings: Any warnings
                - refiner_queries: Final polished queries
                - refiner_notes: Refiner's refinement notes
                - issues_resolved: List of issues fixed
                - variation_seed: The variation seed used (if any)
                - logs: Detailed process logs
        """
        variation_note = f" (Variation #{variation_seed})" if variation_seed else ""
        self.logger.info(f"Starting query generation for topic{variation_note}: '{topic}'")
        start_time = time.time()

        # Agent 1: Pulse (PICO-based keyword expansion)
        pulse_result = self._agent_pulse(topic, variation_seed=variation_seed)

        # Agent 2: Formulator (PICO-structured query construction)
        formulator_result = self._agent_formulator(pulse_result)

        # Agent 3: Sentinel
        sentinel_result = self._agent_sentinel({
            "elsevier_query": formulator_result.get('elsevier_query', ''),
            "pubmed_query": formulator_result.get('pubmed_query', ''),
            "openalex_query": formulator_result.get('openalex_query', '')
        })

        # Agent 4: Refiner
        refiner_result = self._agent_refiner(sentinel_result)

        elapsed = time.time() - start_time
        self.logger.info(f"🎊 Query generation completed in {elapsed:.2f} seconds - Ready to unleash upon the databases!")
        self.logger.info("=" * 60)

        return {
            "pulse_keywords": pulse_result.get('expanded_keywords', []),
            "pulse_pico": pulse_result.get('pico', {}),
            "pulse_pico_statement": pulse_result.get('pico_statement', ''),
            "pulse_study_design": pulse_result.get('study_design', []),
            "pulse_reasoning": pulse_result.get('reasoning', ''),
            "formulator_queries": {
                "elsevier_query": formulator_result.get('elsevier_query', ''),
                "pubmed_query": formulator_result.get('pubmed_query', ''),
                "openalex_query": formulator_result.get('openalex_query', '')
            },
            "formulator_pico_structure": formulator_result.get('pico_structure', {}),
            "formulator_reasoning": formulator_result.get('reasoning', ''),
            "sentinel_queries": {
                "elsevier_query": sentinel_result.get('elsevier_query', ''),
                "pubmed_query": sentinel_result.get('pubmed_query', ''),
                "openalex_query": sentinel_result.get('openalex_query', '')
            },
            "sentinel_validation": sentinel_result.get('validation_notes', ''),
            "sentinel_warnings": sentinel_result.get('warnings', []),
            "refiner_queries": {
                "elsevier_query": refiner_result.get('elsevier_query', ''),
                "pubmed_query": refiner_result.get('pubmed_query', ''),
                "openalex_query": refiner_result.get('openalex_query', '')
            },
            "refiner_notes": refiner_result.get('refinement_notes', ''),
            "issues_resolved": refiner_result.get('issues_resolved', []),
            "variation_seed": variation_seed,
            "logs": self.logger.get_ui_logs()
        }


# Test the module
if __name__ == "__main__":
    team = QueryGenerationTeam()
    result = team.generate_queries("climate change and mental health impacts")

    print("\n" + "=" * 60)
    print("PULSE KEYWORDS:")
    print("=" * 60)
    for kw in result['pulse_keywords']:
        print(f"  - {kw}")

    print("\n" + "=" * 60)
    print("FINAL QUERIES:")
    print("=" * 60)
    print(f"\nElsevier/Scopus:\n{result['sentinel_queries']['elsevier_query']}")
    print(f"\nPubMed:\n{result['sentinel_queries']['pubmed_query']}")
    print(f"\nOpenAlex:\n{result['sentinel_queries']['openalex_query']}")

    if result['sentinel_warnings']:
        print("\n" + "=" * 60)
        print("WARNINGS:")
        print("=" * 60)
        for warning in result['sentinel_warnings']:
            print(f"  ⚠️  {warning}")
