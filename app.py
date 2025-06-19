from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import openai
from datetime import datetime
from data_storage import job_storage, candidate_storage
from ai_services import analyze_cv, generate_jd, calculate_match_score
from utils import allowed_file, extract_text_from_pdf
from chatbot_ai import rad_chatbot
import json

# Clear existing environment variables first
for key in ['FLASK_APP', 'FLASK_ENV', 'SECRET_KEY', 'OPENAI_API_KEY']:
    if key in os.environ:
        del os.environ[key]

# Load environment variables from .env file only
load_dotenv(override=True)

app = Flask(__name__)

# Get configuration from .env file only
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise ValueError("SECRET_KEY not found in .env file")

openai_key = os.getenv('OPENAI_API_KEY') 
if not openai_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

app.config['SECRET_KEY'] = secret_key
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))

# Initialize OpenAI with key from .env file
openai.api_key = openai_key

print(f"Loaded SECRET_KEY from .env: {secret_key[:10]}...")
print(f"Loaded OPENAI_API_KEY from .env: {openai_key[:10]}...")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def dashboard():
    active_jobs = job_storage.count_by_status('active')
    pending_candidates = candidate_storage.count_by_status('pending_review')
    return render_template('dashboard.html', active_jobs=active_jobs, pending_candidates=pending_candidates)

@app.route('/jd/create', methods=['GET', 'POST'])
def create_jd():
    if request.method == 'POST':
        role_title = request.form.get('role_title')
        department = request.form.get('department')
        seniority = request.form.get('seniority')
        skills = request.form.get('skills')
        min_score = float(request.form.get('min_score', 70))
        
        # Generate JD using AI
        generated_jd = generate_jd(role_title, department, seniority, skills)
        
        jd = job_storage.create(
            role_title=role_title,
            department=department,
            seniority_level=seniority,
            required_skills=skills,
            description=generated_jd,
            min_score=min_score,
            status='draft'
        )
        
        flash('Job Description created successfully!', 'success')
        return redirect(url_for('view_jd', jd_id=jd['id']))
    
    return render_template('create_jd.html')

@app.route('/jd/<int:jd_id>')
def view_jd(jd_id):
    jd = job_storage.get_by_id(jd_id)
    if not jd:
        flash('Job Description not found', 'error')
        return redirect(url_for('dashboard'))
    
    candidates = candidate_storage.filter_by(job_id=jd_id)
    return render_template('view_jd.html', jd=jd, candidates=candidates)

