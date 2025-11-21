import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trash2, ArrowLeft, Calendar, Trophy } from 'lucide-react';

export default function HistoryScreen({ onBack }) {
    const [history, setHistory] = useState([]);

    useEffect(() => {
        const saved = JSON.parse(localStorage.getItem('quizHistory') || '[]');
        setHistory(saved);
    }, []);

    const clearHistory = () => {
        if (confirm('Are you sure you want to clear all quiz history?')) {
            localStorage.removeItem('quizHistory');
            setHistory([]);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-2xl mx-auto"
        >
            <div className="flex items-center justify-between mb-6">
                <button onClick={onBack} className="btn btn-secondary text-sm py-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </button>
                <h2 className="text-xl font-bold">Quiz History</h2>
                <button
                    onClick={clearHistory}
                    disabled={history.length === 0}
                    className="btn btn-secondary text-red-500 hover:bg-red-50 border-red-200 text-sm py-2 disabled:opacity-50"
                >
                    <Trash2 className="w-4 h-4" />
                    Clear
                </button>
            </div>

            {history.length === 0 ? (
                <div className="text-center py-12 text-secondary bg-surface rounded-lg border border-border">
                    <Trophy className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>No quiz history yet.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {history.map((entry, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="card p-4 flex items-center justify-between hover:border-primary/30 transition-colors"
                        >
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm
                  ${entry.percentage >= 70 ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}`}>
                                    {Math.round(entry.percentage)}%
                                </div>
                                <div>
                                    <div className="font-medium">{entry.score} / {entry.total} correct</div>
                                    <div className="text-sm text-secondary flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        {new Date(entry.date).toLocaleDateString()}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </motion.div>
    );
}
