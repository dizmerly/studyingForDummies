import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Home, Trophy } from 'lucide-react';
import { api } from '../services/api';

export default function ResultsScreen({ onRestart, onHome }) {
    const [results, setResults] = useState(null);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const data = await api.getResults();
                setResults(data);

                // Save to history (localStorage for now, as per original app)
                const history = JSON.parse(localStorage.getItem('quizHistory') || '[]');
                const entry = {
                    date: new Date().toISOString(),
                    score: data.score,
                    total: data.total,
                    percentage: data.percentage,
                    duration: 'N/A' // Duration tracking would need to be added to React state
                };
                history.unshift(entry);
                if (history.length > 20) history.pop();
                localStorage.setItem('quizHistory', JSON.stringify(history));

            } catch (err) {
                console.error(err);
            }
        };
        fetchResults();
    }, []);

    if (!results) return <div className="text-center p-8">Loading results...</div>;

    let message;
    let colorClass;
    if (results.percentage >= 90) {
        message = "Excellent work! 🌟";
        colorClass = "text-yellow-500";
    } else if (results.percentage >= 70) {
        message = "Good job! 👍";
        colorClass = "text-green-500";
    } else if (results.percentage >= 50) {
        message = "Not bad! Keep practicing. 📚";
        colorClass = "text-blue-500";
    } else {
        message = "Keep studying! You'll do better next time. 💪";
        colorClass = "text-gray-500";
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card max-w-lg mx-auto text-center"
        >
            <div className={`inline-flex p-4 rounded-full bg-surface mb-6 shadow-sm ${colorClass}`}>
                <Trophy className="w-12 h-12" />
            </div>

            <h2 className="text-2xl font-bold mb-2">Quiz Completed!</h2>
            <p className="text-secondary mb-8">{message}</p>

            <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="p-4 bg-background rounded-lg border border-border">
                    <div className="text-sm text-secondary mb-1">Score</div>
                    <div className="text-2xl font-bold">{results.score} / {results.total}</div>
                </div>
                <div className="p-4 bg-background rounded-lg border border-border">
                    <div className="text-sm text-secondary mb-1">Percentage</div>
                    <div className={`text-2xl font-bold ${colorClass}`}>{results.percentage}%</div>
                </div>
            </div>

            <div className="flex gap-3">
                <button onClick={onHome} className="btn btn-secondary flex-1">
                    <Home className="w-4 h-4" />
                    New Quiz
                </button>
                <button onClick={onRestart} className="btn btn-primary flex-1">
                    <RefreshCw className="w-4 h-4" />
                    Restart
                </button>
            </div>
        </motion.div>
    );
}
