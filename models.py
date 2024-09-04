import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import requests
from bs4 import BeautifulSoup
from extract_contents import extract_text_from_pdf
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Input(db.Model):
    __tablename__ = 'inputs'

    id = db.Column(db.Integer, primary_key=True)
    document_name = db.Column(db.Text, nullable=False)
    document_url = db.Column(db.Text)
    document_contents = db.Column(db.Text)
    document_summary = db.Column(db.Text, nullable=True, default='')

    # Add relationship to ClaimEdits
    claim_edits = db.relationship('ClaimEdit', back_populates='input', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Input {self.document_name}>'

    @classmethod
    def create_from_url(cls, url):
        logging.info(f"Attempting to create Input from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            logging.info(f"Successfully fetched URL: {url}")

            content_type = response.headers.get('Content-Type', '').lower()
            logging.info(f"Content-Type: {content_type}")

            if 'application/pdf' in content_type:
                document_contents = extract_text_from_pdf(url)
                logging.info("Extracted text from PDF")
            else:
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252']
                document_contents = None

                for encoding in encodings:
                    try:
                        document_contents = response.content.decode(encoding)
                        logging.info(f"Successfully decoded content with {encoding}")
                        break
                    except UnicodeDecodeError:
                        logging.warning(f"Failed to decode with {encoding}")

                if document_contents is None:
                    logging.warning("All decoding attempts failed, using 'utf-8' with 'ignore'")
                    document_contents = response.content.decode('utf-8', errors='ignore')

            new_input = cls(
                document_name=url,  # Use URL as document name
                document_url=url,
                document_contents=document_contents
            )
            logging.info("Successfully created new Input object")
            return new_input
        except Exception as e:
            logging.error(f"Error creating Input from URL: {str(e)}", exc_info=True)
            return None

class ClaimEdit(db.Model):
    __tablename__ = 'claim_edits'

    id = db.Column(db.Integer, primary_key=True)
    input_id = db.Column(db.Integer, db.ForeignKey('inputs.id'), nullable=False)
    edit_description = db.Column(db.Text)
    edit_message = db.Column(db.Text)
    edit_conditions = db.Column(db.Text)
    edit_non_conditions = db.Column(db.Text)

    # Relationship to Input
    input = db.relationship('Input', back_populates='claim_edits')

    def __repr__(self):
        return f'<ClaimEdit {self.id} for Input {self.input_id}>'

# Database configuration
DATABASE_URL = os.environ['DATABASE_URL']