import React, { useState } from 'react';
import { Upload, FileText, Loader2, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import { motion } from 'framer-motion';

export default function StartScreen({ onQuizStart, onAIGenerate }) {
    const [loading, setLoading] = useState(false);
    const [pasteMode, setPasteMode] = useState(false);
    const [text, setText] = useState('');
    const [error, setError] = useState('');

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setLoading(true);
        setError('');
        try {
            const data = await api.uploadFile(file);
            onQuizStart(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handlePasteSubmit = async () => {
        if (!text.trim()) return;

        setLoading(true);
        setError('');
        try {
            const data = await api.pasteText(text);
            onQuizStart(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card max-w-lg mx-auto w-full text-center"
        >
            <h1 className="text-3xl font-bold mb-2 gradient-text">
                Studying For Dummies
            </h1>
            <p className="text-secondary mb-8">Upload a file or paste text to generate a quiz.</p>

            {error && (
                <div className="error-box">
                    {error}
                </div>
            )}

            {!pasteMode ? (
                <div className="flex flex-col gap-4">
                    <label className="w-full">
                        <input
                            type="file"
                            className="hidden"
                            onChange={handleFileUpload}
                            accept=".txt,.md"
                            style={{ display: 'none' }}
                        />
                        <div className="btn btn-primary w-full cursor-pointer">
                            {loading ? (
                                <Loader2 className="animate-spin" />
                            ) : (
                                <>
                                    <Upload />
                                    <span>Upload File</span>
                                </>
                            )}
                        </div>
                    </label>

                    <div className="divider">
                        <div className="divider-line"></div>
                        <div className="divider-text">Or</div>
                    </div>

                    <button
                        onClick={() => setPasteMode(true)}
                        className="btn btn-secondary w-full"
                    >
                        <FileText />
                        <span>Paste Text</span>
                    </button>

                    {onAIGenerate && (
                        <>
                            <div className="divider">
                                <div className="divider-line"></div>
                                <div className="divider-text">Or</div>
                            </div>

                            <button
                                onClick={onAIGenerate}
                                className="btn w-full"
                                style={{
                                    background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)',
                                    color: 'white',
                                    border: 'none'
                                }}
                            >
                                <Sparkles />
                                <span>Generate with AI</span>
                            </button>
                        </>
                    )}
                </div>
            ) : (
                <div className="flex flex-col gap-4 text-left">
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Paste your quiz content here..."
                        rows={8}
                        className="resize-none"
                        autoFocus
                    />
                    <div className="flex gap-3">
                        <button
                            onClick={() => setPasteMode(false)}
                            className="btn btn-secondary flex-1"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handlePasteSubmit}
                            disabled={loading || !text.trim()}
                            className="btn btn-primary flex-1"
                        >
                            {loading ? (
                                <Loader2 className="animate-spin" />
                            ) : (
                                <span>Generate Quiz</span>
                            )}
                        </button>
                    </div>
                </div>
            )}
        </motion.div>
    );
}
