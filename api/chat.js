/**
 * Vercel Serverless: AI-чатбот (MiniMax API)
 * Скилл: https://github.com/evgyur/cursor-ai-chatbot
 *
 * В настройках Vercel добавь переменную: MINIMAX_API_KEY
 */

const path = require('path');
const fs = require('fs');

function getKnowledge() {
  try {
    const p = path.join(__dirname, '..', 'knowledge.json');
    const raw = fs.readFileSync(p, 'utf8');
    const arr = JSON.parse(raw);
    return Array.isArray(arr)
      ? arr.map((x) => (typeof x === 'string' ? x : `${x.q || ''}: ${x.a || ''}`)).join('\n\n')
      : String(raw);
  } catch {
    return 'Консультант: Никифор Удалой. Связь: contact@example.com, LinkedIn, Twitter.';
  }
}

const KNOWLEDGE = getKnowledge();
const SYSTEM_PROMPT = `Ты вежливый консультант по имени Никифор Удалой на сайте-визитке.

ПРАВИЛА:
1. Отвечай ТОЛЬКО на основе информации ниже.
2. Не выдумывай услуги, цены или факты.
3. Если информации нет — скажи "Уточните, пожалуйста, у меня нет этих данных" и предложи связаться по контактам с сайта.
4. Отвечай кратко, по-русски.
5. В конце при необходимости предлагай написать на email или в соцсети.

Данные:
${KNOWLEDGE}`;

async function callMiniMax(apiKey, userMessage) {
  const url = 'https://api.minimax.io/v1/text/chatcompletion_v2';
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'M2-her',
      messages: [
        { role: 'system', name: 'Assistant', content: SYSTEM_PROMPT },
        { role: 'user', name: 'User', content: userMessage },
      ],
      temperature: 0.7,
      max_completion_tokens: 1024,
    }),
  });

  const raw = await res.text();
  if (!res.ok) throw new Error(raw || `API ${res.status}`);

  const data = JSON.parse(raw);
  if (data.base_resp && data.base_resp.status_code !== 0) {
    throw new Error(data.base_resp.status_msg || 'MiniMax API error');
  }

  const choice = data.choices && data.choices[0];
  const content =
    choice?.message?.content ??
    choice?.message?.text ??
    choice?.text ??
    data.reply ??
    (typeof data.choices?.[0] === 'string' ? data.choices[0] : '');
  const text = (content && (typeof content === 'string' ? content : content.text || content.content)) || '';
  return text.trim() || 'Не удалось получить ответ. Попробуйте ещё раз или напишите на контакты с сайта.';
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.MINIMAX_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'Сервер: не задан MINIMAX_API_KEY' });
  }

  const { message } = req.body || {};
  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'Нет сообщения' });
  }

  try {
    const response = await callMiniMax(apiKey, message.trim());
    return res.status(200).json({ response });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: err.message || 'Ошибка запроса к AI' });
  }
};
