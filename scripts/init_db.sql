-- ═══════════════════════════════════════════════════════════
--  Pre-Authorization Desk — PostgreSQL Init Script
--  Run automatically on first container start
-- ═══════════════════════════════════════════════════════════

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Runs table
CREATE TABLE IF NOT EXISTS preauth_runs (
    id                  VARCHAR(64)  PRIMARY KEY,
    request_id          VARCHAR(64)  NOT NULL,
    correlation_id      VARCHAR(64),
    status              VARCHAR(20)  NOT NULL DEFAULT 'pending',
    outcome             VARCHAR(30),
    recommendation      TEXT,
    escalation_reason   TEXT,
    admission_type      VARCHAR(30),
    prompt_version      VARCHAR(10)  NOT NULL DEFAULT 'v1',
    processing_time_ms  FLOAT,
    citations           JSONB        DEFAULT '[]',
    agent_steps         JSONB        DEFAULT '[]',
    token_usage         JSONB        DEFAULT '{}',
    request_payload     JSONB,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_runs_request_id  ON preauth_runs(request_id);
CREATE INDEX IF NOT EXISTS idx_runs_status      ON preauth_runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_outcome     ON preauth_runs(outcome);
CREATE INDEX IF NOT EXISTS idx_runs_created_at  ON preauth_runs(created_at DESC);

-- Feedback table
CREATE TABLE IF NOT EXISTS preauth_feedback (
    id              SERIAL       PRIMARY KEY,
    run_id          VARCHAR(64)  NOT NULL REFERENCES preauth_runs(id) ON DELETE CASCADE,
    satisfactory    BOOLEAN      NOT NULL,
    reason          TEXT,
    reviewer_id     VARCHAR(100),
    submitted_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_run_id ON preauth_feedback(run_id);

-- Quarantine table
CREATE TABLE IF NOT EXISTS preauth_quarantine (
    id                  SERIAL       PRIMARY KEY,
    request_id          VARCHAR(64)  NOT NULL,
    correlation_id      VARCHAR(64),
    validation_errors   JSONB        NOT NULL,
    raw_payload         JSONB,
    quarantined_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quarantine_request_id ON preauth_quarantine(request_id);

-- Evaluation results table
CREATE TABLE IF NOT EXISTS eval_results (
    id                  SERIAL       PRIMARY KEY,
    scenario_id         VARCHAR(64)  NOT NULL,
    prompt_version      VARCHAR(10)  NOT NULL,
    expected_outcome    VARCHAR(30)  NOT NULL,
    actual_outcome      VARCHAR(30),
    passed              BOOLEAN,
    citation_match      BOOLEAN,
    groundedness        FLOAT,
    faithfulness        FLOAT,
    context_relevance   FLOAT,
    processing_time_ms  FLOAT,
    evaluated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eval_scenario_id ON eval_results(scenario_id);
CREATE INDEX IF NOT EXISTS idx_eval_prompt_ver  ON eval_results(prompt_version);

-- Demo data view
CREATE OR REPLACE VIEW v_run_summary AS
SELECT
    r.id              AS run_id,
    r.status,
    r.outcome,
    r.admission_type,
    r.prompt_version,
    r.processing_time_ms,
    r.created_at,
    (r.token_usage->>'total_tokens')::INT AS total_tokens,
    (r.token_usage->>'estimated_cost_usd')::FLOAT AS cost_usd,
    f.satisfactory    AS feedback_satisfactory
FROM preauth_runs r
LEFT JOIN preauth_feedback f ON f.run_id = r.id
ORDER BY r.created_at DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO preauth_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO preauth_user;
