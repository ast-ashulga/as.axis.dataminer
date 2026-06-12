"""Workspace and output directory path resolution."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent


def workspace_dir(run_id: str) -> Path:
    return _ROOT / "workspace" / run_id


def output_dir(tradition: str) -> Path:
    return _ROOT / "output" / tradition


def fragments_dir(tradition: str, division: str) -> Path:
    return output_dir(tradition) / "fragments" / division


def nas_to_fragment_path(tradition: str, nas: str) -> Path:
    """Return the fragment file path for a NAS address (bijective: one NAS = one file).

    nms://tradition/division/episode      → fragments/division/episode.yaml
    nms://tradition/division/episode/sub  → fragments/division/episode/sub.yaml
    """
    parts = nas.split("/")[3:]  # strip "nms:", "", "tradition"
    return output_dir(tradition) / "fragments" / Path(*parts[:-1]) / f"{parts[-1]}.yaml"


def annotation_candidates_dir(tradition: str, division: str) -> Path:
    return output_dir(tradition) / "annotation-candidates" / division


def artifacts_dir(tradition: str, division: str) -> Path:
    return output_dir(tradition) / "artifacts" / division


def embeddings_dir(tradition: str, division: str) -> Path:
    return output_dir(tradition) / "embeddings" / division


def parallels_dir(tradition: str) -> Path:
    return output_dir(tradition) / "parallels"


def pipeline_reports_dir(tradition: str) -> Path:
    return output_dir(tradition) / "pipeline-reports"


def ingested_dir(run_id: str) -> Path:
    return workspace_dir(run_id) / "ingested"


def segmented_dir(run_id: str) -> Path:
    return workspace_dir(run_id) / "segmented"


# ---- Specific file paths ----

def nas_proposals_path(tradition: str) -> Path:
    return output_dir(tradition) / "nas-proposals.yaml"


def nas_confirmed_path(tradition: str) -> Path:
    return output_dir(tradition) / "nas-confirmed.yaml"


def nas_revisions_path(tradition: str) -> Path:
    return output_dir(tradition) / "nas-revisions.yaml"


def manifest_path(tradition: str) -> Path:
    return output_dir(tradition) / "manifest.yaml"


def review_decisions_path(tradition: str) -> Path:
    return output_dir(tradition) / "review-decisions.yaml"


def ingestion_report_path(tradition: str) -> Path:
    return pipeline_reports_dir(tradition) / "ingestion-report.yaml"


def segmentation_report_path(tradition: str) -> Path:
    return pipeline_reports_dir(tradition) / "segmentation-report.yaml"


def annotation_report_path(tradition: str) -> Path:
    return pipeline_reports_dir(tradition) / "annotation-report.yaml"


def pipeline_errors_path(tradition: str) -> Path:
    return pipeline_reports_dir(tradition) / "pipeline-errors.yaml"


def review_queue_path(tradition: str) -> Path:
    return pipeline_reports_dir(tradition) / "review-queue.yaml"


def load_passage_text(division: str, episode: str) -> str | None:
    """Return segmented passage text for a division/episode, or None if not yet segmented."""
    candidates = list((_ROOT / "workspace").glob(f"*/segmented/{division}/{episode}.txt"))
    if candidates:
        return candidates[-1].read_text(encoding="utf-8")
    return None


def load_all_passage_texts(division: str, episode: str, nas: str = "") -> list[tuple[str, str]]:
    """Return all passage texts as (source_label, text) pairs.

    When nas is provided, tries the bijective sub-episode path first
    (segmented/division/episode/sub-episode.txt), falling back to the
    episode-level path (segmented/division/episode.txt).
    Source label is the translation_id from the run manifest, falling back to run_id.
    """
    import re as _re

    def _collect(glob_pat: str) -> list[tuple[str, str]]:
        results = []
        for txt_path in sorted((_ROOT / "workspace").glob(f"*/segmented/{glob_pat}")):
            path_parts = txt_path.parts
            seg_idx = next(i for i, p in enumerate(path_parts) if p == "segmented")
            run_dir = Path(*path_parts[:seg_idx])
            manifest_file = run_dir / "ingested" / "manifest.yaml"
            label = run_dir.name
            if manifest_file.exists():
                raw = manifest_file.read_text(encoding="utf-8")
                m = _re.search(r"^translation_id:\s*(.+)$", raw, _re.MULTILINE)
                if m:
                    label = m.group(1).strip().strip('"').strip("'")
            results.append((label, txt_path.read_text(encoding="utf-8")))
        return results

    if nas:
        nas_parts = nas.split("/")[3:]  # strip "nms:", "", tradition
        if len(nas_parts) >= 2:
            nas_glob = str(Path(*nas_parts[:-1]) / f"{nas_parts[-1]}.txt")
            found = _collect(nas_glob)
            if found:
                return found

    return _collect(f"{division}/{episode}.txt")
