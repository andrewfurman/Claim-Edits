import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_migrate import Migrate
from models import db, Input
from summarize_input import summarize_input
from generate_claim_edits import generate_claim_edits

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    inputs = Input.query.order_by(Input.id.asc()).all()
    return render_template('inputs.html', inputs=inputs)


@app.route('/add_input', methods=['POST'])
def add_input():
    document_url = request.form['document_url']
    app.logger.info(f"Received request to add input with URL: {document_url}")
    try:
        new_input = Input.create_from_url(document_url)
        if new_input is None:
            raise ValueError(
                f"Failed to create Input object from URL: {document_url}")
        app.logger.info("Successfully created Input object")
        db.session.add(new_input)
        db.session.commit()
        app.logger.info("Successfully added Input to database")
        return redirect(url_for('index'))
    except Exception as e:
        error_message = f"Error adding input: {str(e)}"
        app.logger.error(error_message, exc_info=True)
        return jsonify({"success": False, "error": error_message}), 500


@app.route('/input/<int:input_id>')
def input_contents(input_id):
    input_doc = Input.query.get_or_404(input_id)
    claim_edits = input_doc.claim_edits  # Fetch related claim edits
    return render_template('input_contents.html',
                           input=input_doc,
                           claim_edits=claim_edits)


@app.route('/input/<int:input_id>/summarize', methods=['POST'])
def generate_summary(input_id):
    try:
        summary = summarize_input(input_id)
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        app.logger.error(f"Error generating summary: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


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


@app.route('/input/<int:input_id>/update', methods=['POST'])
def update_input(input_id):
    input_doc = Input.query.get_or_404(input_id)
    data = request.json
    if 'document_name' in data:
        input_doc.document_name = data['document_name']
    if 'document_contents' in data:
        input_doc.document_contents = data['document_contents']
    if 'document_summary' in data:
        input_doc.document_summary = data['document_summary']
    db.session.commit()
    return jsonify({"success": True})


@app.route('/input/<int:input_id>/generate_edits', methods=['POST'])
def generate_edits(input_id):
    try:
        result = generate_claim_edits(input_id)
        return jsonify({"success": True, "message": result})
    except Exception as e:
        app.logger.error(f"Error generating edits: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
