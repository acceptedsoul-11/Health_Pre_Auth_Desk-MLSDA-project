"""Write the 50-record manual demo guide without adding records to Redis."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Import the reusable, non-dashboard sample builder from the seeder.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_demo_data import _build_additional_demo_records  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "MANUAL_DEMO_GUIDE.txt"


def _payload(record: dict) -> dict:
    return {
        "request_id": f"MANUAL-{record['record_id']}",
        "patient": record["patient"],
        "policy": record["policy"],
        "hospital": record["hospital"],
        "medical": record["medical"],
        "free_text_notes": record["note"],
    }


def _powershell_block(payload: dict) -> str:
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    return f'''$body = @'
{body}
'@
$response = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/preauth" `
  -ContentType "application/json" `
  -Body $body
$response | ConvertTo-Json -Depth 10

# Save the returned run ID, then poll until the agent finishes.
$runId = $response.run_id
do {{
  Start-Sleep -Seconds 2
  $status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/preauth/$runId"
  Write-Host "Status: $($status.status)"
}} while ($status.status -in @("pending", "processing"))
$status | ConvertTo-Json -Depth 10
'''


def main() -> None:
    records = _build_additional_demo_records()
    sections = [
        """MANUAL LIVE DEMO GUIDE — 50 ADDITIONAL PRE-AUTH REQUESTS
===============================================================

These 50 samples are NOT seeded into Redis and will NOT appear on the dashboard.
Submit one sample at a time through the Submit page or the API; each submission
gets its own live run ID and status page. Submitted RUN-* records are stored in
PostgreSQL for durable run history; Redis is used for fast queue/status polling.
If PostgreSQL is temporarily unavailable, the request still runs and remains
available through Redis for its configured cache lifetime.

RECOMMENDED WINDOWS + DOCKER COMMANDS
--------------------------------------
Open PowerShell in the project folder:

  cd C:\\Users\\saira\\OneDrive\\Desktop\\MLSDA_mini

First-time setup / start:

  docker compose up -d
  docker compose ps
  docker compose run --rm corpus-ingest
  Start-Process http://localhost:3000/submit

For later demos, use only `docker compose up -d` unless the stack is stopped.
Do NOT run scripts\\seed_demo_data.py for these 50 manual samples; that command
is only for the original dashboard showcase records.

SHOW THE DEMO IN THE BROWSER
----------------------------
1. Open http://localhost:3000/submit (the Start-Process command above does it).
2. Enter one sample's patient, policy, hospital, and medical fields from below.
3. Click Submit Pre-Authorization Request.
4. The app navigates to the live status page for that request.
5. Use the Dashboard link only for the original pre-seeded showcase records.

RUN ONE SAMPLE DIRECTLY FROM POWERSHELL
---------------------------------------
Each sample below contains a complete copy/paste block. Copy the block under
the sample you want, paste it into PowerShell, and press Enter. It POSTs one
request, prints the run ID, and polls until the result is complete.

If you prefer the UI, use the same JSON values as the form fields instead.

STOP COMMANDS
-------------
Stop the demo containers but keep local volumes/data:

  docker compose stop

Stop and remove the containers/network (safe; volumes are kept):

  docker compose down

Optional full local reset (removes Redis/Postgres/Grafana/Prometheus volumes):

  docker compose down -v

"""
    ]

    for index, record in enumerate(records, start=1):
        payload = _payload(record)
        sections.append(
            f"""\nSAMPLE {index:02d} — {record['record_id']} — {record['patient']['full_name']}
{'-' * 72}
Expected route: {record['expected_outcome']}
Hospital: {record['hospital']['hospital_name']} ({record['hospital']['city']})
Procedure: {record['medical']['procedure_name']}
Note: {record['note']}

Copy/paste this complete PowerShell block to run this one sample:

{_powershell_block(payload)}
"""
        )

    OUT.write_text("\n".join(sections), encoding="utf-8")
    print(f"Wrote {len(records)} manual samples to {OUT}")


if __name__ == "__main__":
    main()
