from flask import Flask, render_template, request, jsonify
from processor import TalentProcessor
from analyzer import SkillProfiler

app = Flask(__name__)

# Load models once to keep the UI snappy
proc = TalentProcessor()
prof = SkillProfiler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    jd_text = data.get('jd', '')
    resume_text = data.get('resume', '')
    github_handle = data.get('github', '')

    # 1. Run the Logic
    audit_results = proc.audit_jd(jd_text)
    blinded_resume = proc.redact_pii(resume_text)
    match_score = proc.get_semantic_match(blinded_resume, jd_text)
    
    # 2. Skill Profiling (Default to octocat if empty for demo)
    github_data = prof.analyze_github(github_handle if github_handle else "octocat")

    return jsonify({
        "audit": audit_results,
        "blinded": blinded_resume,
        "score": round(float(match_score) * 100, 2), # Convert to percentage
        "github": github_data
    })

if __name__ == '__main__':
    app.run(debug=True)