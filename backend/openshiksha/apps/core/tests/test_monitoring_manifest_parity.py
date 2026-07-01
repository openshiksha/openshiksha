"""OACT-6 — Manifest-vs-docs parity guard for the monitoring stack.

Two safety-critical artifacts are embedded **verbatim** inside the deployable
`k8s/monitoring/` manifests, each a hand-maintained copy of a canonical source
under `docs/ops/`:

  * `k8s/monitoring/prometheus.yaml` → ConfigMap ``prometheus-rules`` embeds
    ``docs/ops/prometheus/openshiksha-alerts.yml`` (the ALT-1 alert rules).
  * `k8s/monitoring/grafana.yaml` → ConfigMap ``grafana-dashboard-overview``
    embeds ``docs/ops/grafana/openshiksha-overview.json`` (the MET-5 dashboard).

The only thing keeping them in sync today is a "keep the two in sync" comment.
Edit one, forget the other, and the `alerting-lint` CI job (which lints the
`docs/` copy) still passes while the **deployed** rules are stale — the classic
observability failure where the alarm you think you changed didn't change.

This is a pure file-parsing test (no DB, no Django models) that lives in the
test suite purely so it runs in CI for free. It compares **parsed structure**
(dicts/lists), not raw bytes, so the indentation/quoting the block-scalar embed
introduces is tolerated while any real content drift fails loudly.

Mirrors the existing repo parity idioms (widget-schema vendoring parity in
``test_widget_fields.py``; the LA i18n key-parity guard).
"""

import json
from pathlib import Path

import yaml

# tests/test_monitoring_manifest_parity.py -> repo root is parents[5]:
#   [0]=tests [1]=core [2]=apps [3]=openshiksha [4]=backend [5]=<repo root>
REPO_ROOT = Path(__file__).resolve().parents[5]


def _load_configmap_data(manifest_path: Path, configmap_name: str, data_key: str) -> str:
    """Return ``data[data_key]`` of the ConfigMap named ``configmap_name`` from a
    multi-document YAML manifest, or fail with a clear message."""
    docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
    for doc in docs:
        if (
            isinstance(doc, dict)
            and doc.get("kind") == "ConfigMap"
            and doc.get("metadata", {}).get("name") == configmap_name
        ):
            data = doc.get("data") or {}
            assert data_key in data, f"ConfigMap {configmap_name!r} in {manifest_path} has no data key {data_key!r}"
            return data[data_key]
    raise AssertionError(f"no ConfigMap named {configmap_name!r} found in {manifest_path}")


class TestMonitoringManifestParity:
    """The artifacts embedded in the deployable manifests must match their
    canonical ``docs/ops/`` sources by parsed structure."""

    def test_alert_rules_embed_matches_canonical_source(self):
        manifest = REPO_ROOT / "k8s" / "monitoring" / "prometheus.yaml"
        canonical = REPO_ROOT / "docs" / "ops" / "prometheus" / "openshiksha-alerts.yml"

        embedded_raw = _load_configmap_data(manifest, "prometheus-rules", "openshiksha-alerts.yml")
        embedded = yaml.safe_load(embedded_raw)
        source = yaml.safe_load(canonical.read_text(encoding="utf-8"))

        assert embedded == source, (
            "The alert rules embedded in k8s/monitoring/prometheus.yaml "
            "(ConfigMap prometheus-rules) have drifted from the canonical source "
            "docs/ops/prometheus/openshiksha-alerts.yml. Re-copy the canonical "
            "rules into the manifest ConfigMap."
        )

    def test_dashboard_embed_matches_canonical_source(self):
        manifest = REPO_ROOT / "k8s" / "monitoring" / "grafana.yaml"
        canonical = REPO_ROOT / "docs" / "ops" / "grafana" / "openshiksha-overview.json"

        embedded_raw = _load_configmap_data(manifest, "grafana-dashboard-overview", "openshiksha-overview.json")
        embedded = json.loads(embedded_raw)
        source = json.loads(canonical.read_text(encoding="utf-8"))

        assert embedded == source, (
            "The Grafana dashboard embedded in k8s/monitoring/grafana.yaml "
            "(ConfigMap grafana-dashboard-overview) has drifted from the canonical "
            "source docs/ops/grafana/openshiksha-overview.json. Re-copy the "
            "canonical dashboard JSON into the manifest ConfigMap."
        )

    def test_embedded_copies_are_non_empty_and_parse(self):
        """A truncated paste must fail loudly rather than silently comparing empty."""
        rules_raw = _load_configmap_data(
            REPO_ROOT / "k8s" / "monitoring" / "prometheus.yaml",
            "prometheus-rules",
            "openshiksha-alerts.yml",
        )
        dashboard_raw = _load_configmap_data(
            REPO_ROOT / "k8s" / "monitoring" / "grafana.yaml",
            "grafana-dashboard-overview",
            "openshiksha-overview.json",
        )

        rules = yaml.safe_load(rules_raw)
        assert isinstance(rules, dict) and rules.get("groups"), "embedded alert rules parsed empty / missing 'groups'"

        dashboard = json.loads(dashboard_raw)
        assert isinstance(dashboard, dict) and dashboard.get(
            "panels"
        ), "embedded Grafana dashboard parsed empty / missing 'panels'"
