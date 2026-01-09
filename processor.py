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