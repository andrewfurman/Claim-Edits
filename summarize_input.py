# import OpenAI from "openai";
# const openai = new OpenAI();

# const completion = await openai.chat.completions.create({
#     model: "gpt-4o-mini",
#     messages: [
#         { role: "system", content: "You are a helpful assistant." },
#         {
#             role: "user",
#             content: "Write a haiku about recursion in programming.",
#         },
#     ],
# });

# console.log(completion.choices[0].message);

import os
import json
from openai import OpenAI
from models import db, Input

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def summarize_input(input_id):
    # Retrieve the input from the database
    input_doc = Input.query.get_or_404(input_id)

    # Prepare the ChatGPT API request
    payload = {
        "model": "gpt-4o-mini",  # or whichever model you prefer
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes documents and generates names for them."},
            {"role": "user", "content": f"Please summarize the following document in three bullet points, each starting with an emoji, and generate a name for it. Format the summary as markdown:\n\n{input_doc.document_contents}"}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "document_summary",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "A three-bullet-point summary always formatted as markdown bullet points. Each bullet point will start with an emoji distrinctly representing the bullet point, followed by a boleded title, followed by a colon, then a one sentance detailed description free of filler words. Also insert a new line between each bullet point. The bullet points should always be formated using asteriks such as * First item * Second item * Third item"
                        },
                        "generated_name": {
                            "type": "string",
                            "description": "A generated name for the document based on its content - this should include the name of the organization that produced the document followed by a very descriptive name that fits in under 100 characters"
                        }
                    },
                    "required": ["summary", "generated_name"],
                    "additionalProperties": False
                }
            }
        }
    }

    # Send request to ChatGPT API
    response = client.chat.completions.create(**payload)

    # Extract the summary and generated name from the response
    result = json.loads(response.choices[0].message.content)

    # Update the document_summary and name in the database
    input_doc.document_summary = result['summary']
    input_doc.document_name = result['generated_name']
    db.session.commit()

    return result['summary'], result['generated_name']

# Example usage:
# summary, name = summarize_input(1)  # Where 1 is the ID of the input you want to summarize