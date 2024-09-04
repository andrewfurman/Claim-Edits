import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import requests
from bs4 import BeautifulSoup
from extract_contents import extract_text_from_pdf

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
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses

            content_type = response.headers.get('Content-Type', '').lower()

            if 'application/pdf' in content_type:
                document_name = url.split('/')[-1]
                document_contents = extract_text_from_pdf(response.content)
            else:
                # Detect the encoding
                encoding = response.encoding if response.encoding else 'utf-8'

                # Try to decode with the detected encoding, fallback to 'latin-1' if it fails
                try:
                    decoded_content = response.content.decode(encoding)
                except UnicodeDecodeError:
                    decoded_content = response.content.decode('latin-1')

                soup = BeautifulSoup(decoded_content, 'html.parser')
                document_name = soup.title.string if soup.title else "Untitled Document"
                document_contents = soup.get_text()

            new_input = cls(
                document_name=document_name,
                document_url=url,
                document_contents=document_contents
            )
            return new_input
        except Exception as e:
            print(f"Error creating Input from URL: {str(e)}")
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