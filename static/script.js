document.addEventListener('DOMContentLoaded', function() {
    const summaries = document.querySelectorAll('.editable-summary');
    summaries.forEach(setupEditableSummary);

    const documentName = document.getElementById('documentName');
    if (documentName) {
        documentName.contentEditable = false;
        setupEditableDocumentName(documentName);
    }

    const analyzeButton = document.getElementById('analyzeConflicts');
    if (analyzeButton) {
        analyzeButton.addEventListener('click', analyzeConflicts);
    }

    const generateEditsButton = document.getElementById('generateEditsButton');
    if (generateEditsButton) {
        // Remove any existing event listeners
        generateEditsButton.replaceWith(generateEditsButton.cloneNode(true));

        // Get the new button (after replacing)
        const newGenerateEditsButton = document.getElementById('generateEditsButton');

        newGenerateEditsButton.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent any default action
            event.stopPropagation(); // Stop event from bubbling up

            const inputId = this.dataset.inputId;
            if (!this.disabled) { // Check if button is not already disabled
                generateEdits(inputId);
            }
        });
    }

    const addInputForm = document.getElementById('addInputForm');
    if (addInputForm) {
        addInputForm.addEventListener('submit', handleAddInput);
    }

    const importLegacyCodeForm = document.getElementById('importLegacyCodeForm');
    if (importLegacyCodeForm) {
        importLegacyCodeForm.addEventListener('submit', handleAddLegacyCode);
    }

    const deleteButton = document.getElementById('deleteButton');
    if (deleteButton) {
        // Remove any existing event listeners
        deleteButton.replaceWith(deleteButton.cloneNode(true));

        // Get the new button (after replacing)
        const newDeleteButton = document.getElementById('deleteButton');

        newDeleteButton.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent any default action
            event.stopPropagation(); // Stop event from bubbling up

            const inputId = document.getElementById('documentName').dataset.inputId;
            if (!this.disabled) { // Check if button is not already disabled
                this.disabled = true; // Disable the button to prevent double clicks
                deleteInput(inputId);
            }
        });
    }
});

function deleteInput(inputId) {
    if (confirm('Are you sure you want to delete this input?')) {
        fetch(`/input/${inputId}/delete`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/';  // Redirect to the main page
            } else {
                throw new Error(data.error || "Failed to delete input");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error deleting input: ${error.message}`);
        });
    }
}

function handleAddInput(event) {
    event.preventDefault();
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    let startTime = Date.now();
    let timerInterval;
    // Disable the button and show loading state
    submitButton.disabled = true;
    submitButton.style.backgroundColor = 'gray';
    updateAddInputButtonText();
    // Start the timer
    timerInterval = setInterval(updateAddInputButtonText, 1000);
    // Send the form data
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            throw new Error(data.error || "Failed to add input");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error adding input: ${error.message}`);
    })
    .finally(() => {
        // Stop the timer and reset the button
        clearInterval(timerInterval);
        submitButton.disabled = false;
        submitButton.style.backgroundColor = '';
        submitButton.textContent = originalButtonText;
    });
    function updateAddInputButtonText() {
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        submitButton.textContent = `🔄 Adding Input... ${elapsedSeconds}s`;
    }
}

function handleAddLegacyCode(event) {
    event.preventDefault();
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    let startTime = Date.now();
    let timerInterval;
    // Disable the button and show loading state
    submitButton.disabled = true;
    submitButton.style.backgroundColor = 'gray';
    updateAddLegacyCodeButtonText();
    // Start the timer
    timerInterval = setInterval(updateAddLegacyCodeButtonText, 1000);
    // Send the form data
    fetch('/add_input_legacy', {
        method: 'POST',
        body: new FormData(form)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            throw new Error(data.error || "Failed to add legacy code input");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error adding legacy code input: ${error.message}`);
    })
    .finally(() => {
        // Stop the timer and reset the button
        clearInterval(timerInterval);
        submitButton.disabled = false;
        submitButton.style.backgroundColor = '';
        submitButton.textContent = originalButtonText;
    });
    function updateAddLegacyCodeButtonText() {
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        submitButton.textContent = `🔄 Importing Legacy Code... ${elapsedSeconds}s`;
    }
}

function generateEdits(inputId) {
    const generateButton = document.getElementById('generateEditsButton');
    let startTime = Date.now();
    let timerInterval;

    // Disable the button and show loading state
    generateButton.disabled = true;
    generateButton.style.backgroundColor = 'gray';
    updateGenerateButtonText();

    // Start the timer
    timerInterval = setInterval(updateGenerateButtonText, 1000);

    // Call the generate_edits endpoint
    fetch(`/input/${inputId}/generate_edits`, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data); // For debugging
        if (data.success) {
            // Show an alert with the returned string
            alert(data.message);
            // Refresh the page to show new edits
            location.reload();
        } else {
            throw new Error(data.error || "Failed to generate edits");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error generating edits: ${error.message}`);
    })
    .finally(() => {
        // Stop the timer and reset the button
        clearInterval(timerInterval);
        generateButton.disabled = false;
        generateButton.style.backgroundColor = '';
        generateButton.textContent = '✨ Generate Edits ✨';
    });

    function updateGenerateButtonText() {
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        generateButton.textContent = `🔄 Generating Edits... ${elapsedSeconds}s 🔄`;
    }
}

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

function analyzeConflicts() {
    const analyzeButton = document.getElementById('analyzeConflicts');
    const resultsDiv = document.getElementById('conflictResults');
    let startTime = Date.now();
    let timerInterval;

    // Disable the button and show loading state
    analyzeButton.disabled = true;
    analyzeButton.style.backgroundColor = 'gray';
    updateButtonText();

    // Start the timer
    timerInterval = setInterval(updateButtonText, 1000);

    // Call the analyze_conflicts endpoint
    fetch('/analyze_conflicts', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Parse the summary using marked and create HTML
            const summaryHtml = marked.parse(data.summary);
            resultsDiv.innerHTML = `
                <h3>Conflict Analysis Results:</h3>
                <div class="markdown-content">${summaryHtml}</div>
            `;
        } else {
            resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        resultsDiv.innerHTML = `<p>Error analyzing conflicts: ${error.message}</p>`;
    })
    .finally(() => {
        // Stop the timer and reset the button
        clearInterval(timerInterval);
        analyzeButton.disabled = false;
        analyzeButton.style.backgroundColor = '';
        analyzeButton.textContent = '✨ Analyze Claim Edits for Conflicting Logic ✨';
    });

    function updateButtonText() {
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        analyzeButton.textContent = `🔄 Analyzing Claim Edits for Conflicting Logic... ${elapsedSeconds} 🔄`;
    }
}