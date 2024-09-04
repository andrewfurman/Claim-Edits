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
from openai import OpenAI
from models import db, Input

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def summarize_input(input_id):
    # Retrieve the input from the database
    input_doc = Input.query.get_or_404(input_id)

    # Send the document contents to ChatGPT for summarization
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or whichever model you prefer
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
            {"role": "user", "content": f"Please summarize the following document.  This summary should contain 3 bullet points that each start with an emoji that distinctly represents the bullet, a bolded title and a one sentance description:\n\n{input_doc.document_contents}"}
        ]
    )

    # Extract the summary from the response
    summary = response.choices[0].message.content

    # Update the document_summary in the database
    input_doc.document_summary = summary
    db.session.commit()

    return summary

# Example usage:
# summary = summarize_input(1)  # Where 1 is the ID of the input you want to summarize