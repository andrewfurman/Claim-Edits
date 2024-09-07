import os
import json
from openai import OpenAI
from sqlalchemy import create_engine, join
from sqlalchemy.orm import sessionmaker
from models import ClaimEdit, Input, Base

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def analyze_edit_conflicts():
    # Set up database connection
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query all claim edits with input names
    claim_edits_with_inputs = session.query(ClaimEdit, Input.document_name).join(Input).all()

    # Format claim edits as JSON
    claim_edits_json = json.dumps([{
        # 'id': edit.id,
        # 'input_id': edit.input_id,
        'input_name': input_name,
        'edit_description': edit.edit_description,
        'edit_message': edit.edit_message,
        'edit_conditions': edit.edit_conditions,
        'edit_non_conditions': edit.edit_non_conditions
    } for edit, input_name in claim_edits_with_inputs], indent=2)

    # Prepare the ChatGPT API request
    payload = {
        "model": "gpt-4o-mini",  # or whichever model you prefer
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that analyzes claim edits and identifies conflicting logic."},
            {"role": "user", "content": f"Here is the JSON data of all claim edits, including input names:\n\n{claim_edits_json}\n\nPlease analyze this data and provide a summary of conflicting logic between claim edits. This should specifically highlight where there is conflicting logic refrencing the same Claim Data Segments. For example if one edit discusses specific formats of a segment, and then another edit says to ignore this segment if certain criteria is met. This is what should be highlighted."}
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
                            "description": "Detailed list of conflicting claim edits based on the provided data. Use Markdown headers for each of the conflicts with bullet points below to give details of the segments in the claim that would conflict, and a recommendation of if this logic needs to be changed. The bullet points below each header should always be formatted using asterisks such as * First item * Second item * Third item. Start each bullet point with a bolded title, followed by a colon, then a one sentence detailed description free of filler words. For each conflicting edit, make sure to include a bullet point that highlights the specific Claim Data Segment and the data in that segment being validated by each edit. Make sure to highlight specific logic to ignore claim data segment validations if those directons to ignore edits are found in one edit, but the validations are required in another edit."
                        }
                    },
                    "required": ["summary"],
                    "additionalProperties": False
                }
            }
        }
    }

    # Send request to ChatGPT API
    response = client.chat.completions.create(**payload)

    # Extract the summary from the response
    result = json.loads(response.choices[0].message.content)

    # Close the database session
    session.close()

    return result['summary']