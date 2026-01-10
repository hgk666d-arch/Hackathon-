import os
import re
import docx
from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
from processor import TalentProcessor
from analyzer import SkillProfiler

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

proc = TalentProcessor()
prof = SkillProfiler()

def extract_resume_data(path):
    text = ""
    try:
        if path.lower().endswith('.pdf'):
            reader = PdfReader(path)
            for page in reader.pages:
                text += page.extract_text()
        elif path.lower().endswith('.docx'):
            doc = docx.Document(path)
            text = "\n".join([para.text for para in doc.paragraphs])
        
        github = re.search(r"github\.com/([\w-]+)", text)
        linkedin = re.search(r"linkedin\.com/in/([\w-]+)", text)
        
        # NEW: Extract Years of Experience
        exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience", text, re.IGNORECASE)
        years_exp = int(exp_match.group(1)) if exp_match else 0
        
        return {
            "text": text, 
            "github": github.group(1) if github else None, 
            "linkedin": linkedin.group(0) if linkedin else "Not Found",
            "years_exp": years_exp
        }
    except Exception:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    files = request.files.getlist('resumes')
    jd_text = request.form.get('jd', '')
    mandatory_input = request.form.get('mandatory_skills', '').lower()
    mandatory_skills = [s.strip() for s in mandatory_input.split(',') if s.strip()]
    
    leaderboard = []
    audit = proc.audit_jd(jd_text)

    for file in files:
        if file.filename == '': continue
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        
        # The 'data' variable is defined here for EACH file
        data = extract_resume_data(path)
        if not data: continue

        resume_content = data['text'].lower()
        
        # 1. Mandatory Skill Check
        missing_mandatory = [s for s in mandatory_skills if s not in resume_content]
        mandatory_penalty = len(missing_mandatory) * 25 
        
        # 2. General Skill Gap (40% Weight)
        skill_gap = proc.get_skill_gap(data['text'], jd_text)
        skill_score = max(0, 100 - (len(skill_gap) * 5))

        # 3. Experience Score (20% Weight)
        # Normalize: 10 years = 100 points
        exp_score = min(100, data['years_exp'] * 10)
        
        # 4. Semantic Relevance (20% Weight)
        blinded = proc.redact_pii(data['text'])
        semantic_raw = proc.get_semantic_match(blinded, jd_text)
        semantic_score = float(semantic_raw) * 100
        
        # 5. Verification Bonus (20% Weight)
        github_stats = prof.analyze_github(data['github']) if data['github'] else {}
        verification_bonus = 20 if github_stats.get('repo_count', 0) > 0 else 0

        # --- FINAL SCORE CALCULATION ---
        # Skill(40%) + Exp(20%) + Semantic(20%) + Verification(20%) - Penalty
        final_score = (skill_score * 0.4) + (exp_score * 0.2) + (semantic_score * 0.2) + verification_bonus - mandatory_penalty
        final_score = round(max(0, min(100, final_score)), 2)

        # Generate Prep & Summary
        interview_prep = proc.get_interview_questions(skill_gap)
        tech_keywords = ["python", "java", "react", "aws", "docker", "fastapi", "sql"]
        top_skills = [s for s in tech_keywords if s in resume_content]
        summary = proc.generate_summary(semantic_raw, top_skills, skill_gap)

        leaderboard.append({
            "name": file.filename,
            "score": final_score,
            "years_exp": data['years_exp'], # Added for the UI
            "skill_gap": skill_gap,
            "missing_mandatory": missing_mandatory,
            "interview_prep": interview_prep,
            "summary": summary,
            "github": github_stats,
            "profiles": {"github": data['github'], "linkedin": data['linkedin']}
        })

    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({"audit": audit, "candidates": leaderboard})

if __name__ == '__main__':
    app.run(debug=True)