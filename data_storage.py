import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class DataStorage:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.jobs_file = os.path.join(data_dir, 'jobs.json')
        self.candidates_file = os.path.join(data_dir, 'candidates.json')
        self.interviews_file = os.path.join(data_dir, 'interviews.json')
    
    def _load_json(self, filepath: str) -> List[Dict]:
        """Load JSON data from file."""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_json(self, filepath: str, data: List[Dict]):
        """Save JSON data to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _get_next_id(self, data: List[Dict]) -> int:
        """Get next ID for new record."""
        if not data:
            return 1
        return max(item.get('id', 0) for item in data) + 1

# Job Description operations
class JobStorage:
    def __init__(self, storage: DataStorage):
        self.storage = storage
    
    def create(self, **kwargs) -> Dict:
        """Create new job description."""
        jobs = self.storage._load_json(self.storage.jobs_file)
        new_job = {
            'id': self.storage._get_next_id(jobs),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        jobs.append(new_job)
        self.storage._save_json(self.storage.jobs_file, jobs)
        return new_job
    
    def get_by_id(self, job_id: int) -> Optional[Dict]:
        """Get job by ID."""
        jobs = self.storage._load_json(self.storage.jobs_file)
        return next((job for job in jobs if job['id'] == job_id), None)
    
    def filter_by(self, **kwargs) -> List[Dict]:
        """Filter jobs by criteria."""
        jobs = self.storage._load_json(self.storage.jobs_file)
        filtered = jobs
        for key, value in kwargs.items():
            filtered = [job for job in filtered if job.get(key) == value]
        return filtered
    
    def count_by_status(self, status: str) -> int:
        """Count jobs by status."""
        return len(self.filter_by(status=status))

# Candidate operations
class CandidateStorage:
    def __init__(self, storage: DataStorage):
        self.storage = storage
    
    def create(self, **kwargs) -> Dict:
        """Create new candidate."""
        candidates = self.storage._load_json(self.storage.candidates_file)
        new_candidate = {
            'id': self.storage._get_next_id(candidates),
            'created_at': datetime.utcnow().isoformat(),
            'shortlisted': 'none',  # New field: 'none', 'yes'
            'notes': '',  # New field for notes
            **kwargs
        }
        candidates.append(new_candidate)
        self.storage._save_json(self.storage.candidates_file, candidates)
        return new_candidate
    
    def get_by_id(self, candidate_id: int) -> Optional[Dict]:
        """Get candidate by ID."""
        candidates = self.storage._load_json(self.storage.candidates_file)
        return next((c for c in candidates if c['id'] == candidate_id), None)
    
    def filter_by(self, **kwargs) -> List[Dict]:
        """Filter candidates by criteria."""
        candidates = self.storage._load_json(self.storage.candidates_file)
        filtered = candidates
        for key, value in kwargs.items():
            filtered = [c for c in filtered if c.get(key) == value]
        return filtered
    
    def count_by_status(self, status: str) -> int:
        """Count candidates by status."""
        return len(self.filter_by(status=status))

# Initialize storage instances
storage = DataStorage()
job_storage = JobStorage(storage)
candidate_storage = CandidateStorage(storage)
