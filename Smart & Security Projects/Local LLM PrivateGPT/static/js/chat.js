/* ─── chat.js — WebSocket chat client + citation rendering ──── */

(function () {
    const socket = io();
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messagesEl = document.getElementById('chat-messages');
    const statusEl = document.getElementById('chat-status');
    const convList = document.getElementById('conversation-list');
    const newConvBtn = document.getElementById('new-conversation-btn');

    let currentConversationId = null;
    let assistantBubble = null;

    // ── Load conversations ──
    function loadConversations() {
        fetch('/chat/conversations')
            .then(r => r.json())
            .then(data => {
                convList.innerHTML = '';
                (data.conversations || []).forEach(c => {
                    const li = document.createElement('li');
                    li.textContent = c.title || 'Untitled';
                    li.addEventListener('click', () => loadConversation(c.id));
                    convList.appendChild(li);
                });
            });
    }

    function loadConversation(id) {
        currentConversationId = id;
        fetch(`/chat/conversations/${id}/messages`)
            .then(r => r.json())
            .then(data => {
                messagesEl.innerHTML = '';
                (data.messages || []).forEach(m => {
                    addBubble(m.role, m.content);
                });
            });
    }

    // ── Chat bubbles ──
    function addBubble(role, text) {
        const div = document.createElement('div');
        div.className = `chat-bubble ${role}`;
        div.textContent = text;
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return div;
    }

    // ── Send message ──
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const question = input.value.trim();
        if (!question) return;

        addBubble('user', question);
        input.value = '';

        // Create assistant bubble for streaming
        assistantBubble = addBubble('assistant', '');

        socket.emit('ask', {
            question: question,
            conversation_id: currentConversationId,
        });
    });

    // ── Socket events ──
    socket.on('status', (data) => {
        statusEl.textContent = data.message || '';
    });

    socket.on('answer_token', (data) => {
        if (assistantBubble) {
            assistantBubble.textContent += data.token;
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
        if (data.done) {
            statusEl.textContent = '';
        }
    });

    socket.on('citations', (data) => {
        if (!data.citations || data.citations.length === 0) return;
        const citDiv = document.createElement('div');
        citDiv.className = 'citations';
        citDiv.innerHTML = '<strong>Sources:</strong>';
        data.citations.forEach(c => {
            const item = document.createElement('div');
            item.className = 'citation-item';
            item.innerHTML = `<span>${escapeHtml(c.document)} — Page ${c.page}</span>` +
                `<div class="citation-passage">${escapeHtml(c.passage)}</div>`;
            item.addEventListener('click', () => item.classList.toggle('expanded'));
            citDiv.appendChild(item);
        });
        messagesEl.appendChild(citDiv);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    });

    socket.on('conversation_created', (data) => {
        currentConversationId = data.conversation_id;
        loadConversations();
    });

    // ── New conversation ──
    newConvBtn.addEventListener('click', () => {
        currentConversationId = null;
        messagesEl.innerHTML = '<div class="chat-welcome"><h2>Ask a question about your documents</h2></div>';
    });

    // ── Init ──
    loadConversations();
})();
