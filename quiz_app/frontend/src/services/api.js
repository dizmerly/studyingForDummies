const apiBase = '/api';

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch {
    throw new Error('Could not reach the server. Check that the API is running.');
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Something went wrong. Please try again.');
  }
  return data;
}

export const api = {
  generate(source, settings) {
    return request('/practice-sets/generate', {
      method: 'POST', body: JSON.stringify({ source, settings }),
    });
  },
  getSet(setId) {
    return request(`/practice-sets/${setId}`);
  },
  answer(setId, questionId, choiceId) {
    return request(`/practice-sets/${setId}/answers`, {
      method: 'POST', body: JSON.stringify({ questionId, choiceId }),
    });
  },
  results(setId) {
    return request(`/practice-sets/${setId}/results`);
  },
  retry(setId) {
    return request(`/practice-sets/${setId}/retry`, { method: 'POST' });
  },
};
