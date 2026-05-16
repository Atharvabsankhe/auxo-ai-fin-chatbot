import './style.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const reportList = document.getElementById('report-list');
const heroSection = document.getElementById('hero-section');
const newChatBtn = document.querySelector('.new-chat-btn');
const actionButtons = document.querySelectorAll('.action-btn');

// API Configuration - empty string for relative paths in production
const API_BASE = window.location.origin === 'http://localhost:5173' ? 'http://127.0.0.1:8000' : '';

function addMessage(content, isUser = false) {
  // Hide hero on first message
  if (heroSection) {
    heroSection.style.display = 'none';
  }

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  
  if (isUser) {
    contentDiv.textContent = content;
  } else {
    const rawHtml = marked.parse(content);
    contentDiv.innerHTML = DOMPurify.sanitize(rawHtml);
  }
  
  messageDiv.appendChild(contentDiv);
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addLoadingIndicator() {
  const loadingDiv = document.createElement('div');
  loadingDiv.id = 'loading-indicator';
  loadingDiv.className = 'message bot-message';
  loadingDiv.innerHTML = `
    <div class="message-content">
      <div class="typing">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
    </div>
  `;
  chatMessages.appendChild(loadingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return loadingDiv;
}

function addReportLink(filename, url) {
  const emptyState = reportList.querySelector('.empty-state');
  if (emptyState) emptyState.remove();

  const li = document.createElement('li');
  li.className = 'nav-item';
  const icon = filename.endsWith('.pdf') ? '📄' : '📊';
  li.innerHTML = `
    <a href="${API_BASE}${url}" target="_blank" class="report-link" style="text-decoration: none; color: inherit; display: flex; align-items: center; gap: 12px;">
      <span class="icon">${icon}</span>
      <span>${filename}</span>
    </a>
  `;
  reportList.prepend(li);
}

async function handleChat(query) {
  if (!query) return;

  userInput.value = '';
  addMessage(query, true);
  const loadingIndicator = addLoadingIndicator();

  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) throw new Error('API Error');
    const data = await response.json();
    loadingIndicator.remove();
    addMessage(data.answer);

    if (data.file_path && data.file_url) {
      const filename = data.file_path.split('/').pop();
      addReportLink(filename, data.file_url);
    }
  } catch (error) {
    loadingIndicator.remove();
    addMessage('Sorry, I encountered an error. Please make sure the backend server is running.');
  }
}

chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  handleChat(userInput.value.trim());
});

// Quick Action Buttons
actionButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    handleChat(btn.dataset.query);
  });
});

// New Chat Button
newChatBtn.addEventListener('click', () => {
  chatMessages.innerHTML = '';
  chatMessages.appendChild(heroSection);
  heroSection.style.display = 'flex';
});

userInput.focus();
