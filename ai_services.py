import openai
import json
import re
import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file only
load_dotenv(override=True)

# Set OpenAI API key from .env file
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    openai.api_key = openai_key

def generate_jd(role_title: str, department: str, seniority: str, skills: str) -> str:
    """Generate job description using OpenAI GPT."""
    prompt = f"""
    Create a comprehensive job description for the following role:
    
    Role Title: {role_title}
    Department: {department}
    Seniority Level: {seniority}
    Required Skills: {skills}
    
    Include:
    - Role overview
    - Key responsibilities
    - Required qualifications
    - Preferred qualifications
    - What we offer
    
    Make it professional and engaging.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating JD: {str(e)}"

def analyze_cv(cv_text: str, jd_text: str) -> Dict:
    """Analyze CV using OpenAI and extract key information."""
    prompt = f"""
    Analyze the following CV and extract key information:
    
    CV Text: {cv_text}
    
    Job Description: {jd_text}
    
    Extract and return a JSON object with:
    - name
    - email
    - phone
    - skills (list)
    - experience_years
    - education
    - strengths (based on JD match)
    - gaps (skills missing from JD)
    - summary
    
    Return only valid JSON.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        # Try to parse JSON from response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Extract JSON from response if wrapped in text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Could not parse AI response"}
                
    except Exception as e:
        return {"error": f"Error analyzing CV: {str(e)}"}

def calculate_match_score(cv_text: str, required_skills: str) -> float:
    """Calculate match score between CV and required skills."""
    prompt = f"""
    Rate the match between this CV and required skills on a scale of 0-100:
    
    CV: {cv_text[:2000]}...
    Required Skills: {required_skills}
    
    Consider:
    - Skill overlap
    - Experience relevance
    - Education match
    
    Return only a number between 0-100.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )
        
        score_text = response.choices[0].message.content.strip()
        # Extract number from response
        score_match = re.search(r'\d+', score_text)
        if score_match:
            score = float(score_match.group())
            return min(max(score, 0), 100)  # Ensure 0-100 range
        
        return 0.0
    except Exception as e:
        print(f"Error calculating match score: {str(e)}")
        return 0.0
    except Exception as e:
        print(f"Error calculating match score: {str(e)}")
        return 0.0
        print(f"Error calculating match score: {str(e)}")
        return 0.0

def calculate_ats_score(cv_text: str, jd_text: str) -> float:
    """Calculate ATS compatibility score for a CV against a job description."""
    prompt = f"""
    Analyze this CV for ATS (Applicant Tracking System) compatibility.
    Rate on a scale of 0-100 how well this CV would perform in automated ATS screening systems.
    
    Consider:
    - Keyword matching with job description
    - CV formatting and structure
    - Use of industry-standard terms
    - Absence of unusual formatting or tables
    - Proper section headings
    
    CV: {cv_text[:3000]}...
    
    Job Description: {jd_text[:1000]}...
    
    Return only a number between 0-100.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )
        
        score_text = response.choices[0].message.content.strip()
        # Extract number from response
        score_match = re.search(r'\d+', score_text)
        if score_match:
            score = float(score_match.group())
            return min(max(score, 0), 100)  # Ensure 0-100 range
        
        return 0.0
    except Exception as e:
        print(f"Error calculating ATS score: {str(e)}")
        return 0.0
