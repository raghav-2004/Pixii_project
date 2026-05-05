const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const imagePreview = document.getElementById('image-preview');
const generateBtn = document.getElementById('generate-btn');
const processingSection = document.getElementById('processing-section');
const resultSection = document.getElementById('result-section');
const uploadSection = document.querySelector('.upload-section');

let selectedFile = null;

// Drag and drop handling
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--primary)';
});

dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--border)';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border)';
    if (e.dataTransfer.files.length) {
        handleFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }
    
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreview.classList.remove('hidden');
        generateBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

// Simulated Step progression
const steps = ['step-bg', 'step-cap', 'step-prompt', 'step-gen'];
let stepInterval;

function startStepAnimation() {
    let currentStep = 0;
    document.getElementById(steps[currentStep]).classList.add('active');
    
    stepInterval = setInterval(() => {
        if (currentStep < steps.length - 1) {
            document.getElementById(steps[currentStep]).classList.remove('active');
            currentStep++;
            document.getElementById(steps[currentStep]).classList.add('active');
            
            const texts = [
                "Removing background...",
                "Analyzing product...",
                "Generating perfect prompt...",
                "Applying studio lighting..."
            ];
            document.getElementById('status-text').innerText = texts[currentStep];
        }
    }, 4000); // Change step visual every 4s
}

generateBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    uploadSection.classList.add('hidden');
    processingSection.classList.remove('hidden');
    startStepAnimation();

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('http://localhost:8000/generate-marketing-image', {
            method: 'POST',
            body: formData
        });

        clearInterval(stepInterval);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process image');
        }

        const data = await response.json();
        
        // Show Results
        processingSection.classList.add('hidden');
        resultSection.classList.remove('hidden');
        
        document.getElementById('final-image').src = data.image;
        document.getElementById('result-caption').innerText = data.caption;
        document.getElementById('result-prompt').innerText = data.prompt;

    } catch (error) {
        clearInterval(stepInterval);
        alert(`Error: ${error.message}`);
        location.reload();
    }
});
