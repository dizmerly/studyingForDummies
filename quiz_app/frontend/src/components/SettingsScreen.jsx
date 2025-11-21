import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Key, Save, Trash2, ExternalLink, AlertCircle, CheckCircle } from 'lucide-react';
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function SettingsScreen({ onBack }) {
    const [apiKey, setApiKey] = useState('');
    const [hasKey, setHasKey] = useState(false);
    const [detectedProvider, setDetectedProvider] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        checkExistingKey();
    }, []);

    const checkExistingKey = async () => {
        try {
            const result = await api.checkApiKey();
            setHasKey(result.hasKey);
        } catch (err) {
            console.error('Failed to check API key:', err);
        }
    };

    const detectProvider = (key) => {
        if (key.startsWith('sk-ant-')) return 'Claude (Anthropic)';
        if (key.startsWith('AIza')) return 'Gemini (Google)';
        if (key === 'ollama' || key.startsWith('ollama')) return 'Ollama (Local)';
        if (key.startsWith('sk-')) return 'OpenAI (GPT)';
        return 'Unknown';
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            await api.saveApiKey(apiKey);
            const provider = detectProvider(apiKey);
            setDetectedProvider(provider);
            setSuccess(`API key saved successfully! Detected: ${provider}`);
            setHasKey(true);
            setApiKey('');
            setTimeout(() => setSuccess(''), 5000);
        } catch (err) {
            setError(err.message || 'Failed to save API key');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete your API key?')) return;

        setError('');
        setSuccess('');
        setLoading(true);

        try {
            await api.deleteApiKey();
            setSuccess('API key deleted successfully');
            setHasKey(false);
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError(err.message || 'Failed to delete API key');
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-2xl mx-auto"
        >
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <SettingsIcon className="w-8 h-8 text-primary" />
                    <h1 className="text-3xl font-bold">Settings</h1>
                </div>

                {/* API Key Section */}
                <div className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Key className="w-5 h-5 text-secondary" />
                        <h2 className="text-xl font-semibold">OpenAI API Key</h2>
                    </div>

                    <div className="info-box mb-4">
                        <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <div className="text-sm">
                            <p className="mb-2">
                                Enter your API key from any supported provider:
                            </p>
                            <ul className="list-disc list-inside space-y-1 mb-2">
                                <li><strong>OpenAI</strong> (sk-...) - <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Get key</a></li>
                                <li><strong>Claude</strong> (sk-ant-...) - <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Get key</a></li>
                                <li><strong>Gemini</strong> (AIza...) - <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Get key</a></li>
                                <li><strong>Ollama</strong> (ollama) - Free local AI, no key needed!</li>
                            </ul>
                            <p className="text-xs text-secondary">
                                The app will auto-detect your provider based on the key format.
                            </p>
                        </div>
                    </div>

                    {hasKey && (
                        <div className="success-box mb-4">
                            <CheckCircle className="w-5 h-5 flex-shrink-0" />
                            <span className="text-sm">API key configured</span>
                        </div>
                    )}

                    <form onSubmit={handleSave} className="space-y-4">
                        <div>
                            <label htmlFor="apiKey" className="block text-sm font-medium mb-2">
                                {hasKey ? 'Update API Key' : 'Enter API Key'}
                            </label>
                            <input
                                type="password"
                                id="apiKey"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="sk-..."
                                className="w-full"
                                disabled={loading}
                            />
                        </div>

                        {error && (
                            <div className="error-box">
                                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}

                        {success && (
                            <div className="success-box">
                                <CheckCircle className="w-5 h-5 flex-shrink-0" />
                                <span>{success}</span>
                            </div>
                        )}

                        <div className="flex gap-3">
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={loading || !apiKey}
                            >
                                <Save className="w-4 h-4" />
                                <span>{hasKey ? 'Update Key' : 'Save Key'}</span>
                            </button>

                            {hasKey && (
                                <button
                                    type="button"
                                    onClick={handleDelete}
                                    className="btn btn-secondary"
                                    disabled={loading}
                                >
                                    <Trash2 className="w-4 h-4" />
                                    <span>Delete Key</span>
                                </button>
                            )}
                        </div>
                    </form>

                    <div className="warning-box mt-4">
                        <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                        <div className="text-sm">
                            <p className="font-medium mb-1">Security Notice</p>
                            <p>
                                Your API key is encrypted and stored securely. It's only used server-side and never exposed to the frontend.
                            </p>
                        </div>
                    </div>
                </div>

                <button onClick={onBack} className="btn btn-secondary">
                    Back
                </button>
            </div>
        </motion.div>
    );
}
