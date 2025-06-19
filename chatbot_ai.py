import openai
import json
from data_storage import job_storage, candidate_storage
from datetime import datetime

class RADChatbot:
    def __init__(self):
        self.context = self._build_context()
    
    def _build_context(self):
        """Build context with current recruitment data."""
        jobs = job_storage.storage._load_json(job_storage.storage.jobs_file)
        candidates = candidate_storage.storage._load_json(candidate_storage.storage.candidates_file)
        
        # Debug: Print candidates data to see what we have
        print(f"DEBUG: Found {len(candidates)} total candidates")
        for candidate in candidates:
            print(f"DEBUG: Candidate {candidate.get('name')} - Status: {candidate.get('status')} - Shortlisted: {candidate.get('shortlisted')}")
        
        # Count shortlisted candidates - include interview_scheduled as shortlisted
        shortlisted_count = len([c for c in candidates if 
                               c.get('status') == 'shortlisted' or 
                               c.get('shortlisted') == 'yes' or
                               c.get('status') == 'interview_scheduled'])
        print(f"DEBUG: Shortlisted count (including interviews): {shortlisted_count}")
        
        context = {
            "total_jobs": len(jobs),
            "active_jobs": len([j for j in jobs if j.get('status') == 'active']),
            "draft_jobs": len([j for j in jobs if j.get('status') == 'draft']),
            "total_candidates": len(candidates),
            "shortlisted_candidates": shortlisted_count,
            "pending_candidates": len([c for c in candidates if c.get('status') == 'pending_review']),
            "jobs_data": jobs,
            "candidates_data": candidates
        }
        
        # Get top candidates by score
        sorted_candidates = sorted(candidates, key=lambda x: x.get('match_score', 0), reverse=True)
        context["top_candidates"] = sorted_candidates[:5]
        
        return context
    
    def process_message(self, user_message: str) -> str:
        """Process user message with AI and data context."""
        # Always refresh context with latest data
        self.context = self._build_context()
        
        # Force fallback for shortlisted queries to ensure we see the data
        message_lower = user_message.lower()
        if any(word in message_lower for word in ['shortlisted', 'shortlist']):
            return self._fallback_response(user_message)
        
        # Get shortlisted candidates for the prompt
        shortlisted_candidates = [c for c in self.context['candidates_data'] 
                                if c.get('status') == 'shortlisted' or c.get('shortlisted') == 'yes']
        
        print(f"DEBUG: Sending {len(shortlisted_candidates)} shortlisted candidates to AI")
        
        # Create comprehensive system prompt with all data
        system_prompt = f"""
        You are RAD Bot, an AI recruitment assistant with access to real-time recruitment data.
        
        CURRENT RECRUITMENT STATUS:
        - Total Jobs: {self.context['total_jobs']} (Active: {self.context['active_jobs']}, Draft: {self.context['draft_jobs']})
        - Total Candidates: {self.context['total_candidates']}
        - Shortlisted Candidates: {len(shortlisted_candidates)}
        - Pending Review: {self.context['pending_candidates']}
        
        SHORTLISTED CANDIDATES (Status='shortlisted' OR shortlisted='yes'):
        {json.dumps(shortlisted_candidates, indent=2, default=str)}
        
        ALL CANDIDATES DATA:
        {json.dumps(self.context['candidates_data'], indent=2, default=str)}
        
        When asked about shortlisted candidates, use the SHORTLISTED CANDIDATES data above.
        Always provide specific details including names, scores, and job titles.
        If there are shortlisted candidates in the data, show them - don't say there are none.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"AI Error: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback responses if AI is unavailable."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['shortlisted', 'shortlist']):
            # Refresh data before checking
            self.context = self._build_context()
            # Check status, shortlisted field, AND interview_scheduled status
            candidates = [c for c in self.context['candidates_data'] 
                         if c.get('status') == 'shortlisted' or 
                            c.get('shortlisted') == 'yes' or
                            c.get('status') == 'interview_scheduled']
            
            print(f"DEBUG: Fallback found {len(candidates)} shortlisted candidates")
            
            if candidates:
                response = f"📊 You have {len(candidates)} shortlisted candidates:\n\n"
                for candidate in candidates[:5]:
                    job_title = "Unknown Job"
                    for job in self.context['jobs_data']:
                        if job.get('id') == candidate.get('job_id'):
                            job_title = job.get('role_title', 'Unknown Job')
                            break
                    
                    status_display = candidate.get('status', 'unknown')
                    if status_display == 'interview_scheduled':
                        status_display = "Interview Scheduled (Shortlisted)"
                    
                    response += f"• {candidate.get('name', 'Unknown')} - {candidate.get('match_score', 0):.1f}% match\n"
                    response += f"  Job: {job_title}\n"
                    response += f"  Status: {status_display}\n"
                    response += f"  Shortlisted Field: {candidate.get('shortlisted', 'none')}\n"
                    if candidate.get('notes'):
                        recent_note = candidate.get('notes', '').split('\n')[-1][:50]
                        response += f"  Latest Note: {recent_note}...\n"
                    response += "\n"
                if len(candidates) > 5:
                    response += f"... and {len(candidates) - 5} more candidates"
                return response
            else:
                return f"📊 No candidates have been shortlisted yet.\nTotal candidates: {self.context['total_candidates']}\nPending review: {self.context['pending_candidates']}"
        
        elif any(word in message_lower for word in ['jobs', 'posting', 'positions']):
            active_jobs = [j for j in self.context['jobs_data'] if j.get('status') == 'active']
            if active_jobs:
                response = f"You have {len(active_jobs)} active job postings:\n\n"
                for job in active_jobs[:3]:
                    response += f"- {job.get('role_title', 'Unknown')} - {job.get('department', 'Unknown')}\n"
                return response
            else:
                return "No active job postings currently."
        
        elif any(word in message_lower for word in ['pending', 'review']):
            pending = [c for c in self.context['candidates_data'] if c.get('status') == 'pending_review']
            return f"You have {len(pending)} candidates pending review."
        
        elif any(word in message_lower for word in ['top', 'best', 'highest']):
            if self.context['top_candidates']:
                response = "Top candidates by match score:\n\n"
                for i, candidate in enumerate(self.context['top_candidates'][:3], 1):
                    response += f"{i}. {candidate.get('name', 'Unknown')} - {candidate.get('match_score', 0):.1f}%\n"
                return response
            else:
                return "No candidates available yet."
        
        else:
            return f"""I'm RAD Bot, your AI recruitment assistant! Here's what I can help with:

Current Status:
- {self.context['active_jobs']} active jobs
- {self.context['shortlisted_candidates']} shortlisted candidates
- {self.context['pending_candidates']} pending review

Try asking:
- Show me shortlisted candidates
- What are our active jobs?
- Who are the top candidates?
- How many pending reviews?"""

# Initialize the chatbot
rad_chatbot = RADChatbot()
