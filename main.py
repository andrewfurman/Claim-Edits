import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from models import db, Input, ClaimEdit
from conflicts_gpt import analyze_edit_conflicts
import logging
from sqlalchemy.exc import SQLAlchemyError
from summarize_input import summarize_input as generate_summary
from generate_claim_edits import generate_claim_edits

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def index():
    inputs = Input.query.all()
    return render_template('inputs.html', inputs=inputs)

@app.route('/add_input', methods=['POST'])
def add_input():
    url = request.form.get('document_url')
    legacy_code = request.form.get('legacy_code')
    logger.info(f"Received request to add input. URL: {url}, Legacy Code: {'Present' if legacy_code else 'Not present'}")
    if url:
        # Check if the URL already exists
        existing_input = Input.query.filter_by(document_url=url).first()
        if existing_input:
            logger.info("Duplicate URL detected, not adding to database")
            return jsonify(success=False, error="This URL has already been added")
        new_input = Input.create_from_url(url)
        if new_input:
            try:
                db.session.add(new_input)
                db.session.commit()
                logger.info("Successfully added Input to database")
                return jsonify(success=True, message="Input added successfully")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error occurred: {str(e)}")
                return jsonify(success=False, error="An error occurred while adding the input to the database")
        else:
            return jsonify(success=False, error="Failed to create input from URL")
    
    # ... rest of the function remains the same ...
    elif legacy_code:
        # Handle legacy code input
        new_input = Input(
            document_name="Legacy Code",
            document_contents=legacy_code,
            document_type="legacy_code"
        )
        try:
            db.session.add(new_input)
            db.session.commit()
            logger.info("Successfully added legacy code Input to database")
            return jsonify(success=True, message="Legacy code added successfully")
        except IntegrityError:
            db.session.rollback()
            logger.info("Integrity error occurred, not adding legacy code to database")
            return jsonify(success=False, error="An error occurred while adding the legacy code")
    else:
        return jsonify(success=False, error="No URL or legacy code provided")

@app.route('/input/<int:input_id>/update', methods=['POST'])
def update_input(input_id):
    input_item = Input.query.get_or_404(input_id)
    data = request.json

    if 'document_summary' in data:
        input_item.document_summary = data['document_summary']
    elif 'document_name' in data:
        input_item.document_name = data['document_name']

    try:
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e))

@app.route('/input/<int:input_id>/summarize', methods=['POST'])
def summarize_input(input_id):
    input_item = Input.query.get_or_404(input_id)

    try:
        summary, generated_name = generate_summary(input_id)

        # The generate_summary function already updates the database,
        # so we don't need to set input_item.document_summary or commit here

        return jsonify(success=True, summary=summary, generated_name=generated_name)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500

@app.route('/input/<int:input_id>')
def input_contents(input_id):
    input_item = Input.query.get_or_404(input_id)
    claim_edits = ClaimEdit.query.filter_by(input_id=input_id).all()
    return render_template(
        'input_contents.html',
        input=input_item,
        claim_edits=claim_edits
    )

@app.route('/conflicts')
def conflicts():
    return render_template('conflicts.html')

@app.route('/analyze_conflicts', methods=['GET'])
def analyze_conflicts():
    try:
        summary = analyze_edit_conflicts()
        return jsonify(success=True, summary=summary)
    except Exception as e:
        logger.error(f"Error in analyze_conflicts: {str(e)}")
        return jsonify(success=False, error=str(e))

@app.route('/input/<int:input_id>/delete', methods=['POST'])
def delete_input(input_id):
    input_doc = Input.query.get_or_404(input_id)
    try:
        db.session.delete(input_doc)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Error deleting input: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/input/<int:input_id>/generate_edits', methods=['POST'])
def generate_edits(input_id):
    try:
        # Generate the edits
        result_message = generate_claim_edits(input_id)
        
        return jsonify(success=True, message=result_message)
    except Exception as e:
        print(f"Error generating edits: {str(e)}")  # For debugging
        return jsonify(success=False, error=str(e)), 500

@app.route('/claim_edits')
def claim_edits():
    claim_edits = ClaimEdit.query.all()
    return render_template('claim_edits.html', claim_edits=claim_edits)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)