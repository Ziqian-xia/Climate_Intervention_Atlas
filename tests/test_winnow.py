"""
Tests for Winnow — updated functions:
  - AnthropicProvider  (model param)
  - BedrockProvider    (unchanged API, regression)
  - DummyProvider      (regression)
  - create_llm_provider factory
  - app.py: ANTHROPIC_MODELS / BEDROCK_MODELS catalogue
  - app.py: session-state defaults (anthropic_model_id)
"""

import sys
import os
import types
import unittest

# ── Add repo root to path ──────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.llm_providers import (
    AnthropicProvider,
    BedrockProvider,
    DummyProvider,
    create_llm_provider,
)


# ==============================================================================
# AnthropicProvider
# ==============================================================================

class TestAnthropicProviderInit(unittest.TestCase):

    def test_default_model_is_sonnet_4_6(self):
        p = AnthropicProvider()
        self.assertEqual(p.model, "claude-sonnet-4-6")

    def test_custom_model_stored(self):
        for mid in ["claude-opus-4-7", "claude-haiku-4-5-20251001", "claude-3-5-sonnet-20241022"]:
            with self.subTest(model=mid):
                p = AnthropicProvider(model=mid)
                self.assertEqual(p.model, mid)

    def test_no_api_key_not_available(self):
        p = AnthropicProvider(api_key=None)
        self.assertFalse(p.is_available())

    def test_empty_api_key_not_available(self):
        p = AnthropicProvider(api_key="")
        self.assertFalse(p.is_available())

    def test_get_model_name_contains_model_id(self):
        p = AnthropicProvider(model="claude-haiku-4-5-20251001")
        self.assertIn("claude-haiku-4-5-20251001", p.get_model_name())

    def test_no_client_when_no_key(self):
        p = AnthropicProvider(api_key=None)
        self.assertIsNone(p.client)


# ==============================================================================
# DummyProvider  (regression)
# ==============================================================================

class TestDummyProvider(unittest.TestCase):

    def test_always_available(self):
        self.assertTrue(DummyProvider().is_available())

    def test_returns_empty_string(self):
        p = DummyProvider()
        result = p.call_model("sys", "user")
        self.assertIsInstance(result, str)

    def test_get_model_name(self):
        self.assertIsInstance(DummyProvider().get_model_name(), str)


# ==============================================================================
# create_llm_provider factory
# ==============================================================================

class TestCreateLlmProvider(unittest.TestCase):

    def test_dummy_factory(self):
        p = create_llm_provider("dummy", {})
        self.assertIsInstance(p, DummyProvider)

    def test_anthropic_factory_default_model(self):
        p = create_llm_provider("anthropic", {"api_key": None})
        self.assertIsInstance(p, AnthropicProvider)
        self.assertEqual(p.model, "claude-sonnet-4-6")

    def test_anthropic_factory_custom_model(self):
        p = create_llm_provider("anthropic", {
            "api_key": None,
            "model": "claude-opus-4-7"
        })
        self.assertEqual(p.model, "claude-opus-4-7")

    def test_anthropic_factory_haiku(self):
        p = create_llm_provider("anthropic", {
            "api_key": None,
            "model": "claude-haiku-4-5-20251001"
        })
        self.assertEqual(p.model, "claude-haiku-4-5-20251001")

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            create_llm_provider("openai", {})

    def test_bedrock_factory_returns_bedrock(self):
        p = create_llm_provider("bedrock", {})
        self.assertIsInstance(p, BedrockProvider)


# ==============================================================================
# App-level model catalogue  (imported without Streamlit)
# ==============================================================================

