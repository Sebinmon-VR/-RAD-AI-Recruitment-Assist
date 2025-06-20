from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory, abort
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import openai
from datetime import datetime
from data_storage import job_storage, candidate_storage
from ai_services import analyze_cv, generate_jd, calculate_match_score, calculate_ats_score
from utils import allowed_file, extract_text_from_pdf, get_ats_tips
from chatbot_ai import rad_chatbot
import json
import uuid

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

@app.context_processor
def inject_now():
    return {'current_year': datetime.utcnow().year}

@app.route('/')
def dashboard():
    active_jobs = job_storage.count_by_status('active')
    pending_candidates = candidate_storage.count_by_status('pending_review')
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    shortlisted_count = len([c for c in candidates if c.get('status') == 'shortlisted' or c.get('status') == 'interview_scheduled'])
    in_process_count = len([c for c in candidates if c.get('status') == 'interview_scheduled'])

    # Tracking counts
    new_applications = len([c for c in candidates if c.get('status') in ['pending_review', 'new', None, '']])
    in_review = len([c for c in candidates if c.get('status') == 'in_review'])
    shortlisted = len([c for c in candidates if c.get('status') == 'shortlisted'])
    in_process = len([c for c in candidates if c.get('status') == 'interview_scheduled'])
    rejected = len([c for c in candidates if c.get('status') == 'rejected'])

    # Collect recent activities from jobs and candidates
    activities = []
    jobs = job_storage.storage._load_json(job_storage.storage.jobs_file)
    for job in jobs:
        activities.append({
            "type": "job",
            "id": job.get("id"),
            "title": job.get("role_title"),
            "status": job.get("status"),
            "updated_at": job.get("updated_at", job.get("created_at")),
            "desc": f"Job '{job.get('role_title')}' ({job.get('status')})"
        })
    for c in candidates:
        activities.append({
            "type": "candidate",
            "id": c.get("id"),
            "name": c.get("name"),
            "status": c.get("status"),
            "updated_at": c.get("updated_at", c.get("created_at")),
            "desc": f"Candidate '{c.get('name')}' ({c.get('status')})"
        })
    # Sort by updated_at descending
    activities = sorted(
        activities,
        key=lambda x: x.get("updated_at") or "",
        reverse=True
    )
    recent_activities = activities[:10]

    # Real-time tracking data
    job_tracking = []
    for job in jobs:
        job_id = job.get("id")
        job_candidates = [c for c in candidates if c.get("job_id") == job_id]
        job_tracking.append({
            "id": job_id,
            "title": job.get("role_title"),
            "status": job.get("status"),
            "openings": job.get("openings", 1),
            "applications": len(job_candidates),
            "shortlisted": len([c for c in job_candidates if c.get("status") == "shortlisted"]),
            "interviewed": len([c for c in job_candidates if c.get("status") == "interview_scheduled"]),
            "hired": len([c for c in job_candidates if c.get("status") == "hired"]),
        })

    return render_template(
        'dashboard.html',
        active_jobs=active_jobs,
        pending_candidates=pending_candidates,
        shortlisted_count=shortlisted_count,
        in_process_count=in_process_count,
        recent_activities=recent_activities,
        job_tracking=job_tracking,
        new_applications=new_applications,
        in_review=in_review,
        shortlisted=shortlisted,
        in_process=in_process,
        rejected=rejected,
    )

