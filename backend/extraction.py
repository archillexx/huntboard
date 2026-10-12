from dotenv import load_dotenv
from openai import OpenAI, APIError
from pydantic import BaseModel, ValidationError



load_dotenv()
client = OpenAI()


class ExtractionFailed(Exception):
    pass


def extract_skills(description, llm_client=client):

    try:
        response = llm_client.responses.parse(
        text_format=ExtractedSkills,
        model = "gpt-5-mini",
        instructions = "Extract only the technical skills explicitly mentioned in the job description (e.g., programming languages, frameworks, libraries, databases, cloud platforms, tools, APIs, and technologies), exclude all soft skills and non-technical requirements",
        input = description,
        )

        return  response.output_parsed.skills
    except(APIError, ValidationError):
        try:
            response = llm_client.responses.parse(
            text_format=ExtractedSkills,
            model = "gpt-5-mini",
            instructions = "Extract only the technical skills explicitly mentioned in the job description (e.g., programming languages, frameworks, libraries, databases, cloud platforms, tools, APIs, and technologies), exclude all soft skills and non-technical requirements",
            input = description,
            )

            return  response.output_parsed.skills
        
        except(APIError, ValidationError):
            raise ExtractionFailed("Could not extraxt skills after 2 attempts")
            
        
    
    


class ExtractedSkills(BaseModel):
    skills: list[str]



if __name__ == "__main__":
    description_job1="Strong full stack experience across React, PHP, JavaScript, Node, TypeScript, and Python  Database design and optimisation across SQL and NoSQL  Comfortable operating across cloud environments (AWS, GCP, Azure)  A track record of solving hard problems and shipping reliable software under pressure  You produce clean, thoughtful code and you care about the engineer who comes after you  You use AI tools actively and know how to get real leverage out of them  A degree in software engineering, computer science or a related field, or experience that shows the same ability  For senior and lead positions: you have owned a production platform end to end, led other engineers, and made architecture decisions you then had to live with"
    desrciption_job2="Experience writing software, ideally in scientific, engineering or data-heavy work. Graduates with strong university, research, or personal projects are encouraged to apply  Python - Write clean, reliable, efficient code with good error handling (defensive programming), and understand how the language works under the hood  NumPy, pandas - Work efficiently with large datasets and familiar with basic statistics (averages, distributions, histograms, charting)  PyTorch, OpenCV - Work with existing image analysis and AI code; GPU experience is a plus  PySide6, PyQt - Build and maintain GUI  Docker/Linux/Windows/conda/pip - Set up and troubleshoot development environments  Secure Development Practices -Handle credentials, dependencies and client data safely; recognise common security risks  Git/GitHub/CI-CD/pull requests - Familiar with working in a development team: sharing code, reviewing others' work and taking feedback on your own  Familiar with setting up or working with CI/CD pipelines and pull request reviews  Comfort working on software written by someone else: understanding it and changing it safely  Candidates must hold full and unrestricted working rights in Australia"
    desrciption_job3="Core Skills  Backend      C# / .NET       T-SQL / SQL Server       Microsoft Azure services, such as:        Azure Functions       Storage Queues       Azure Cosmos DB       SQL Server (cloud-hosted)    Front-End      JavaScript, HTML, CSS, ReactJS or experience with a similar framework     Highly Regarded      Xamarin Forms or React Native mobile app development       Experience with A.I assisted development tools "
    output1 = extract_skills(description_job1)
    output2 = extract_skills(desrciption_job2)
    output3 = extract_skills(desrciption_job3)

    print(output1)
    print(output2)
    print(output3)

