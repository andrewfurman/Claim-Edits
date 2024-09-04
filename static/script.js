document.addEventListener('DOMContentLoaded', function() {
    const summaries = document.querySelectorAll('.editable-summary');
    summaries.forEach(setupEditableSummary);
});

function setupEditableSummary(summary) {
    const markdownContent = summary.querySelector('.markdown-content');
    const markdownSource = summary.querySelector('.markdown-source');

    if (markdownContent && markdownSource) {
        markdownContent.innerHTML = marked.parse(markdownSource.textContent);
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
            summaryElement.innerHTML = `
                <div class="markdown-content">${marked.parse(data.summary)}</div>
                <div class="markdown-source" style="display: none;">${data.summary}</div>
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