const API_BASE = 'http://localhost:5001/api';

const defaultHeaders = {
    'Content-Type': 'application/json',
};

const fetchWithCredentials = async (url, options = {}) => {
    const response = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Request failed');
    }

    return response.json();
};

export const api = {
    // Authentication
    async checkAuth() {
        return fetchWithCredentials(`${API_BASE}/auth/me`);
    },

    async login(email, password) {
        return fetchWithCredentials(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    async signup(email, password) {
        return fetchWithCredentials(`${API_BASE}/auth/signup`, {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    async logout() {
        return fetchWithCredentials(`${API_BASE}/auth/logout`, {
            method: 'POST',
        });
    },

    // Quiz operations
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'include',
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        return response.json();
    },

    async pasteText(text) {
        return fetchWithCredentials(`${API_BASE}/paste`, {
            method: 'POST',
            body: JSON.stringify({ text }),
        });
    },

    async getQuestion() {
        return fetchWithCredentials(`${API_BASE}/question`);
    },

    async checkAnswer(answer) {
        return fetchWithCredentials(`${API_BASE}/answer`, {
            method: 'POST',
            body: JSON.stringify({ answer }),
        });
    },

    async getResults() {
        return fetchWithCredentials(`${API_BASE}/results`);
    },

    async restartQuiz() {
        return fetchWithCredentials(`${API_BASE}/restart`, {
            method: 'POST',
        });
    },

    async resetQuiz() {
        return fetchWithCredentials(`${API_BASE}/reset`, {
            method: 'POST',
        });
    },

    // AI Settings
    async saveApiKey(apiKey) {
        return fetchWithCredentials(`${API_BASE}/settings/api-key`, {
            method: 'POST',
            body: JSON.stringify({ apiKey }),
        });
    },

    async checkApiKey() {
        return fetchWithCredentials(`${API_BASE}/settings/api-key`);
    },

    async deleteApiKey() {
        return fetchWithCredentials(`${API_BASE}/settings/api-key`, {
            method: 'DELETE',
        });
    },

    // AI Generation
    async generateQuizWithAI(notes, numQuestions = 10, difficulty = 'medium') {
        return fetchWithCredentials(`${API_BASE}/ai/generate-quiz`, {
            method: 'POST',
            body: JSON.stringify({ notes, numQuestions, difficulty }),
        });
    },

    async chatWithAssistant(message, context = '', history = []) {
        return fetchWithCredentials(`${API_BASE}/ai/chat`, {
            method: 'POST',
            body: JSON.stringify({ message, context, history }),
        });
    },

    // History
    async getHistory() {
        return fetchWithCredentials(`${API_BASE}/history`);
    },
};
