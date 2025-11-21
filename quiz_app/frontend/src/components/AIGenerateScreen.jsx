import { motion } from 'framer-motion';
import { Upload, FileText, Sparkles, Loader2, AlertCircle, Settings as SettingsIcon } from 'lucide-react';
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function AIGenerateScreen({ onQuizGenerated, onBack }) {
    const [notes, setNotes] = useState('');
    const [file, setFile] = useState(null);
    const [numQuestions, setNumQuestions] = useState(10);
    const [difficulty, setDifficulty] = useState('medium');
    const [provider, setProvider] = useState('auto');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [hasApiKey, setHasApiKey] = useState(false);

    useEffect(() => {
        checkApiKey();
    }, []);

    const checkApiKey = async () => {
        try {
            const result = await api.checkApiKey();
            setHasApiKey(result.hasKey);
        } catch (err) {
            console.error('Failed to check API key:', err);
        }
    };

    const handleFileUpload = (e) => {
        const uploadedFile = e.target.files[0];
        if (uploadedFile) {
            setFile(uploadedFile);
            const reader = new FileReader();
            reader.onload = (event) => {
                setNotes(event.target.result);
            };
            reader.readAsText(uploadedFile);
        }
    };

    const handleGenerate = async () => {
        if (!notes.trim()) {
            setError('Please upload or paste your study notes');
            return;
        }

        setError('');
        setLoading(true);

        try {
            await api.generateQuizWithAI(notes, numQuestions, difficulty);
            onQuizGenerated();
        } catch (err) {
            setError(err.message || 'Failed to generate quiz');
        } finally {
            setLoading(false);
        }
    };

    if (!hasApiKey) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-2xl mx-auto"
            >
                <div className="card text-center">
                    <SettingsIcon className="w-16 h-16 text-secondary mx-auto mb-4" />
                    <h2 className="text-2xl font-bold mb-4">API Key Required</h2>
                    <p className="text-secondary mb-6">
                        To use AI quiz generation, you need to configure your API key in Settings.
                    </p>
                    <div className="flex gap-3 justify-center">
                        <button onClick={() => window.location.hash = '#settings'} className="btn btn-primary">
                            <SettingsIcon className="w-4 h-4" />
                            <span>Go to Settings</span>
                        </button>
                        <button onClick={onBack} className="btn btn-secondary">
                            Back
                        </button>
                    </div>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-4xl mx-auto"
        >
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <Sparkles className="w-8 h-8 text-primary" />
                    <h1 className="text-3xl font-bold">AI Quiz Generator</h1>
                </div>

                <p className="text-secondary mb-6">
                    Upload or paste your study notes, and AI will automatically generate quiz questions for you.
                </p>

                {/* File Upload */}
                <div className="mb-6">
                    <label className="block text-sm font-medium mb-2">
                        Upload Notes (Optional)
                    </label>
                    <label className="btn btn-secondary w-full cursor-pointer">
                        <Upload className="w-4 h-4" />
                        <span>{file ? file.name : 'Choose File'}</span>
                        <input
                            type="file"
                            accept=".txt,.md,.pdf"
                            onChange={handleFileUpload}
                            className="hidden"
                        />
                    </label>
                </div>

                {/* Text Area */}
                <div className="mb-6">
                    <label htmlFor="notes" className="block text-sm font-medium mb-2">
                        Or Paste Your Notes
                    </label>
                    <textarea
                        id="notes"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Paste your study notes here...

Example:
Photosynthesis is the process by which plants convert light energy into chemical energy. It occurs in chloroplasts and requires sunlight, water, and carbon dioxide..."
                        rows={12}
                        className="w-full resize-none"
                    />
                </div>

                {/* Settings Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    {/* Number of Questions */}
                    <div>
                        <label htmlFor="numQuestions" className="block text-sm font-medium mb-2">
                            Number of Questions
                        </label>
                        <select
                            id="numQuestions"
                            value={numQuestions}
                            onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                            className="w-full p-2 rounded-lg border border-border bg-background"
                        >
                            <option value={5}>5 Questions</option>
                            <option value={10}>10 Questions</option>
                            <option value={15}>15 Questions</option>
                            <option value={20}>20 Questions</option>
                        </select>
                    </div>

                    {/* Difficulty */}
                    <div>
                        <label htmlFor="difficulty" className="block text-sm font-medium mb-2">
                            Difficulty
                        </label>
                        <select
                            id="difficulty"
                            value={difficulty}
                            onChange={(e) => setDifficulty(e.target.value)}
                            className="w-full p-2 rounded-lg border border-border bg-background"
                        >
                            <option value="easy">Easy</option>
                            <option value="medium">Medium</option>
                            <option value="hard">Hard</option>
                        </select>
                    </div>

                    {/* Provider */}
                    <div>
                        <label htmlFor="provider" className="block text-sm font-medium mb-2">
                            AI Provider
                        </label>
                        <select
                            id="provider"
                            value={provider}
                            onChange={(e) => setProvider(e.target.value)}
                            className="w-full p-2 rounded-lg border border-border bg-background"
                        >
                            <option value="auto">Auto-Detect</option>
                            <option value="openai">OpenAI (GPT-4)</option>
                            <option value="anthropic">Claude (Anthropic)</option>
                            <option value="google">Gemini (Google)</option>
                            <option value="ollama">Ollama (Local)</option>
                        </select>
                    </div>
                </div>

                {error && (
                    <div className="error-box mb-6">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        <span>{error}</span>
                    </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3">
                    <button
                        onClick={handleGenerate}
                        disabled={loading || !notes.trim()}
                        className="btn btn-primary flex-1"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Generating Quiz...</span>
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-4 h-4" />
                                <span>Generate Quiz</span>
                            </>
                        )}
                    </button>

                    <button onClick={onBack} className="btn btn-secondary">
                        Cancel
                    </button>
                </div>

                {/* Info Box */}
                <div className="info-box mt-6">
                    <FileText className="w-5 h-5 text-blue-400 flex-shrink-0" />
                    <div className="text-sm">
                        <p className="font-medium mb-1">Supported Formats</p>
                        <p>
                            Upload .txt, .md, or .pdf files, or paste your notes directly. The AI will analyze your content and generate relevant quiz questions.
                        </p>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
