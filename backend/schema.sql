-- SentinelSIF Raw PostgreSQL Database Schema
-- SIF (Serious Injury & Fatality) Precursor Detection System

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL, -- e.g. "worker", "supervisor", "admin"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    report_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    department VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    hazard_type VARCHAR(255) DEFAULT NULL, -- Filled in later by NLP classifier
    severity VARCHAR(100) DEFAULT NULL,    -- Filled in later
    risk_score DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indices for common query performance
CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(date);
CREATE INDEX IF NOT EXISTS idx_reports_department ON reports(department);
CREATE INDEX IF NOT EXISTS idx_reports_hazard_type ON reports(hazard_type);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
