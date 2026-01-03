document.getElementById('generateBtn').onclick = async function() {
    const url = document.getElementById('videoUrl').value;
    const loader = document.getElementById('loader');
    const outputContainer = document.getElementById('outputContainer');
    const display = document.getElementById('notesDisplay');

    if (!url) {
        alert("Please paste a link first!");
        return;
    }

    // Reset UI
    loader.classList.remove('hidden');
    outputContainer.classList.add('hidden');

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            // Convert Gemini's Markdown to HTML
            display.innerHTML = marked.parse(data.notes);
            outputContainer.classList.remove('hidden');
        }
    } catch (err) {
        alert("Server Error. Check console.");
    } finally {
        loader.classList.add('hidden');
    }
};
