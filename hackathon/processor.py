from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from sentence_transformers import SentenceTransformer, util
import spacy

class TalentProcessor:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load("en_core_web_lg")

    def get_skill_gap(self, resume_text, jd_text):
        """Identifies missing technical skills by comparing JD and Resume."""
        # Process both texts with spaCy
        doc_jd = self.nlp(jd_text)
        doc_resume = self.nlp(resume_text)

        # Extract 'ORG' (Companies/Tools) and 'PRODUCT' (Languages/Frameworks)
        # We also look for specific technical keywords
        def extract_tech(doc):
            return {token.text.lower() for token in doc if token.pos_ in ['PROPN', 'NOUN'] 
                    and not token.is_stop}

        jd_skills = extract_tech(doc_jd)
        resume_skills = extract_tech(doc_resume)

        # Identify skills in JD but not in Resume
        missing = jd_skills - resume_skills
        
        # Filter for common tech keywords to avoid noise
        tech_keywords = {"python", "java", "react", "aws", "docker", "sql", "fastapi", "c++", "javascript"}
        verified_missing = [skill for skill in missing if skill in tech_keywords]

        return verified_missing

    def redact_pii(self, text):
        """Removes Name, Email, Phone, and Location for Blind Hiring."""
        results = self.analyzer.analyze(text=text, entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"], language='en')
        return self.anonymizer.anonymize(text=text, analyzer_results=results).text

    def get_semantic_match(self, resume_text, jd_text):
        """Uses NLP to recognize transferable skills beyond keywords."""
        embeddings = self.model.encode([resume_text, jd_text], convert_to_tensor=True)
        score = util.pytorch_cos_sim(embeddings[0], embeddings[1])
        return round(float(score), 4)

    def audit_jd(self, jd_text):
        """Checks for non-inclusive language."""
        masculine_terms = ["rockstar", "ninja", "dominant", "competitive"]
        found = [word for word in masculine_terms if word in jd_text.lower()]
        return {"inclusive": len(found) == 0, "flags": found}
    
    def generate_summary(self, score, skills, gaps):
        """Generates a one-sentence AI summary of the candidate's fit."""
        if score > 0.8:
            return f"Strong match with expert proficiency in {', '.join(skills[:2])}."
        elif score > 0.5:
            gap_text = f" but lacks {', '.join(gaps[:2])}" if gaps else ""
            return f"Solid technical background in {', '.join(skills[:2])}{gap_text}."
        else:
            return "Profile does not closely align with the core technical requirements of this role."

    def get_interview_questions(self, gaps):
        """Generates targeted technical questions based on identified skill gaps."""
        # A dictionary of expert-level questions for common tech keywords
        question_bank = {
            "python": "Explain the difference between a list and a tuple. In what scenario is a tuple more efficient?",
            "aws": "How would you ensure high availability and disaster recovery for a web application on AWS?",
            "docker": "What is the difference between an Entrypoint and a Command in a Dockerfile?",
            "react": "Explain the virtual DOM and how React handles reconciliation during state changes.",
            "fastapi": "How does FastAPI leverage Python type hints for data validation and documentation?",
            "sql": "What is an index in a database, and how does it improve query performance? Are there downsides?",
            "java": "Explain the difference between a Checked Exception and an Unchecked Exception in Java."
        }
        
        # Fallback question for less common skills
        return [question_bank.get(skill.lower(), f"Can you describe a challenging project where you successfully implemented {skill}?") for skill in gaps]
        
if __name__ == "__main__":
    # 1. Test PII Redaction (Blind Hiring)
    test_resume = "Contact: John Doe, Email: john.doe@example.com, Phone: 123-456-7890. Experience at Google."
    print("--- Testing Redaction ---")
    # Change 'redact_function' to the actual name of your redaction function
    # redacted = redact_pii(test_resume) 
    # print(f"Result: {redacted}")

    # 2. Test Semantic Matching
    print("\n--- Testing Semantic Matching ---")
    job_desc = "Looking for a Python developer with AI experience."
    candidate_skills = "Expert in Python programming and machine learning models."
    # Change 'match_function' to the actual name of your similarity function
    # score = calculate_similarity(job_desc, candidate_skills)
    # print(f"Match Score: {score}")