@app.route('/jd/create', methods=['GET', 'POST'])
def create_jd():
    if request.method == 'POST':
        role_title = request.form.get('role_title')
        department = request.form.get('department')
        seniority = request.form.get('seniority')
        skills = request.form.get('skills')
        min_score = float(request.form.get('min_score', 70))
        openings = int(request.form.get('openings', 1))
        
        # Generate JD using AI
        generated_jd = generate_jd(role_title, department, seniority, skills)
        
        jd = job_storage.create(
            role_title=role_title,
            department=department,
            seniority_level=seniority,
            required_skills=skills,
            description=generated_jd,
            min_score=min_score,
            openings=openings,
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
                ats_score = calculate_ats_score(cv_text, jd['description'])
                ats_tips = get_ats_tips(ats_score)
                
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
                    ats_score=ats_score,
                    ats_tips=ats_tips,
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

@app.route('/candidates/<int:candidate_id>/create_interview_link')
def create_interview_link(candidate_id):
    candidate = candidate_storage.get_by_id(candidate_id)
    if not candidate:
        flash('Candidate not found', 'error')
        return redirect(url_for('dashboard'))
    # Generate a unique meeting ID (could be stored in candidate data for persistence)
    meeting_id = f"interview_{candidate_id}_{uuid.uuid4().hex[:8]}"
    meeting_url = url_for('interview_meeting', meeting_id=meeting_id, _external=True)
    flash(f"Share this link with the candidate: {meeting_url}", "info")
    return redirect(url_for('view_candidate', candidate_id=candidate_id))

@app.route('/api/upload_interview_video', methods=['POST'])
def upload_interview_video():
    video = request.files.get('video')
    candidate_id = request.form.get('candidate_id')
    if not video or not candidate_id:
        return jsonify({'success': False, 'error': 'Missing video or candidate_id'}), 400

    # Save video to a dedicated folder
    video_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'interview_videos')
    os.makedirs(video_folder, exist_ok=True)
    filename = f"interview_{candidate_id}.webm"
    filepath = os.path.join(video_folder, filename)
    video.save(filepath)

    # Update candidate record with video path
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    for candidate in candidates:
        if str(candidate['id']) == str(candidate_id):
            candidate['interview_video'] = f"interview_videos/{filename}"
            break
    candidate_storage.storage._save_json(candidate_storage.storage.candidates_file, candidates)

    return jsonify({'success': True, 'filepath': f"interview_videos/{filename}"})

@app.route('/uploads/interview_videos/<filename>')
def serve_interview_video(filename):
    video_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'interview_videos')
    return send_from_directory(video_folder, filename)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Always serve from the absolute path of the uploads directory
    uploads_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
    # Print debug info to check the actual path and file existence
    print("Serving file:", filename)
    print("Uploads dir:", uploads_dir)
    full_path = os.path.join(uploads_dir, filename)
    print("Full path:", full_path)
    if not os.path.isfile(full_path):
        print("File does not exist!")
    try:
        return send_from_directory(uploads_dir, filename)
    except Exception as e:
        print("Error serving file:", e)
        abort(404)

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

@app.route('/interview/<meeting_id>')
def interview_meeting(meeting_id):
    # You can add authentication/authorization here
    return render_template('interview_meeting.html', meeting_id=meeting_id)

@app.route('/jobs/<int:job_id>/update_status/<status>', methods=['POST'])
def update_job_status(job_id, status):
    jobs = job_storage.storage._load_json(job_storage.storage.jobs_file)
    for job in jobs:
        if job['id'] == job_id:
            job['status'] = status
            job['updated_at'] = datetime.utcnow().isoformat()
            break
    job_storage.storage._save_json(job_storage.storage.jobs_file, jobs)
    flash(f"Job status updated to {status.replace('_', ' ').capitalize()}!", "success")
    return redirect(url_for('dashboard'))

@app.route('/candidates/<int:candidate_id>/update_status/<status>', methods=['POST'])
def update_candidate_status(candidate_id, status):
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    for candidate in candidates:
        if candidate['id'] == candidate_id:
            candidate['status'] = status
            candidate['updated_at'] = datetime.utcnow().isoformat()
            break
    candidate_storage.storage._save_json(candidate_storage.storage.candidates_file, candidates)
    flash(f"Candidate status updated to {status.replace('_', ' ').capitalize()}!", "success")
    return redirect(url_for('view_candidate', candidate_id=candidate_id))

@app.route('/api/tracking')
def api_tracking():
    jobs = job_storage.storage._load_json(job_storage.storage.jobs_file)
    candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
    tracking = []

    for job in jobs:
        job_id = job.get("id")
        job_candidates = [c for c in candidates if c.get("job_id") == job_id]
        tracking.append({
            "job_id": job_id,
            "job_title": job.get("role_title"),
            "job_status": job.get("status"),
            "openings": job.get("openings", 1),
            "applications": len(job_candidates),
            "candidates": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "status": c.get("status"),
                    "interview_scheduled": c.get("status") == "interview_scheduled",
                    "hired": c.get("status") == "hired",
                    "rejected": c.get("status") == "rejected",
                    "waiting_list": c.get("status") == "waiting_list",
                    "offer_letter": c.get("offer_letter", False),
                    "offer_accepted": c.get("offer_accepted", False),
                    "onboarding_complete": c.get("onboarding_complete", False),
                    "probation_status": c.get("probation_status", "not_started"),
                    "updated_at": c.get("updated_at", c.get("created_at"))
                }
                for c in job_candidates
            ]
        })
    return jsonify({"tracking": tracking})

if __name__ == '__main__':
    app.run(debug=True)
