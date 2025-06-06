document.addEventListener('DOMContentLoaded', function() {
            const uploadForm = document.getElementById('uploadForm');
            const documentFile = document.getElementById('documentFile');
            const uploadStatus = document.getElementById('uploadStatus');
            const uploadSpinner = document.getElementById('uploadSpinner');
            const featureButtons = document.querySelectorAll('.feature-button');
            const outputAreas = {
                summary: document.getElementById('summaryOutput'),
                flashcards: document.getElementById('flashcardsOutput'),
                qna: document.getElementById('qnaOutput'),
                mindmap: document.getElementById('mindMapOutput')
            };
            const spinners = {
                summary: document.getElementById('summarySpinner'),
                flashcards: document.getElementById('flashcardsSpinner'),
                qna: document.getElementById('qnaSpinner'),
                mindmap: document.getElementById('mindmapSpinner')
            };

            const queryDocumentButton = document.getElementById('queryDocumentButton');
            const userQueryInput = document.getElementById('userQueryInput');
            const queryOutput = document.getElementById('queryOutput');
            const querySpinner = document.getElementById('querySpinner');

            let documentId = null;

            uploadForm.addEventListener('submit', function(e) {
                e.preventDefault();

                const file = documentFile.files[0];
                if (!file) {
                    uploadStatus.textContent = 'Please select a file to upload.';
                    uploadStatus.style.color = 'red';
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                // Disable upload button and show spinner
                uploadForm.querySelector('button[type="submit"]').disabled = true;
                uploadSpinner.style.display = 'block';
                uploadStatus.textContent = 'Uploading and processing... This may take a moment.';
                uploadStatus.style.color = 'blue';

                // Clear previous outputs when a new document is uploaded
                for (const key in outputAreas) {
                    outputAreas[key].innerHTML = '';
                    spinners[key].style.display = 'none';
                }
                queryOutput.innerHTML = '';
                querySpinner.style.display = 'none';


                fetch('/upload', {
                    method: 'POST',
                    body: formData,
                })
                .then(response => response.json())
                .then(data => {
                    uploadSpinner.style.display = 'none';
                    uploadForm.querySelector('button[type="submit"]').disabled = false;
                    if (data.error) {
                        uploadStatus.textContent = `Error: ${data.error}`;
                        uploadStatus.style.color = 'red';
                    } else {
                        documentId = data.document_id;
                        uploadStatus.textContent = data.message;
                        uploadStatus.style.color = 'green';
                        // Enable feature buttons once document is processed
                        featureButtons.forEach(button => button.disabled = false);
                        queryDocumentButton.disabled = false; // Enable query button
                    }
                })
                .catch(error => {
                    uploadSpinner.style.display = 'none';
                    uploadForm.querySelector('button[type="submit"]').disabled = false;
                    uploadStatus.textContent = `Upload failed: ${error}`;
                    uploadStatus.style.color = 'red';
                    console.error('Error during upload:', error);
                });
            });

            featureButtons.forEach(button => {
                button.addEventListener('click', function() {
                    if (!documentId) {
                        alert("Please upload a document first!");
                        return;
                    }

                    const feature = this.dataset.feature;
                    const apiUrl = `/generate_${feature}/${documentId}`;
                    const outputElement = outputAreas[feature];
                    const spinnerElement = spinners[feature];

                    // Disable current button, show spinner, clear output
                    this.disabled = true;
                    outputElement.innerHTML = '';
                    spinnerElement.style.display = 'block';

                    fetch(apiUrl)
                        .then(response => {
                            if (!response.ok) {
                                return response.json().then(errData => {
                                    throw new Error(errData.error || `HTTP error! status: ${response.status}`);
                                });
                            }
                            return response.json();
                        })
                        .then(data => {
                            spinnerElement.style.display = 'none';
                            this.disabled = false;

                            if (data.error) {
                                outputElement.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                                return;
                            }

                            // Handle different data types for different features
                            if (feature === 'summary' && data.summary) {
                                outputElement.innerHTML = `<p>${data.summary}</p>`;
                            } else if (feature === 'flashcards' && data.flashcards && Array.isArray(data.flashcards)) {
                                if (data.flashcards.length === 0) {
                                    outputElement.innerHTML = '<p>No flashcards generated.</p>';
                                } else {
                                    let html = '<h5>Generated Flashcards:</h5><div id="flashcardsCarousel" class="carousel slide" data-bs-ride="carousel" data-bs-interval="false">';
                                    html += '<div class="carousel-inner">';
                                    data.flashcards.forEach((card, index) => {
                                        // Process details to show as bullet points or paragraphs
                                        let detailsContent = '';
                                        // Check if details contains newline characters (typical for bullet points from LLM)
                                        if (card.details && card.details.includes('\n')) {
                                            detailsContent = '<ul>';
                                            card.details.split('\n').forEach(line => {
                                                const trimmedLine = line.trim();
                                                if (trimmedLine) {
                                                    // Remove leading bullets if present (e.g., "- Point")
                                                    detailsContent += `<li>${trimmedLine.startsWith('- ') ? trimmedLine.substring(2) : trimmedLine}</li>`;
                                                }
                                            });
                                            detailsContent += '</ul>';
                                        } else if (card.details) {
                                            detailsContent = `<p>${card.details}</p>`;
                                        }


                                        html += `
                                            <div class="carousel-item ${index === 0 ? 'active' : ''}">
                                                <div class="flashcard-container">
                                                    <div class="flashcard-flipper">
                                                        <div class="flashcard-front">
                                                            <p><strong>${card.concept || 'Undefined Concept'}</strong></p>
                                                        </div>
                                                        <div class="flashcard-back">
                                                            ${detailsContent || '<p>No details provided.</p>'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        `;
                                    });
                                    outputElement.innerHTML = html;

                                    // Add event listeners to flip flashcards
                                    document.querySelectorAll('.flashcard-container').forEach(card => {
                                        card.addEventListener('click', function() {
                                            this.classList.toggle('flipped');
                                        });
                                    });
                                }
                            } else if (feature === 'qna' && data.qa_pairs && Array.isArray(data.qa_pairs)) {
                                if (data.qa_pairs.length === 0) {
                                    outputElement.innerHTML = '<p>No Q&A pairs generated.</p>';
                                } else {
                                    let html = '<h5>Generated Q&A Pairs:</h5>';
                                    data.qa_pairs.forEach((qa, index) => {
                                        html += `<div class="card mb-2"><div class="card-body"><strong>Q${index + 1}:</strong> ${qa.question}<br><strong>A${index + 1}:</strong> ${qa.answer}</div></div>`;
                                    });
                                    outputElement.innerHTML = html;
                                }
                            } else if (feature === 'mindmap' && data.mind_map_data) {
                                if (data.mind_map_data.startsWith('data:image/png;base64,')) {
                                    outputElement.innerHTML = `<img src="${data.mind_map_data}" alt="Mind Map" class="img-fluid">`;
                                } else {
                                    outputElement.innerHTML = `<p style="color: red;">Error: Mind map data is not a valid image. Received: ${data.mind_map_data.substring(0, 100)}...</p>`;
                                }
                            } else {
                                outputElement.innerHTML = '<p>No content generated or unexpected format.</p>';
                            }
                        })
                        .catch(error => {
                            spinnerElement.style.display = 'none';
                            this.disabled = false;
                            console.error(`Error generating ${feature}:`, error);
                            outputElement.innerHTML = `<p style="color: red;">Failed to generate ${feature}: ${error.message || error}. Please check server logs.</p>`;
                        });
                });
            });

            // Event listener for the "Ask Document" button
            if (queryDocumentButton) {
                queryDocumentButton.addEventListener('click', function() {
                    if (!documentId) {
                        alert("Please upload a document first!");
                        return;
                    }

                    const userQuery = userQueryInput.value.trim();
                    if (!userQuery) {
                        alert("Please enter a question!");
                        return;
                    }

                    const apiUrl = `/query_document/${documentId}`;

                    // Disable button, show spinner, clear output
                    this.disabled = true;
                    queryOutput.innerHTML = '';
                    querySpinner.style.display = 'block';

                    fetch(apiUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: userQuery })
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(errData => {
                                throw new Error(errData.error || `HTTP error! status: ${response.status}`);
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        querySpinner.style.display = 'none';
                        this.disabled = false;

                        if (data.error) {
                            queryOutput.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                        } else if (data.answer) {
                            queryOutput.innerHTML = `<p><strong>Answer:</strong> ${data.answer}</p>`;
                        } else {
                            queryOutput.innerHTML = '<p>No answer could be generated for your question.</p>';
                        }
                    })
                    .catch(error => {
                        querySpinner.style.display = 'none';
                        this.disabled = false;
                        console.error('Error querying document:', error);
                        queryOutput.innerHTML = `<p style="color: red;">Failed to get answer: ${error.message || error}. Please check server logs.</p>`;
                    });
                });
            }

            // Initially disable feature buttons until a document is uploaded
            featureButtons.forEach(button => button.disabled = true);
            queryDocumentButton.disabled = true; // Disable query button too
        });