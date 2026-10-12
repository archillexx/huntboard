
from collections import Counter


SKILLS_ALIASES = {
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "react": "react",

    "nodejs": "node.js",
    "node.js": "node.js",
    "node js": "node.js",
    "node": "node.js",

    "javascript": "javascript",
    "js": "javascript",

    "typescript": "typescript",
    "ts": "typescript",

    "amazon web services": "aws",
    "aws": "aws",

    "microsoft azure": "azure",
    "azure": "azure",

    "postgres": "postgresql",
    "postgresql": "postgresql",
    "postgre sql": "postgresql",

    "mongodb": "mongodb",
    "mongo db": "mongodb",
    "mongo": "mongodb",

    "kubernetes": "kubernetes",
    "k8s": "kubernetes",

    "docker": "docker",

    "python": "python",
    "python3": "python",
    "py": "python",

    "c++": "c++",
    "cpp": "c++",
    "c plus plus": "c++",

    "c#": "c#",
    "csharp": "c#",
    "c sharp": "c#",

    "golang": "go",
    "go": "go",

    "nextjs": "next.js",
    "next.js": "next.js",
    "next js": "next.js",

    "angular": "angular",
    "angularjs": "angular",
    "angular.js": "angular",

    "vue": "vue",
    "vuejs": "vue",
    "vue.js": "vue",

    "express": "express",
    "expressjs": "express",
    "express.js": "express",

    "mysql": "mysql",
    "my sql": "mysql",

    "sql": "sql",

    "graphql": "graphql",
    "graph ql": "graphql",

    "rest api": "rest",
    "restful api": "rest",
    "restful": "rest",
    "rest": "rest",

    "github": "github",
    "gitlab": "gitlab",
    "bitbucket": "bitbucket",

    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "ci cd": "ci/cd",

    "amazon ec2": "ec2",
    "aws ec2": "ec2",
    "ec2": "ec2",

    "amazon s3": "s3",
    "aws s3": "s3",
    "s3": "s3",

    "aws lambda": "lambda",
    "amazon lambda": "lambda",
    "lambda": "lambda",

    "aws rds": "rds",
    "amazon rds": "rds",
    "rds": "rds",

    "aws eks": "eks",
    "amazon eks": "eks",
    "eks": "eks",

    "aws ecs": "ecs",
    "amazon ecs": "ecs",
    "ecs": "ecs",

    "terraform": "terraform",

    "jenkins": "jenkins",

    "pytorch": "pytorch",
    "torch": "pytorch",

    "tensorflow": "tensorflow",

    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",

    "machine learning": "machine learning",
    "ml": "machine learning",

    "artificial intelligence": "artificial intelligence",
    "ai": "artificial intelligence",

    "generative ai": "generative ai",
    "gen ai": "generative ai",
    "genai": "generative ai",

    "natural language processing": "natural language processing",
    "nlp": "natural language processing",

    "react native": "react native",
    "reactnative": "react native",

    "flutter": "flutter",

    "jest": "jest",
    "pytest": "pytest",
    "junit": "junit",
    "selenium": "selenium",
    "cypress": "cypress",
    "playwright": "playwright",

    "apache spark": "apache spark",
    "spark": "apache spark",
    "pyspark": "apache spark",

    "apache kafka": "apache kafka",
    "kafka": "apache kafka",

    "apache airflow": "airflow",
    "airflow": "airflow",

    "databricks": "databricks",
    "snowflake": "snowflake",

    "html": "html",
    "html5": "html",

    "css": "css",
    "css3": "css",

    "tailwind": "tailwind css",
    "tailwind css": "tailwind css",
    "tailwindcss": "tailwind css",

    "bootstrap": "bootstrap",
    "bootstrap css": "bootstrap",

    "redis": "redis",
    "sqlite": "sqlite",
    "oracle": "oracle",

    "firebase": "firebase",

    "bash": "bash",
    "bash scripting": "bash",

    "powershell": "powershell",
    "pwsh": "powershell",

    "jira": "jira",
    "atlassian jira": "jira",

    "npm": "npm",
    "node package manager": "npm",

    "yarn": "yarn",
    "pnpm": "pnpm",

    "maven": "maven",
    "apache maven": "maven",

    "gradle": "gradle",

    "nginx": "nginx",

    "prometheus": "prometheus",
    "grafana": "grafana",
    "splunk": "splunk",
    "datadog": "datadog",
}

def normalise_skills(skills):
    cleaned_skills = []
    for skill in skills:
        cleaned_skill=skill.strip().lower()
        cleaned_skills.append(SKILLS_ALIASES.get(cleaned_skill, cleaned_skill))

    return cleaned_skills 

def most_missed_skills(jobs,my_skills):

    tally = Counter()
    if not jobs:
        return []
    for job in jobs:
        _,missing_skills = fit_score(job,my_skills)
        tally.update(missing_skills)
    
    return tally.most_common()


def fit_score(j_skills,r_skills):
        normalised_j_skills = normalise_skills(j_skills)
        normalised_r_skills = normalise_skills(r_skills) 
        job_skills = set(normalised_j_skills)
        resume_skills = set(normalised_r_skills)
        if job_skills == set():
            score = None
            missing_skills = []
        else:
            missing_skills = sorted(job_skills - resume_skills)
            missing_skills_count = len(missing_skills)

            score = ((len(job_skills)-missing_skills_count)/len(job_skills))*100

        
        return score,missing_skills



if __name__ == "__main__":
    jobSkills=["react","python","java"]
    resumeSkills = ["react","python","c++","c"]
    
    percentage, missingSkill = fit_score(jobSkills,resumeSkills)

    print(f"Percentage={percentage}% Missing Skill is {missingSkill} ")


    
