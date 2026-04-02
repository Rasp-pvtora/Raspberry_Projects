/* learning.js — Learning mode: prompts, grading, progress */

const btnStart = document.getElementById('btnStart');
const btnNext = document.getElementById('btnNext');
const promptWord = document.getElementById('promptWord');
const gradeResult = document.getElementById('gradeResult');
const difficultySelect = document.getElementById('difficulty');
const progressTable = document.getElementById('progressTable');

let currentPrompt = null;
let practicing = false;

if (btnStart) {
    btnStart.addEventListener('click', startPractice);
}
if (btnNext) {
    btnNext.addEventListener('click', nextPrompt);
}

// Listen for recognition during practice
socket.on('recognition', (data) => {
    if (!practicing || !currentPrompt) return;

    // Auto-grade when a sign is recognized
    gradeAttempt(data.label);
});

async function startPractice() {
    practicing = true;
    btnStart.disabled = true;
    btnNext.disabled = false;
    await nextPrompt();
}

async function nextPrompt() {
    gradeResult.textContent = '—';
    gradeResult.className = 'grade-result';

    const difficulty = difficultySelect ? difficultySelect.value : 'alphabet';
    const resp = await fetch('/learning/prompt?difficulty=' + difficulty);
    const data = await resp.json();

    currentPrompt = data.word;
    promptWord.textContent = data.word;
}

async function gradeAttempt(actual) {
    if (!currentPrompt) return;

    const resp = await fetch('/learning/grade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expected: currentPrompt, actual: actual }),
    });
    const data = await resp.json();

    if (data.correct) {
        gradeResult.textContent = 'Correct!';
        gradeResult.className = 'grade-result correct';
    } else {
        gradeResult.textContent = 'Try again — you signed: ' + data.actual;
        gradeResult.className = 'grade-result incorrect';
    }

    loadProgress();
}

async function loadProgress() {
    const resp = await fetch('/learning/progress');
    const data = await resp.json();

    if (!progressTable || data.length === 0) return;

    let html = '<table><tr><th>Sign</th><th>Attempts</th><th>Correct</th><th>Accuracy</th></tr>';
    data.forEach((row) => {
        const acc = row.attempts > 0 ? Math.round((row.correct / row.attempts) * 100) : 0;
        html += '<tr><td>' + row.sign_label + '</td><td>' + row.attempts +
            '</td><td>' + row.correct + '</td><td>' + acc + '%</td></tr>';
    });
    html += '</table>';
    progressTable.innerHTML = html;
}

// Load progress on page load
loadProgress();
