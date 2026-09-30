const form = document.querySelector('#chat-form');
const input = document.querySelector('#prompt-input');
const sendButton = document.querySelector('#send-button');
const conversation = document.querySelector('#conversation');
const errorMessage = document.querySelector('#error-message');

function addMessage(role, content, tokenUsage = null) {
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
  time.textContent = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(new Date());
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

function showTyping() {
  const article = document.createElement('article');
  article.className = 'message assistant-message';
  article.setAttribute('aria-label', 'Assistant is responding');
  article.innerHTML = '<div class="avatar assistant-avatar" aria-hidden="true">H</div><div class="message-body"><div class="message-meta"><span>HR Assistant</span></div><div class="typing-indicator" aria-hidden="true"><span></span><span></span><span></span></div></div>';
  conversation.append(article);
  conversation.scrollTop = conversation.scrollHeight;
  return article;
}

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
  const typingMessage = showTyping();

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: userInput }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || result.error || 'The assistant could not respond.');
    typingMessage.remove();
    addMessage('assistant', result.content, result);
  } catch (error) {
    typingMessage.remove();
    errorMessage.textContent = error.message || 'Unable to reach the assistant. Please try again.';
    errorMessage.hidden = false;
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
});
