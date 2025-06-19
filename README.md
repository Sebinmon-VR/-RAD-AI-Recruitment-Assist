# RAD - AI-Powered Recruitment Assistant

An intelligent recruitment chatbot system that automates CV screening, candidate shortlisting, and provides AI-powered insights for hiring decisions.

## 🚀 Features

### 1. AI-Powered Job Description Generation
- Create comprehensive JDs using OpenAI GPT
- Set minimum score thresholds for auto-shortlisting
- Role-based skill matching

### 2. Automated CV Analysis & Shortlisting
- Upload multiple CVs (PDF, DOC, DOCX)
- AI extracts candidate information and skills
- Automatic scoring and shortlisting based on job requirements
- Match score calculation using AI

### 3. Intelligent RAD Bot
- Real-time AI chatbot with access to all recruitment data
- Natural language queries about candidates and jobs
- Shortlisted candidate insights and recommendations

### 4. Candidate Management
- Detailed candidate profiles with AI analysis
- Status tracking (Pending → Shortlisted → Interview → Hired)
- Notes system with timestamps
- Action buttons for workflow management

### 5. Real-time Dashboard
- Active jobs and candidate statistics
- Quick access to all recruitment functions
- Job listings with candidate counts

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **AI**: OpenAI GPT-4/3.5-turbo for CV analysis and chatbot
- **Data Storage**: File-based JSON storage
- **PDF Processing**: PyPDF2, pdfplumber
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Environment**: python-dotenv for configuration

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/RAD-AI-Recruitment-Assist.git
   cd RAD-AI-Recruitment-Assist
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   SECRET_KEY=your-secret-key
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the application:**
   - Open http://localhost:5000 in your browser
   - Start creating jobs and uploading CVs!

## 🔧 Configuration

### Environment Variables (.env)
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
```

### OpenAI API Key
Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## 🎯 Usage

1. **Create Job Description**: Use AI to generate comprehensive JDs
2. **Upload CVs**: Bulk upload candidate CVs for analysis
3. **Review Candidates**: AI automatically scores and shortlists candidates
4. **Chat with RAD Bot**: Ask questions about your recruitment data
5. **Manage Pipeline**: Track candidates through interview stages

## 📊 Data Structure

The system uses file-based storage with JSON files:
- `data/jobs.json` - Job descriptions and requirements
- `data/candidates.json` - Candidate profiles and analysis
- `uploads/` - CV file storage

## 🤖 RAD Bot Commands

Try these queries with the AI chatbot:
- "Show me shortlisted candidates"
- "What are our active jobs?"
- "Who are the top candidates?"
- "Give me recruitment insights"
- "What needs my attention?"

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set `FLASK_ENV=production` in .env
2. Use a proper WSGI server like Gunicorn
3. Configure proper secret keys
4. Set up file backups for data persistence

## 📁 Project Structure

```
RAD-AI-Recruitment-Assist/
├── app.py                 # Main Flask application
├── data_storage.py        # File-based data management
├── ai_services.py         # OpenAI integration
├── chatbot_ai.py         # AI chatbot functionality
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
├── templates/           # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── create_jd.html
│   ├── view_jd.html
│   ├── jobs_list.html
│   ├── view_candidate.html
│   ├── upload_candidates.html
│   └── chatbot.html
├── static/              # CSS, JS, images
│   ├── css/
│   └── js/
├── data/                # JSON data files
├── uploads/             # CV file storage
└── README.md           # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the debug endpoint: `/debug/data`
2. Review the console logs
3. Ensure OpenAI API key is valid
4. Verify file permissions for data storage

## 🔮 Future Enhancements

- Database integration (PostgreSQL/MongoDB)
- Email notifications
- Interview scheduling integration
- Advanced analytics dashboard
- Multi-tenant support
- API endpoints for external integrations

## 🔒 Security Notes

**IMPORTANT**: Never commit sensitive information to version control!

### Before pushing to GitHub:
1. **Check .env file**: Ensure `.env` file is in `.gitignore` and not tracked
2. **Verify API keys**: Make sure no real API keys are in any tracked files
3. **Secret key**: Generate a secure secret key for production

### Generate secure keys:
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Check for accidentally committed secrets
git log --grep="key\|password\|secret" --oneline
```

### Environment Setup:
- Copy `.env.example` to `.env`
- Add your actual API keys to `.env` (not tracked by git)
- Never share your `.env` file
