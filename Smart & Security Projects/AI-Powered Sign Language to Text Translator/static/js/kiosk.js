/* kiosk.js — Kiosk mode: auto-reset on inactivity */

const TIMEOUT = typeof KIOSK_TIMEOUT !== 'undefined' ? KIOSK_TIMEOUT : 60000;
let inactivityTimer = null;

function resetKiosk() {
    const signLabel = document.getElementById('signLabel');
    const currentSentence = document.getElementById('currentSentence');
    const confidenceLevel = document.getElementById('confidenceLevel');

    if (signLabel) signLabel.textContent = 'Ready';
    if (currentSentence) currentSentence.textContent = 'Show a sign to begin...';
    if (confidenceLevel) confidenceLevel.style.width = '0%';
}

function restartTimer() {
    if (inactivityTimer) clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(resetKiosk, TIMEOUT);
}

// Reset timer on any user/sign activity
socket.on('recognition', () => restartTimer());
socket.on('frame', () => restartTimer());
document.addEventListener('touchstart', restartTimer);
document.addEventListener('mousemove', restartTimer);

// Receive camera frames
const cameraFeed = document.getElementById('cameraFeed');
socket.on('frame', (data) => {
    if (data.frame && cameraFeed) {
        updateFrame(cameraFeed, data.frame);
    }
});

// Receive recognition
socket.on('recognition', (data) => {
    const signLabel = document.getElementById('signLabel');
    const confidenceLevel = document.getElementById('confidenceLevel');
    const currentSentence = document.getElementById('currentSentence');

    if (signLabel) signLabel.textContent = data.label;
    if (confidenceLevel) updateConfidenceBar(confidenceLevel, data.confidence);
    if (currentSentence) currentSentence.textContent = data.sentence || '';
});

// Start the inactivity timer
restartTimer();
