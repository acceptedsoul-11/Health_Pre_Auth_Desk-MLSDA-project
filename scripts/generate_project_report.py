from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, Line, Rect, String


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "Health_PreAuth_Desk_Report.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#12304A")
TEAL = colors.HexColor("#0F8B8D")
BLUE = colors.HexColor("#2F6F9F")
PALE_BLUE = colors.HexColor("#EAF3F7")
PALE_TEAL = colors.HexColor("#E8F6F4")
INK = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#5B6875")
LIGHT = colors.HexColor("#F5F7FA")
BORDER = colors.HexColor("#D5DEE7")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCompact", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=23, textColor=NAVY, spaceAfter=3))
styles.add(ParagraphStyle(name="SubCompact", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=MUTED, spaceAfter=5))
styles.add(ParagraphStyle(name="H1Compact", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=NAVY, spaceBefore=5, spaceAfter=3))
styles.add(ParagraphStyle(name="H2Compact", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=9.5, leading=11, textColor=TEAL, spaceBefore=4, spaceAfter=2))
styles.add(ParagraphStyle(name="BodyCompact", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10, textColor=INK, spaceAfter=3))
styles.add(ParagraphStyle(name="BulletCompact", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=9.6, leftIndent=10, firstLineIndent=-6, textColor=INK, spaceAfter=1.5))
styles.add(ParagraphStyle(name="TableHeadCompact", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.2, leading=8.5, textColor=colors.white))
styles.add(ParagraphStyle(name="TableCellCompact", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.1, leading=8.5, textColor=INK))
styles.add(ParagraphStyle(name="CodeCompact", parent=styles["Code"], fontName="Courier", fontSize=6.5, leading=8, textColor=INK, backColor=LIGHT, borderColor=BORDER, borderWidth=0.4, borderPadding=4))


def P(text: str, style: str = "BodyCompact") -> Paragraph:
    return Paragraph(escape(text), styles[style])


def bullet(text: str) -> Paragraph:
    return Paragraph("- " + escape(text), styles["BulletCompact"])


def make_table(rows, widths):
    data = []
    for ri, row in enumerate(rows):
        style = styles["TableHeadCompact"] if ri == 0 else styles["TableCellCompact"]
        data.append([Paragraph(escape(str(cell)), style) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ]
    for ri in range(2, len(data), 2):
        commands.append(("BACKGROUND", (0, ri), (-1, ri), LIGHT))
    table.setStyle(TableStyle(commands))
    return table


def architecture():
    d = Drawing(510, 150)

    def box(x, y, w, h, title, sub, fill, stroke=BLUE):
        d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=fill, strokeColor=stroke, strokeWidth=0.9))
        d.add(String(x + w / 2, y + h - 14, title, fontName="Helvetica-Bold", fontSize=7.2, fillColor=NAVY, textAnchor="middle"))
        d.add(String(x + w / 2, y + 10, sub, fontName="Helvetica", fontSize=5.8, fillColor=MUTED, textAnchor="middle"))

    def arrow(x1, y1, x2, y2, color=TEAL):
        d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.1))
        if x2 > x1:
            d.add(Line(x2, y2, x2 - 5, y2 + 2.5, strokeColor=color, strokeWidth=1.1))
            d.add(Line(x2, y2, x2 - 5, y2 - 2.5, strokeColor=color, strokeWidth=1.1))
        else:
            d.add(Line(x2, y2, x2 - 2.5, y2 + 5, strokeColor=color, strokeWidth=1.1))
            d.add(Line(x2, y2, x2 + 2.5, y2 + 5, strokeColor=color, strokeWidth=1.1))

    box(10, 98, 110, 35, "React frontend", "submit / status / demo", PALE_BLUE)
    box(200, 98, 115, 35, "FastAPI", "validate + queue", PALE_TEAL)
    box(390, 98, 110, 35, "PostgreSQL", "RUN-* history", colors.HexColor("#FFF5E6"), colors.HexColor("#D58B2A"))
    arrow(120, 115, 200, 115)
    arrow(315, 115, 390, 115)

    box(55, 35, 105, 35, "Redis", "broker + status", colors.HexColor("#F1ECFA"), colors.HexColor("#8055A5"))
    box(205, 35, 105, 35, "Celery worker", "async execution", PALE_TEAL)
    box(355, 35, 105, 35, "LangGraph", "RAG + verify", PALE_BLUE)
    arrow(255, 98, 108, 70)
    arrow(160, 52, 205, 52)
    arrow(310, 52, 355, 52)
    arrow(407, 70, 445, 98)

    d.add(String(80, 10, "Prometheus / Grafana metrics", fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.HexColor("#C95454"), textAnchor="middle"))
    d.add(String(255, 10, "Flower worker view", fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.HexColor("#8055A5"), textAnchor="middle"))
    d.add(String(430, 10, "Jaeger traces", fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.HexColor("#8055A5"), textAnchor="middle"))
    return d


class CleanDoc(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="clean")
        self.addPageTemplates([PageTemplate(id="clean", frames=frame)])


