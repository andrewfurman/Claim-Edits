# Example ChatGPT Request in structured data

# POST /v1/chat/completions
# {
#   "model": "gpt-4o-2024-08-06",
#   "messages": [
#     {
#       "role": "system",
#       "content": "Extract action items, due dates, and owners from meeting notes."
#     },
#     {
#       "role": "user",
#       "content": "...meeting notes go here..."
#     }
#   ],
#   "response_format": {
#     "type": "json_schema",
#     "json_schema": {
#       "name": "action_items",
#       "strict": true,
#       "schema": {
#         "type": "object",
#         "properties": {
#           "action_items": {
#             "type": "array",
#             "items": {
#               "type": "object",
#               "properties": {
#                 "description": {
#                   "type": "string",
#                   "description": "Description of the action item."
#                 },
#                 "due_date": {
#                   "type": ["string", "null"],
#                   "description": "Due date for the action item, can be null if not specified."
#                 },
#                 "owner": {
#                   "type": ["string", "null"],
#                   "description": "Owner responsible for the action item, can be null if not specified."
#                 }
#               },
#               "required": ["description", "due_date", "owner"],
#               "additionalProperties": false
#             },
#             "description": "List of action items from the meeting."
#           }
#         },
#         "required": ["action_items"],
#         "additionalProperties": false
#       }
#     }
#   }
# }

# generate_claim_edits.py

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

def generate_claim_edits(input_id):
    # Get the input document contents
    document_contents = get_input_contents(input_id)

    # Prepare the ChatGPT API request
    payload = {
        "model": "gpt-4o-mini",  # or whichever model you prefer
        "messages": [
            {
                "role": "system",
                "content": "Extract claim edits from the given document."
            },
            {
                "role": "user",
                "content": document_contents
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "claim_edits",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "claim_edits": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "edit_description": {
                                        "type": "string",
                                        "description": "Description of the claim edit."
                                    },
                                    "edit_message": {
                                        "type": "string",
                                        "description": "Message for the claim edit."
                                    },
                                    "edit_conditions": {
                                        "type": "string",
                                        "description": "Conditions for the claim edit."
                                    },
                                    "edit_non_conditions": {
                                        "type": "string",
                                        "description": "Non-conditions for the claim edit."
                                    }
                                },
                                "required": ["edit_description", "edit_message", "edit_conditions", "edit_non_conditions"],
                                "additionalProperties": False
                            },
                            "description": "List of claim edits extracted from the document."
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
    claim_edits_data = json.loads(response.choices[0].message.content)['claim_edits']

    # Update the database with new claim edits
    input_doc = Input.query.get(input_id)
    for edit_data in claim_edits_data:
        new_edit = ClaimEdit(
            input_id=input_id,
            edit_description=edit_data['edit_description'],
            edit_message=edit_data['edit_message'],
            edit_conditions=edit_data['edit_conditions'],
            edit_non_conditions=edit_data['edit_non_conditions']
        )
        db.session.add(new_edit)

    db.session.commit()

    return f"Generated {len(claim_edits_data)} claim edits for input {input_id}"