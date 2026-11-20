"""Tests for the OCI Generative AI provider plugin. Run inside a Hermes checkout's environment."""

import dataclasses
import importlib.util
import pathlib

import pytest

from providers import get_provider_profile
from providers.base import ProviderProfile

_PLUGIN = pathlib.Path(__file__).resolve().parents[1] / "__init__.py"


@pytest.fixture(scope="module")
def profile() -> ProviderProfile:
    spec = importlib.util.spec_from_file_location("hermes_oci_provider", _PLUGIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # registers the profile
    p = get_provider_profile("oci")
    assert p is module.oci
    return p


def test_aliases_resolve(profile: ProviderProfile) -> None:
    for alias in ("oci-genai", "oracle", "oracle-cloud", "oci-generative-ai"):
        assert get_provider_profile(alias) is profile


def test_openai_compatible_bearer_key(profile: ProviderProfile) -> None:
    assert profile.api_mode == "chat_completions"
    assert profile.auth_type == "api_key"
    assert profile.env_vars[0] == "OCI_GENAI_API_KEY"
    assert profile.base_url.endswith("/openai/v1")


def test_no_model_listing_network_call(profile: ProviderProfile) -> None:
    """The OpenAI-compatible route does not serve GET /models; setup uses the curated list."""
    assert profile.supports_model_listing is False
    assert profile.fetch_models() is None
    assert "openai.gpt-oss-120b" in profile.fallback_models


def test_avoids_zstd_stream_encoding(profile: ProviderProfile) -> None:
    assert "zstd" not in profile.default_headers["Accept-Encoding"]


def test_curated_list_skips_llama(profile: ProviderProfile) -> None:
    """OCI rejects Llama tool calls whose first message is not a user turn."""
    assert not any(m.startswith("meta.") for m in profile.fallback_models)


@pytest.mark.parametrize("model", ["openai.gpt-5.6-mini", "openai.gpt-6-sol", "openai.gpt-6-luna"])
def test_reasoning_off_for_models_that_need_it_to_call_tools(profile: ProviderProfile, model: str) -> None:
    assert profile.build_api_kwargs_extras(model=model) == ({}, {"reasoning_effort": "none"})


@pytest.mark.parametrize("model", ["openai.gpt-5.5", "openai.gpt-oss-120b", "xai.grok-4.7", None])
def test_no_reasoning_override_otherwise(profile: ProviderProfile, model: str | None) -> None:
    assert profile.build_api_kwargs_extras(model=model) == ({}, {})


def test_models_dev_id_where_supported(profile: ProviderProfile) -> None:
    if "models_dev_id" in {f.name for f in dataclasses.fields(ProviderProfile)}:
        assert profile.models_dev_id == "oci"
