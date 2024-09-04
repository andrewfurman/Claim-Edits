document.addEventListener('DOMContentLoaded', function() {
    const summaries = document.querySelectorAll('.editable-summary');
    summaries.forEach(setupEditableSummary);

    // Add event listener for the add input form
    const addInputForm = document.getElementById('addInputForm');
    const addInputButton = document.getElementById('addInputButton');

    if (addInputForm) {
        addInputForm.addEventListener('submit', function(event) {
            event.preventDefault();
            addInputButton.textContent = 'Adding...';
            addInputButton.disabled = true;

            fetch(this.action, {
                method: 'POST',
                body: new FormData(this),
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Failed to add input');
                    });
                }
                return response.text();
            })
            .then(() => {
                window.location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                alert(`Error adding input: ${error.message}`);
            })
            .finally(() => {
                addInputButton.textContent = 'Add Input';
                addInputButton.disabled = false;
            });
        });
    }

    const documentName = document.getElementById('documentName');
    if (documentName) {
        documentName.contentEditable = false;
        setupEditableDocumentName(documentName);
    }
});

function setupEditableSummary(summary) {
    const markdownContent = summary.querySelector('.markdown-content');
    const markdownSource = summary.querySelector('.markdown-source');

    if (markdownContent && markdownSource) {
        let sourceText = markdownSource.textContent;
        // Convert to string if it's somehow still an array
        if (Array.isArray(sourceText)) {
            sourceText = sourceText.join('\n\n');
        }
        markdownContent.innerHTML = marked.parse(sourceText);
    }

    summary.addEventListener('dblclick', function() {
        if (!this.querySelector('textarea')) {
            const content = markdownSource ? markdownSource.textContent.trim() : '';
            const textarea = document.createElement('textarea');
            textarea.value = content;
            this.innerHTML = '';
            this.appendChild(textarea);
            textarea.focus();

            const saveButton = document.createElement('button');
            saveButton.textContent = '💾 Save';
            saveButton.addEventListener('click', function() {
                saveSummary(summary, textarea.value);
            });
            this.appendChild(saveButton);
        }
    });
}

function saveSummary(summaryElement, newContent) {
    const inputId = summaryElement.dataset.inputId;

    if (!inputId) {
        console.error('Error: No input ID found');
        alert('Error saving changes. Please try again.');
        return;
    }

    fetch(`/input/${inputId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            document_summary: newContent
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Recreate the markdown content structure
            summaryElement.innerHTML = `
                <div class="markdown-content">${marked.parse(newContent)}</div>
                <div class="markdown-source" style="display: none;">${newContent}</div>
            `;

            // Re-setup the editable summary
            setupEditableSummary(summaryElement);
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert(`Error saving changes: ${error.message}`);
    });
}

function generateSummary(inputId) {
    let summaryElement = document.getElementById(`summary-${inputId}`);

    if (!summaryElement) {
        summaryElement = document.createElement('div');
        summaryElement.id = `summary-${inputId}`;
        summaryElement.className = 'editable-summary';
        summaryElement.dataset.inputId = inputId;

        const parentElement = document.querySelector(`button[onclick="generateSummary(${inputId})"]`).parentElement;
        parentElement.innerHTML = '';
        parentElement.appendChild(summaryElement);
    }

    summaryElement.textContent = "Generating summary...";

    fetch(`/input/${inputId}/summarize`, {
        method: 'POST',
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Convert summary to string if it's an array
            let summaryText = Array.isArray(data.summary) ? data.summary.join('\n') : data.summary;
            
            summaryElement.innerHTML = `
                <div class="markdown-content">${marked.parse(summaryText)}</div>
                <div class="markdown-source" style="display: none;">${summaryText}</div>
            `;

            setupEditableSummary(summaryElement);
        } else {
            throw new Error(data.error || "Failed to generate summary");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        summaryElement.textContent = `Error: ${error.message}`;
    });
}

function setupEditableDocumentName(element) {
    let originalContent;

    element.addEventListener('dblclick', function() {
        if (this.contentEditable === 'false') {
            this.contentEditable = true;
            originalContent = this.textContent;
            this.focus();

            const saveButton = document.createElement('button');
            saveButton.textContent = '💾 Save';
            saveButton.style.marginLeft = '10px';
            saveButton.addEventListener('click', function() {
                saveDocumentName(element);
            });
            element.parentNode.insertBefore(saveButton, element.nextSibling);
        }
    });

    element.addEventListener('blur', function() {
        if (!event.relatedTarget || !event.relatedTarget.textContent.includes('Save')) {
            this.contentEditable = false;
            this.textContent = originalContent;
            const saveButton = this.nextElementSibling;
            if (saveButton && saveButton.textContent.includes('Save')) {
                saveButton.remove();
            }
        }
    });
}

function saveDocumentName(element) {
    const newName = element.textContent.trim();
    const inputId = element.dataset.inputId;

    fetch(`/input/${inputId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            document_name: newName
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            element.contentEditable = false;
            const saveButton = element.nextElementSibling;
            if (saveButton && saveButton.textContent.includes('Save')) {
                saveButton.remove();
            }
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert(`Error saving changes: ${error.message}`);
        element.textContent = originalContent;
    });
}