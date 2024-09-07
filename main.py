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
    document_url = request.form.get('document_url')

    if not document_url:
        return jsonify({"success": False, "error": "No URL provided"}), 400

    try:
        new_input = Input.create_from_url(document_url)
        if new_input:
            db.session.add(new_input)
            db.session.commit()

            # Now that we have committed the new input, we can access its ID
            new_input_id = new_input.id

            # Call the summarize_input function
            try:
                summary, generated_name = generate_summary(new_input_id)
                return jsonify({
                    "success": True, 
                    "message": "Input added and summarized successfully",
                    "summary": summary,
                    "generated_name": generated_name
                }), 200
            except Exception as summarize_error:
                # If summarization fails, we still return success for adding the input
                logger.error(f"Error summarizing input: {str(summarize_error)}")
                return jsonify({
                    "success": True, 
                    "message": "Input added successfully, but summarization failed",
                    "summarize_error": str(summarize_error)
                }), 200
        else:
            return jsonify({"success": False, "error": "Failed to create input from URL"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/add_input_legacy', methods=['POST'])
def add_input_legacy():
    legacy_code = request.form.get('legacy_code')

    if not legacy_code:
        return jsonify({"success": False, "error": "No legacy code provided"}), 400

    try:
        new_input = Input(
            document_name="Legacy Code",
            document_url="🚫 Not Applicable",
            document_contents=legacy_code,
            document_type="Legacy Code"
        )
        db.session.add(new_input)
        db.session.commit()

        # Now that we have committed the new input, we can access its ID
        new_input_id = new_input.id

        # Call the summarize_input function
        try:
            summary, generated_name = generate_summary(new_input_id)
            return jsonify({
                "success": True, 
                "message": "Legacy code added and summarized successfully",
                "summary": summary,
                "generated_name": generated_name
            }), 200
        except Exception as summarize_error:
            # If summarization fails, we still return success for adding the input
            logger.error(f"Error summarizing legacy code: {str(summarize_error)}")
            return jsonify({
                "success": True, 
                "message": "Legacy code added successfully, but summarization failed",
                "summarize_error": str(summarize_error)
            }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

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