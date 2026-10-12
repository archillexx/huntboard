from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI()


def extract_skills_text(description):
    response = client.responses.create(
        model = "gpt-5-mini",
        instructions = "Take the description and give a list of skills or technology found inside the description required for the job",
        input = description,
    )

    return  response.output_text

if __name__ == "__main__":
    description="Strong full stack experience across React, PHP, JavaScript, Node, TypeScript, and Python  Database design and optimisation across SQL and NoSQL  Comfortable operating across cloud environments (AWS, GCP, Azure)  A track record of solving hard problems and shipping reliable software under pressure  You produce clean, thoughtful code and you care about the engineer who comes after you  You use AI tools actively and know how to get real leverage out of them  A degree in software engineering, computer science or a related field, or experience that shows the same ability  For senior and lead positions: you have owned a production platform end to end, led other engineers, and made architecture decisions you then had to live with"
    
    output = extract_skills_text(description)

    print(output)

