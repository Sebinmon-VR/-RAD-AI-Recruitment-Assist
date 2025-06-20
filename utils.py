import os
import PyPDF2
import pdfplumber
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    """Extract text from PDF file."""
    try:
        with pdfplumber.open(filepath) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        # Fallback to PyPDF2
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e2:
            return f"Error extracting text: {str(e2)}"

def ensure_upload_directory():
    """Ensure upload directory exists."""
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
def get_ats_tips(score):
    """Get ATS improvement tips based on score."""
    if score >= 90:
        return "Excellent ATS compatibility. No changes needed."
    elif score >= 70:
        return "Good ATS compatibility. Consider adding a few more role-specific keywords."
    elif score >= 50:
        return "Average ATS compatibility. Consider using a simpler format and adding more industry standard terms."
    else:
        return "Low ATS compatibility. Consider reformatting with simple sections, standard headers, and more keywords."