class TestModelCatalogue(unittest.TestCase):
    """
    Import only the catalogue constants from app.py by exec-ing the file with
    Streamlit stubbed out so we don't need a running server.
    """

    @classmethod
    def setUpClass(cls):
        # Minimal Streamlit stub — enough for module-level code in app.py to run
        st_stub = types.ModuleType("streamlit")
        # session_state needs attribute access
        class _SS(dict):
            def __getattr__(self, k):
                return self[k] if k in self else None
            def __setattr__(self, k, v):
                self[k] = v
        st_stub.session_state = _SS()

        # Stub every st.* call used at module level
        noop = lambda *a, **kw: None
        for fn in ["set_page_config", "markdown", "title", "caption", "info",
                   "warning", "error", "success", "write", "stop", "rerun",
                   "sidebar", "expander", "columns", "button", "text_input",
                   "text_area", "selectbox", "radio", "number_input", "slider",
                   "checkbox", "file_uploader", "download_button", "metric",
                   "code", "container", "status", "subheader", "balloons",
                   "spinner", "tabs"]:
            setattr(st_stub, fn, noop)

        # sidebar needs to be a context manager
        class _CM:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def __getattr__(self, k): return noop
        st_stub.sidebar = _CM()

        sys.modules["streamlit"] = st_stub

        # Stub pandas (not installed in test env potentially)
        if "pandas" not in sys.modules:
            pd_stub = types.ModuleType("pandas")
            pd_stub.read_csv = lambda *a, **kw: None
            pd_stub.DataFrame = list
            sys.modules["pandas"] = pd_stub

        # Now load just the catalogue constants by reading the file and
        # extracting only the ANTHROPIC_MODELS / BEDROCK_MODELS blocks
        app_path = os.path.join(ROOT, "app.py")
        src = open(app_path).read()

        # Execute only up to first function definition after catalogues
        # We'll exec the whole file but with all the stubs in place
        # Use a fresh namespace to avoid polluting globals
        ns = {"__name__": "__test__"}
        try:
            exec(compile(src, app_path, "exec"), ns)
        except SystemExit:
            pass
        except Exception:
            pass  # partial exec is fine — we only need the catalogues

        cls.ns = ns

    def test_anthropic_models_has_sonnet_46(self):
        models = self.ns.get("ANTHROPIC_MODELS", {})
        self.assertIn("claude-sonnet-4-6", models.values(),
                      "claude-sonnet-4-6 must be in ANTHROPIC_MODELS")

    def test_anthropic_models_has_haiku(self):
        models = self.ns.get("ANTHROPIC_MODELS", {})
        self.assertTrue(
            any("haiku" in v for v in models.values()),
            "A Haiku model must be in ANTHROPIC_MODELS"
        )

    def test_anthropic_models_has_opus(self):
        models = self.ns.get("ANTHROPIC_MODELS", {})
        self.assertTrue(
            any("opus" in v for v in models.values()),
            "An Opus model must be in ANTHROPIC_MODELS"
        )

    def test_bedrock_models_has_sonnet(self):
        models = self.ns.get("BEDROCK_MODELS", {})
        self.assertTrue(
            any("sonnet" in v for v in models.values()),
            "A Sonnet model must be in BEDROCK_MODELS"
        )

    def test_recommended_label_present(self):
        models = self.ns.get("ANTHROPIC_MODELS", {})
        self.assertTrue(
            any("Recommended" in lbl for lbl in models.keys()),
            "At least one label should carry 'Recommended'"
        )

    def test_haiku_label_mentions_screening(self):
        models = self.ns.get("ANTHROPIC_MODELS", {})
        self.assertTrue(
            any("screening" in lbl.lower() for lbl in models.keys()),
            "Haiku label should mention 'screening' as the recommended use-case"
        )

    def test_no_duplicate_model_ids(self):
        for name, models in [
            ("ANTHROPIC_MODELS", self.ns.get("ANTHROPIC_MODELS", {})),
            ("BEDROCK_MODELS",   self.ns.get("BEDROCK_MODELS", {})),
        ]:
            ids = list(models.values())
            self.assertEqual(len(ids), len(set(ids)),
                             f"Duplicate model IDs found in {name}")

    def test_session_default_anthropic_model(self):
        # init_session_state sets 'anthropic_model_id' to 'claude-sonnet-4-6'
        # After the exec above, session_state should have been populated
        ss = sys.modules["streamlit"].session_state
        self.assertEqual(
            ss.get("anthropic_model_id", "NOT_SET"),
            "claude-sonnet-4-6",
            "Default anthropic_model_id must be claude-sonnet-4-6"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
