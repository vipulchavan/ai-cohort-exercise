const form = document.querySelector('#chat-form');
const input = document.querySelector('#prompt-input');
const sendButton = document.querySelector('#send-button');
const conversation = document.querySelector('#conversation');
const errorMessage = document.querySelector('#error-message');
const conversationList = document.querySelector('#conversation-list');
const conversationStatus = document.querySelector('#conversation-status');
const newChatButton = document.querySelector('#new-chat-button');
let conversationId = null;
let conversations = [];
let historyDisabled = false;

function addMessage(role, content, tokenUsage = null, createdAt = null) {
  const isAssistant = role === 'assistant';
  const article = document.createElement('article');
  article.className = `message ${isAssistant ? 'assistant-message' : 'user-message'}`;

  const avatar = document.createElement('div');
  avatar.className = `avatar ${isAssistant ? 'assistant-avatar' : 'user-avatar'}`;
  avatar.setAttribute('aria-hidden', 'true');
  avatar.textContent = isAssistant ? 'H' : 'Y';

  const body = document.createElement('div');
  body.className = 'message-body';
  const meta = document.createElement('div');
  meta.className = 'message-meta';
  const name = document.createElement('span');
  name.textContent = isAssistant ? 'HR Assistant' : 'You';
  const time = document.createElement('time');
  const timestamp = createdAt ? new Date(createdAt) : new Date();
  time.textContent = Number.isNaN(timestamp.getTime())
    ? ''
    : new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(timestamp);
  const text = document.createElement('p');
  text.className = 'message-text';
  text.textContent = content;

  meta.append(name, time);
  body.append(meta, text);
  if (isAssistant && tokenUsage) {
    const usage = document.createElement('p');
    usage.className = 'token-usage';
    usage.textContent = `Total Tokens used for this turn : ${tokenUsage.total_tokens}\nTotal Tokens used so far : ${tokenUsage.total_tokens_used}`;
    body.append(usage);
  }
  article.append(avatar, body);
  conversation.append(article);
  conversation.scrollTop = conversation.scrollHeight;
  return article;
}

function showWelcome() {
  conversation.replaceChildren();
  addMessage('assistant', "Hi, I'm your HR assistant. What can I help you with today?");
}

function setHistoryDisabled(disabled) {
  historyDisabled = disabled;
  newChatButton.disabled = disabled;
  conversationList.querySelectorAll('button').forEach((button) => {
    button.disabled = disabled;
  });
}

function renderConversationList() {
  conversationList.replaceChildren();
  conversationStatus.textContent = conversations.length ? '' : 'No saved conversations yet.';

  conversations.forEach((item) => {
    const button = document.createElement('button');
    button.className = 'sidebar-conversation';
    button.type = 'button';
    button.disabled = historyDisabled;
    if (item.id === conversationId) button.setAttribute('aria-current', 'page');

    const title = document.createElement('span');
    title.className = 'sidebar-conversation-title';
    title.textContent = item.title || 'Untitled conversation';

    const date = document.createElement('span');
    date.className = 'sidebar-conversation-date';
    const createdAt = new Date(item.created_at);
    date.textContent = Number.isNaN(createdAt.getTime())
      ? ''
      : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(createdAt);

    button.append(title, date);
    button.addEventListener('click', () => openConversation(item));
    conversationList.append(button);
  });
}

async function loadConversations() {
  conversationStatus.textContent = 'Loading conversations...';
  try {
    const response = await fetch('/conversations');
    if (!response.ok) throw new Error('Could not load conversations.');
    conversations = await response.json();
    renderConversationList();
  } catch (error) {
    conversationStatus.textContent = error.message || 'Could not load conversations.';
  }
}

async function openConversation(item) {
  errorMessage.hidden = true;
  sendButton.disabled = true;
  setHistoryDisabled(true);
  try {
    const response = await fetch(`/conversations/${item.id}/messages`);
    const messages = await response.json();
    if (!response.ok) throw new Error(messages.detail || 'Could not load this conversation.');

    conversationId = item.id;
    renderConversationList();
    conversation.replaceChildren();
    if (messages.length === 0) showWelcome();
    messages.forEach((message) => addMessage(message.role, message.text, null, message.created_at));
  } catch (error) {
    errorMessage.textContent = error.message || 'Could not load this conversation.';
    errorMessage.hidden = false;
  } finally {
    sendButton.disabled = false;
    setHistoryDisabled(false);
  }
}

function showTyping() {
  const article = document.createElement('article');
  article.className = 'message assistant-message';
  article.setAttribute('aria-label', 'Assistant is responding');
  article.innerHTML = '<div class="avatar assistant-avatar" aria-hidden="true">H</div><div class="message-body"><div class="message-meta"><span>HR Assistant</span></div><div class="typing-indicator" aria-hidden="true"><span></span><span></span><span></span></div></div>';
  conversation.append(article);
  conversation.scrollTop = conversation.scrollHeight;
  return article;
}

newChatButton.addEventListener('click', () => {
  conversationId = null;
  renderConversationList();
  showWelcome();
  errorMessage.hidden = true;
  input.focus();
});

input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
});

input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const userInput = input.value.trim();
  if (!userInput || sendButton.disabled) return;

  errorMessage.hidden = true;
  addMessage('user', userInput);
  input.value = '';
  input.style.height = 'auto';
  sendButton.disabled = true;
  setHistoryDisabled(true);
  const typingMessage = showTyping();

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: userInput, conversation_id: conversationId }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || result.error || 'The assistant could not respond.');
    conversationId = result.conversation_id;
    typingMessage.remove();
    addMessage('assistant', result.content, result);
    await loadConversations();
  } catch (error) {
    typingMessage.remove();
    errorMessage.textContent = error.message || 'Unable to reach the assistant. Please try again.';
    errorMessage.hidden = false;
  } finally {
    sendButton.disabled = false;
    setHistoryDisabled(false);
    input.focus();
  }
});

loadConversations();
