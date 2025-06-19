from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class JobDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    seniority_level = db.Column(db.String(50), nullable=False)
    required_skills = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, active, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    candidates = db.relationship('Candidate', backref='job', lazy=True)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    cv_path = db.Column(db.String(500), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_description.id'), nullable=False)
    match_score = db.Column(db.Float, default=0.0)
    ai_analysis = db.Column(db.Text)
    status = db.Column(db.String(30), default='pending_review')  # pending_review, shortlisted, rejected, interviewed, hired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    interview_stages = db.relationship('InterviewStage', backref='candidate', lazy=True)

class InterviewStage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    stage_name = db.Column(db.String(100), nullable=False)  # technical, hr, final
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, passed, failed
    scheduled_date = db.Column(db.DateTime)
    feedback = db.Column(db.Text)
    interviewer = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
