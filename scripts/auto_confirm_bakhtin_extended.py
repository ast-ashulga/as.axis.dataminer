"""Auto-confirm new Bakhtin extended-code annotation candidates.

Confirms all status:candidate annotations whose codes belong to the
POLYPHONY / CARNIVALESQUE / HETEROGLOSSIA families added in the
Sisyphus gap-closure (S1/S2). Runs for a given tradition, writes
review decisions to review-decisions.yaml under the reviewer 'Mnemosyne'.

Usage:
    python scripts/auto_confirm_bakhtin_extended.py iliad
    python scripts/auto_confirm_bakhtin_extended.py mahabharata
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sisyphus.io.workspace import output_dir, review_decisions_path
from sisyphus.io.yaml_io import read_yaml, write_yaml

EXTENDED_PREFIXES = (
    "BAKHTIN-POLYPHONY-",
    "BAKHTIN-CARNIVALESQUE-",
    "BAKHTIN-HETEROGLOSSIA-",
)

REVIEWER = "Mnemosyne"


def is_extended_code(code: str) -> bool:
    return any(code.startswith(p) for p in EXTENDED_PREFIXES)


def confirm_tradition(tradition: str) -> None:
    ann_root = output_dir(tradition) / "annotation-candidates"
    if not ann_root.exists():
        print(f"No annotation-candidates dir for '{tradition}'")
        return

    decisions_path = review_decisions_path(tradition)
    existing_decisions: list[dict] = []
    if decisions_path.exists():
        existing_decisions = read_yaml(decisions_path).get("decisions", [])

    new_decisions: list[dict] = []
    confirmed_count = 0
    skipped_count = 0

    for ann_path in sorted(ann_root.glob("**/*.bakhtin.yaml")):
        data = read_yaml(ann_path)
        if not data:
            continue

        nas = data.get("nas", "")
        track = data.get("track", "bakhtin")
        modified = False

        for ann in data.get("annotations", []):
            if ann.get("status") != "candidate":
                continue
            code = ann.get("code", "")
            if not is_extended_code(code):
                skipped_count += 1
                continue

            tier = ann.get("proposed_tier", "reconstructed")
            ann["status"] = "confirmed"
            modified = True
            confirmed_count += 1

            new_decisions.append({
                "audit_id": str(uuid.uuid4()),
                "timestamp": datetime.now(UTC).isoformat(),
                "reviewer": REVIEWER,
                "action": "confirmed",
                "record_type": "annotation",
                "nas": nas,
                "track": track,
                "code": code,
                "confidence_tier_assigned": tier,
                "review_note": "Auto-confirmed: Bakhtin extended taxonomy (polyphony/carnivalesque/heteroglossia dimension codes).",
            })

        if modified:
            write_yaml(ann_path, data)

    write_yaml(decisions_path, {
        "tradition_id": tradition,
        "decisions": existing_decisions + new_decisions,
    })

    print(
        f"[{tradition}] confirmed {confirmed_count} extended-code annotations "
        f"({skipped_count} non-extended candidates left as-is)"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/auto_confirm_bakhtin_extended.py <tradition>")
        sys.exit(1)
    confirm_tradition(sys.argv[1])
