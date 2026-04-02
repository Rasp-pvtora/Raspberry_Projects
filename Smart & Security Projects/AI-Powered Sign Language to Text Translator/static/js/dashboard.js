/* dashboard.js — Live recognition feed and hand skeleton overlay */

const cameraFeed = document.getElementById('cameraFeed');
const signLabel = document.getElementById('signLabel');
const confidenceLevel = document.getElementById('confidenceLevel');
const confidenceText = document.getElementById('confidenceText');
const currentSentence = document.getElementById('currentSentence');
const sentenceHistory = document.getElementById('sentenceHistory');

// Receive camera frames
socket.on('frame', (data) => {
    if (data.frame && cameraFeed) {
        updateFrame(cameraFeed, data.frame);
    }
});

// Receive recognition results
socket.on('recognition', (data) => {
    if (signLabel) signLabel.textContent = data.label;
    if (confidenceLevel) updateConfidenceBar(confidenceLevel, data.confidence);
    if (confidenceText) confidenceText.textContent = Math.round(data.confidence * 100) + '%';
    if (currentSentence) currentSentence.textContent = data.sentence || 'Waiting for signs...';
});

// Receive finalized sentences
socket.on('sentence', (data) => {
    if (sentenceHistory) {
        const p = document.createElement('p');
        p.textContent = data.sentence;
        sentenceHistory.prepend(p);
    }
    if (currentSentence) currentSentence.textContent = 'Waiting for signs...';
});