@app.route('/candidates/upload/<int:jd_id>', methods=['GET', 'POST'])
def upload_candidates(jd_id):
    jd = job_storage.get_by_id(jd_id)
    if not jd:
        flash('Job Description not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if 'cv_files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('cv_files')
        processed_count = 0
        shortlisted_count = 0
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract text and analyze CV
                cv_text = extract_text_from_pdf(filepath)
                analysis = analyze_cv(cv_text, jd['description'])
                match_score = calculate_match_score(cv_text, jd['required_skills'])
                
                # Auto-shortlist based on minimum score
                min_score = jd.get('min_score', 70)
                status = 'shortlisted' if match_score >= min_score else 'pending_review'
                shortlisted_value = 'yes' if match_score >= min_score else 'none'
                
                if status == 'shortlisted':
                    shortlisted_count += 1
                
                candidate_storage.create(
                    name=analysis.get('name', 'Unknown'),
                    email=analysis.get('email', ''),
                    phone=analysis.get('phone', ''),
                    cv_path=filepath,
                    job_id=jd_id,
                    match_score=match_score,
                    ai_analysis=str(analysis),
                    status=status,
                    shortlisted=shortlisted_value,
                    notes=''
                )
                processed_count += 1
        
        flash(f'{processed_count} CVs processed. {shortlisted_count} automatically shortlisted (score ≥ {min_score}%)', 'success')
        return redirect(url_for('view_jd', jd_id=jd_id))
    
    return render_template('upload_candidates.html', jd=jd)

@app.route('/candidates/<int:candidate_id>')
def view_candidate(candidate_id):
    candidate = candidate_storage.get_by_id(candidate_id)
    if not candidate:
        flash('Candidate not found', 'error')
        return redirect(url_for('dashboard'))
    return render_template('view_candidate.html', candidate=candidate)

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    user_message = request.json.get('message')
    response = rad_chatbot.process_message(user_message)
    return jsonify({'response': response})

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/jobs')
def jobs_list():
    jobs = job_storage.filter_by()
    return render_template('jobs_list.html', jobs=jobs)

@app.route('/jd/<int:jd_id>/activate')
def activate_job(jd_id):
    jobs = job_storage.storage._load_json(job_storage.storage.jobs_file)
    for job in jobs:
        if job['id'] == jd_id:
            job['status'] = 'active'
            job['updated_at'] = datetime.utcnow().isoformat()
            break
    job_storage.storage._save_json(job_storage.storage.jobs_file, jobs)
    flash('Job activated successfully!', 'success')
    return redirect(url_for('view_jd', jd_id=jd_id))

@app.route('/candidates/<int:candidate_id>/shortlist')
def shortlist_candidate(candidate_id):
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    for candidate in candidates:
        if candidate['id'] == candidate_id:
            candidate['status'] = 'shortlisted'
            candidate['shortlisted'] = 'yes'  # Update shortlisted field
            break
    candidate_storage.storage._save_json(candidate_storage.storage.candidates_file, candidates)
    flash('Candidate shortlisted successfully!', 'success')
    return redirect(url_for('view_candidate', candidate_id=candidate_id))

@app.route('/candidates/<int:candidate_id>/reject')
def reject_candidate(candidate_id):
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    for candidate in candidates:
        if candidate['id'] == candidate_id:
            candidate['status'] = 'rejected'
            candidate['shortlisted'] = 'none'  # Reset shortlisted field
            break
    candidate_storage.storage._save_json(candidate_storage.storage.candidates_file, candidates)
    flash('Candidate rejected.', 'info')
    return redirect(url_for('view_candidate', candidate_id=candidate_id))

@app.route('/candidates/<int:candidate_id>/add_note', methods=['POST'])
def add_note(candidate_id):
    note = request.form.get('note')
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    for candidate in candidates:
        if candidate['id'] == candidate_id:
            existing_notes = candidate.get('notes', '')
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            new_note = f"[{timestamp}] {note}"
            candidate['notes'] = f"{existing_notes}\n{new_note}" if existing_notes else new_note
            break
    candidate_storage.storage._save_json(candidate_storage.storage.candidates_file, candidates)
    flash('Note added successfully!', 'success')
    return redirect(url_for('view_candidate', candidate_id=candidate_id))

@app.route('/candidates/<int:candidate_id>/schedule')
def schedule_interview(candidate_id):
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    for candidate in candidates:
        if candidate['id'] == candidate_id:
            candidate['status'] = 'interview_scheduled'
            candidate['shortlisted'] = 'yes'  # Mark as shortlisted when interview is scheduled
            break
    candidate_storage.storage._save_json(candidate_storage.storage.candidates_file, candidates)
    flash('Interview scheduled!', 'success')
    return redirect(url_for('view_candidate', candidate_id=candidate_id))

@app.route('/debug/data')
def debug_data():
    """Debug endpoint to see actual data in files"""
    jobs = job_storage.storage._load_json(job_storage.storage.jobs_file)
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    
    debug_info = {
        "jobs_count": len(jobs),
        "candidates_count": len(candidates),
        "jobs": jobs,
        "candidates": candidates,
        "shortlisted_by_status": [c for c in candidates if c.get('status') == 'shortlisted'],
        "shortlisted_by_field": [c for c in candidates if c.get('shortlisted') == 'yes'],
        "interview_scheduled": [c for c in candidates if c.get('status') == 'interview_scheduled']
    }
    
    return f"<pre>{json.dumps(debug_info, indent=2, default=str)}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
