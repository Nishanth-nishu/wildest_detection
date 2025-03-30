document.addEventListener('DOMContentLoaded', () => {
    const webcamBtn = document.getElementById('webcam-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const videoUpload = document.getElementById('video-upload');
    const emailInput = document.getElementById('email-input');
    const saveEmailBtn = document.getElementById('save-email');

    // Source selection
    webcamBtn.addEventListener('click', () => {
        webcamBtn.classList.add('active');
        uploadBtn.classList.remove('active');
        // Implement webcam start logic
    });

    uploadBtn.addEventListener('click', () => {
        videoUpload.click();
    });

    videoUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadBtn.classList.add('active');
            webcamBtn.classList.remove('active');
            // Implement video upload processing
        }
    });

    // Email configuration
    saveEmailBtn.addEventListener('click', () => {
        const email = emailInput.value.trim();
        if (email.includes('@')) {
            fetch('/set_email', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ email })
            }).then(response => {
                if (response.ok) {
                    alert('Email saved for alerts!');
                }
            });
        } else {
            alert('Please enter a valid email');
        }
    });

    // Periodically update detection list
    setInterval(() => {
        fetch('/detections').then(r => r.json()).then(data => {
            const list = document.getElementById('detection-list');
            list.innerHTML = data.detections.map(d => `
                <div class="detection-item">
                    <span class="species">${d.species}</span>
                    <span class="confidence">${(d.confidence * 100).toFixed(1)}%</span>
                </div>
            `).join('');
        });
    }, 1000);
});