story = []
story += [
    P("Health Insurance Pre-Authorization Desk", "TitleCompact"),
    P("Compact implementation report: architecture, implemented features, and how the working demo operates", "SubCompact"),
    architecture(),
    Spacer(1, 2),
    P("Implemented system", "H1Compact"),
    make_table([
        ["Area", "What was implemented"],
        ["Frontend", "React Submit, Track Status, Live Records, Cataract Demo, result and feedback views."],
        ["Backend", "FastAPI request contract, validation, Run ID creation, async submission, polling, feedback, health, and metrics endpoints."],
        ["Agents", "LangGraph classifier, verifier, retrieval tools, self-verification, retries, timeouts, and escalation for unsupported evidence."],
        ["Async path", "Redis broker/status layer, Celery worker, queue routing, task retries, and Flower task monitoring."],
        ["Storage", "PostgreSQL RUN-* payload/result history and feedback when available; Redis remains the fast live layer and fallback."],
        ["Demo data", "20 seeded DEMO-* records plus 50 manual-only synthetic samples."],
        ["Observability", "Prometheus, Grafana, Jaeger, structured Docker logs, latency, queue, outcome, and error metrics."],
    ], [38 * mm, 140 * mm]),
    P("Request flow", "H2Compact"),
    bullet("User submits synthetic patient, policy, hospital, and medical fields from React."),
    bullet("FastAPI validates schema, ranges, categories, dates, age consistency, and free-text fields."),
    bullet("A RUN-* ID is returned immediately; PostgreSQL receives the pending row when available."),
    bullet("Redis/Celery sends work to the worker; LangGraph retrieves policy clauses and verifies the route."),
    bullet("The worker writes recommendation, citations, steps, token usage, timing, prompt version, and final state."),
    bullet("The frontend polls the status endpoint and displays the cited recommendation and escalation path."),
    P("The same flow supports a Mumbai hospital or any other valid hospital payload: it receives a live RUN-* result without being added to the seeded Live Records dashboard.", "BodyCompact"),
]

story.append(PageBreak())
story += [
    P("What we implemented and how", "H1Compact"),
    P("FastAPI and validation", "H2Compact"),
    P("Pydantic models enforce patient, policy, hospital, and medical contracts before an agent starts. This covers identifier patterns, age/date consistency, policy dates and coverage, ICD-10 format, admission categories, costs, discharge dates, and free-text length. Invalid or suspicious input is rejected or quarantined by the guardrail path.", "BodyCompact"),
    P("Agent reasoning", "H2Compact"),
    make_table([
        ["Stage", "Implementation"],
        ["Classifier", "Identifies admission type and extracts clinical/policy entities for the coverage decision."],
        ["Retriever", "Searches the FAISS policy corpus and can look up clauses and request fields."],
        ["Verifier", "Checks coverage, waiting periods, exclusions, and supporting passages away from the main cover clause."],
        ["Self-verification", "Blocks unsupported results, retries evidence gathering, and escalates when evidence is insufficient."],
    ], [38 * mm, 140 * mm]),
    P("Frontend and demo behavior", "H2Compact"),
    P("The original 20 DEMO-* records are shown in Live Records. The extra 50 samples are entered manually from MANUAL_DEMO_GUIDE.txt, receive RUN-* IDs, and appear on their own status pages rather than in the dashboard. The samples cover emergency, planned, day-care, network, non-network, approval, query, and medical-review routes. The cataract case demonstrates the separate 24-month waiting-period citation and medical-review route.", "BodyCompact"),
    P("Durable run history", "H2Compact"),
    P("The preauth_runs row is created before queueing when PostgreSQL is available. The worker updates pending, processing, completed, or failed state and stores the request payload, route, recommendation, escalation reason, citations, agent steps, token usage, prompt version, timing, and completion time. Feedback is stored in preauth_feedback. If PostgreSQL is unavailable, the request still runs through Redis/Celery and the status endpoint can use the Redis result for its configured cache lifetime.", "BodyCompact"),
    P("Monitoring and performance", "H2Compact"),
    make_table([
        ["Tool", "Working use"],
    ["Prometheus / Grafana", "Throughput, p50/p95 latency, queue depth, error rate, outcomes, tool-call rate, and security events."],
        ["Flower", "Celery workers, active tasks, and task states."],
        ["Jaeger", "OpenTelemetry traces for backend and worker services."],
        ["Docker logs", "Structured request, worker, agent, tool, and error logs on stdout."],
        ["Locust", "Load test with RPS, p50, p95, and error-rate reporting."],
    ], [38 * mm, 140 * mm]),
    P("Run the demonstration", "H2Compact"),
    Preformatted(r"""cd C:\Users\saira\OneDrive\Desktop\MLSDA_mini
docker compose up -d --build
docker compose run --rm corpus-ingest
docker compose exec backend python /app/scripts/seed_demo_data.py
Start-Process http://localhost:3000""", styles["CodeCompact"]),
    Spacer(1, 2),
    P("Open: application http://localhost:3000 | Swagger http://localhost:8000/api/docs | Flower http://localhost:5555 | Grafana http://localhost:3001 | Prometheus http://localhost:9090 | Jaeger http://localhost:16686", "BodyCompact"),
    P("Completed work", "H2Compact"),
    bullet("Added and validated 50 manual synthetic request payloads without expanding the dashboard seed."),
    bullet("Connected live RUN-* persistence and PostgreSQL fallback status lookup."),
    bullet("Added Flower as a worker/task monitoring service and fixed the Grafana Prometheus datasource UID."),
    bullet("Expanded README and manual demo guide with setup, run, stop, metrics, and screenshot guidance."),
    bullet("Kept Track Status available for revisiting RUN-* requests while keeping the dashboard limited to DEMO-* records."),
]

doc = CleanDoc(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=16 * mm,
    rightMargin=16 * mm,
    topMargin=13 * mm,
    bottomMargin=13 * mm,
    title="Health Insurance Pre-Authorization Desk - Compact Implementation Report",
    author="MLSDA Mini Project",
)
doc.build(story)
print(OUTPUT)

