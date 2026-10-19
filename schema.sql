-- ====================================================================
-- AI Interview Preparation Platform - SQLite Database Schema
-- ====================================================================

PRAGMA foreign_keys = ON;

-- 1. Users Table (Candidates & Admins)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    phone TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'candidate' CHECK(role IN ('candidate', 'admin')),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Question Bank Table
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL CHECK(domain IN ('Software Engineering', 'Data Science', 'Web Development', 'HR/Behavioral')),
    difficulty TEXT NOT NULL CHECK(difficulty IN ('Junior', 'Mid', 'Senior')),
    question_text TEXT NOT NULL,
    expected_keywords TEXT NOT NULL, -- comma-separated keywords
    model_answer TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Interview Sessions Table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    domain TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    total_questions INTEGER NOT NULL DEFAULT 5,
    overall_score REAL DEFAULT 0.0,
    technical_score REAL DEFAULT 0.0,
    clarity_score REAL DEFAULT 0.0,
    completeness_score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'completed' CHECK(status IN ('in_progress', 'completed', 'abandoned')),
    duration_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Session Answers & Evaluation Detail Table
CREATE TABLE IF NOT EXISTS session_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    user_answer TEXT NOT NULL,
    technical_score REAL NOT NULL DEFAULT 0.0,
    clarity_score REAL NOT NULL DEFAULT 0.0,
    completeness_score REAL DEFAULT 0.0,
    overall_score REAL NOT NULL DEFAULT 0.0,
    feedback TEXT NOT NULL,
    strengths TEXT,
    improvements TEXT,
    matched_keywords TEXT,
    missing_keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Indexes for optimal lookup performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_questions_domain_difficulty ON questions(domain, difficulty, is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_session_answers_session ON session_answers(session_id);
