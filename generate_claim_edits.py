import os
import json
from openai import OpenAI
from models import db, Input, ClaimEdit

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def get_input_contents(input_id):
    input_doc = Input.query.get(input_id)
    if not input_doc:
        raise ValueError(f"No input found with id {input_id}")
    return input_doc.document_contents

def get_input_summary(input_id):
    input_doc = Input.query.get(input_id)
    if not input_doc:
        raise ValueError(f"No input found with id {input_id}")
    return input_doc.document_summary

def generate_claim_edits(input_id):
    # Get the input document contents
    document_contents = get_input_contents(input_id)
    document_summary = get_input_summary(input_id)

    # Delete existing claim edits for this input_id
    ClaimEdit.query.filter_by(input_id=input_id).delete()
    db.session.commit()

    # Prepare the ChatGPT API request
    payload = {
        # "model": "gpt-4o-mini",
        "model": "gpt-4o-2024-08-06", # Full ChatGPT Model with Structured Inputs Enabled, change to regular 4o after October 2024
        "messages": [
        {
            "role": "system",
            "content": """
                You are an assistant that extracts claim edits information from the given document.
                Make sure that this includes all data validations that are required for health insurance claims 
                that are specifically mentioned in this document.
                Make sure to not create any edits that are not directly outlined in the document included."
            """
        }, 
        {
            "role": "user",
        "content": f"Here is a summary of the document:\n{document_summary}\n\nHere are the document contents that need claim edits extracted from them:\n{document_contents}"
        }],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "claim_edits",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "claim_edits": {
                            "type":
                            "array",
                            "items": {
                                "type":
                                "object",
                                "properties": {
                                    "edit_description": {
                                        "type":
                                        "string",
                                        "description":
                                        "Description of the claim edit."
                                    },
                                    "edit_message": {
                                        "type":
                                        "string",
                                        "description":
                                        "Message for the claim edit. This is the friendly suggestion displayed to the healthcare provider (doctor) indicating that a data requirement on the Claim that they submited has not been met. This should be phrased as a friendly suggestion such as We recommned that you fill out this data segment when submitting this specific type of claim."
                                    },
                                    "edit_conditions": {
                                        "type":
                                        "string",
                                        "description":
                                        "Conditions for the claim edit to be applied. This is where there is essentially a data quality check, or data requirement that has not been met and the healthcare provider needs to be alerted of this by the health insurance company that they submitted the claim to. These conditions need to be extremely specific and mention specific field names or data attributes in the file format."
                                    },
                                    "edit_non_conditions": {
                                        "type":
                                        "string",
                                        "description":
                                        "Non-conditions for the claim edit. Where this edit should not be run. If no exclusion criteria is found, this value should be N/A"
                                    }
                                },
                                "required": [
                                    "edit_description", "edit_message",
                                    "edit_conditions", "edit_non_conditions"
                                ],
                                "additionalProperties":
                                False
                            },
                            "description":
                            "List of claim edits extracted from the document."
                        }
                    },
                    "required": ["claim_edits"],
                    "additionalProperties": False
                }
            }
        }
    }

    # Send request to ChatGPT API
    response = client.chat.completions.create(**payload)

    # Extract the claim edits from the response
    claim_edits_data = json.loads(
        response.choices[0].message.content)['claim_edits']

    # Update the database with new claim edits
    input_doc = Input.query.get(input_id)
    for edit_data in claim_edits_data:
        new_edit = ClaimEdit(
            input_id=input_id,
            edit_description=edit_data['edit_description'],
            edit_message=edit_data['edit_message'],
            edit_conditions=edit_data['edit_conditions'],
            edit_non_conditions=edit_data['edit_non_conditions'])
        db.session.add(new_edit)

    db.session.commit()

    return f"Generated {len(claim_edits_data)} claim edits for input {input_id}"
