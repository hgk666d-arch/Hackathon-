import requests

class SkillProfiler:
    def analyze_github(self, github_username):
        """Analyzes coding capabilities via GitHub API."""
        url = f"https://api.github.com/users/{github_username}/repos"
        try:
            response = requests.get(url).json()
            languages = {}
            for repo in response:
                lang = repo.get('language')
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
            return {
                "top_languages": sorted(languages, key=languages.get, reverse=True)[:3],
                "repo_count": len(response)
            }
        except:
            return "Profile not found or private."
            