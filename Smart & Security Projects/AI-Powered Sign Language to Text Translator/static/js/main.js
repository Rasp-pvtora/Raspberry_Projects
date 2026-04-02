/* main.js — Shared Socket.IO connection and utilities */

const socket = io();

socket.on('connect', () => {
    console.log('WebSocket connected');
});

socket.on('disconnect', () => {
    console.log('WebSocket disconnected');
});

/**
 * Update an image element with a base64-encoded JPEG frame.
 */
function updateFrame(imgElement, base64Data) {
    if (base64Data) {
        imgElement.src = 'data:image/jpeg;base64,' + base64Data;
    }
}

/**
 * Update confidence bar color based on value.
 */
function updateConfidenceBar(barElement, confidence) {
    const pct = Math.round(confidence * 100);
    barElement.style.width = pct + '%';

    barElement.classList.remove('medium', 'low');
    if (confidence < 0.5) {
        barElement.classList.add('low');
    } else if (confidence < 0.75) {
        barElement.classList.add('medium');
    }
}
