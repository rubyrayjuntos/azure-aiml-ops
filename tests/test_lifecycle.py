from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    source_directory = str(ROOT / "data-science" / "src")
    if source_directory not in sys.path:
        sys.path.insert(0, source_directory)
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promotion_has_winning_and_losing_paths() -> None:
    evaluate = _load("evaluate", "data-science/src/evaluate.py")
    assert evaluate.promotion_decision(0.8, 0.7, 0.01)["promote"] is True
    assert evaluate.promotion_decision(0.7, 0.8, 0.01)["promote"] is False


def test_registration_never_overrides_a_losing_decision() -> None:
    register = _load("register", "data-science/src/register.py")
    assert register.should_register({"promote": False}) is False
    assert register.should_register({"promote": True}) is True
    source = (ROOT / "data-science/src/register.py").read_text()
    assert "deploy_flag=1" not in source.replace(" ", "")


def test_evaluation_uses_an_explicit_champion_metric() -> None:
    source = (ROOT / "data-science/src/evaluate.py").read_text()
    assert "search_model_versions" not in source
    pipeline = ROOT / "mlops/azureml/train/pipeline.yml"
    if pipeline.exists():
        assert "champion_metric" in pipeline.read_text()


def test_batch_deployment_has_no_latest_alias() -> None:
    deployment = ROOT / "mlops/azureml/deploy/batch/deployment.yml"
    if deployment.exists():
        source = deployment.read_text()
        assert "@latest" not in source
        assert "azureml:" in source


def test_local_runner_reuses_lifecycle_scripts() -> None:
    runner = (ROOT / "scripts/run_local_lifecycle.py").read_text()
    for script in ("prepare.py", "train.py", "evaluate.py", "package_model.py", "score_local.py"):
        assert script in runner
    assert "--local-root" in runner


def test_no_out_of_scope_directories() -> None:
    for directory in ("foundry", "databricks", "rag", "infra/bicep"):
        assert not (ROOT / directory).exists()


def test_evidence_writer_matches_artifact_uri_conformance_vectors() -> None:
    emitter = _load("emit_evidence", "scripts/emit_evidence.py")
    vectors = json.loads(
        (ROOT / "platform/artifact-uri-conformance.json").read_text(encoding="utf-8")
    )
    for uri in vectors["valid"]:
        assert emitter.validate_artifact_uri(uri) == uri
    for uri in vectors["invalid"]:
        with pytest.raises(ValueError, match="artifact URI"):
            emitter.validate_artifact_uri(uri)


def test_generated_event_identity_uses_every_versioned_input() -> None:
    emitter = _load("emit_evidence_identity", "scripts/emit_evidence.py")
    baseline = emitter.event_identity("provider", "capability", "operation", "op-1", "run", 0)
    assert emitter.event_identity("provider", "other", "operation", "op-1", "run", 0) != baseline
    assert (
        emitter.event_identity("provider", "capability", "operation", "op-2", "run", 0)
        != baseline
    )
    source = (ROOT / "scripts/emit_evidence.py").read_text(encoding="utf-8")
    assert 'EVENT_IDENTITY_VERSION = "1.0"' in source
    assert emitter.EVENT_IDENTITY_FIELDS == (
        "project",
        "environment",
        "provider",
        "capability",
        "operation",
        "operation_id",
        "source_run_id",
        "source_sequence",
    )


def test_constraints_match_the_pinned_training_environment() -> None:
    constraints = {
        line.split("==", 1)[0].lower(): line.split("==", 1)[1]
        for line in (ROOT / "constraints.txt").read_text(encoding="utf-8").splitlines()
        if "==" in line
    }
    environment = yaml.safe_load(
        (ROOT / "data-science/environment/train-conda.yml").read_text(encoding="utf-8")
    )
    pip_dependencies = next(
        dependency["pip"]
        for dependency in environment["dependencies"]
        if isinstance(dependency, dict) and "pip" in dependency
    )
    for dependency in pip_dependencies:
        name, version = dependency.split("==", 1)
        if name.lower() in constraints:
            assert constraints[name.lower()] == version
