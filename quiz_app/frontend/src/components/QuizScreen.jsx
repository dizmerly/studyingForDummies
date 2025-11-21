import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, ArrowRight, Code } from 'lucide-react';
import { api } from '../services/api';
import { parseQuestionContent } from '../utils/textParser';

export default function QuizScreen({ onComplete }) {
    const [questionData, setQuestionData] = useState(null);
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadQuestion = useCallback(async () => {
        try {
            setLoading(true);
            const data = await api.getQuestion();
            setQuestionData(data);
            setSelectedAnswer(null);
            setResult(null);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadQuestion();
    }, [loadQuestion]);

    const handleAnswer = async (answer) => {
        if (result) return; // Already answered

        setSelectedAnswer(answer);
        try {
            const data = await api.checkAnswer(answer);
            setResult(data);

            // Auto advance after delay
            setTimeout(() => {
                if (data.has_more) {
                    loadQuestion();
                } else {
                    onComplete();
                }
            }, 1500);
        } catch (err) {
            console.error(err);
        }
    };

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (loading || result) return;

            const key = e.key.toLowerCase();
            const choices = ['a', 'b', 'c', 'd'];
            const index = choices.indexOf(key);

            if (index !== -1) {
                handleAnswer(choices[index].toUpperCase());
            } else if (key >= '1' && key <= '4') {
                handleAnswer(choices[parseInt(key) - 1].toUpperCase());
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [loading, result]);

    if (loading && !questionData) {
        return <div className="text-center p-8">Loading...</div>;
    }

    if (!questionData) return null;

    const progress = (questionData.current / questionData.total) * 100;

    return (
        <div className="max-w-2xl mx-auto w-full">
            {/* Progress Bar */}
            <div className="mb-8">
                <div className="flex justify-between text-sm text-secondary mb-3">
                    <span className="font-medium">Question {questionData.current} of {questionData.total}</span>
                    <span className="font-medium">Score: {questionData.score}/{questionData.current - 1}</span>
                </div>
                <div className="progress-bar">
                    <motion.div
                        className="progress-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5 }}
                    />
                </div>
            </div>

            <AnimatePresence mode="wait">
                <motion.div
                    key={questionData.current}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="card"
                >
                    <div className="mb-8 text-lg font-medium leading-relaxed">
                        {parseQuestionContent(questionData.question)}
                    </div>

                    <div className="space-y-3">
                        {questionData.choices.map(([letter, text]) => {
                            const isSelected = selectedAnswer === letter;
                            const isCorrect = result?.correct_answer === letter;
                            const isWrong = result && !result.correct && isSelected;

                            let className = "choice-btn";

                            if (result) {
                                if (isCorrect) {
                                    className += " bg-green-50 border-green-500 text-green-800";
                                } else if (isWrong) {
                                    className += " bg-red-50 border-red-500 text-red-800";
                                } else {
                                    className += " opacity-60";
                                }
                            } else if (isSelected) {
                                className += " border-primary bg-primary/5";
                            }

                            return (
                                <button
                                    key={letter}
                                    onClick={() => handleAnswer(letter)}
                                    disabled={!!result}
                                    className={className}
                                >
                                    <span className="choice-letter">
                                        {letter}
                                    </span>
                                    <span className="flex-1 text-left">{text}</span>
                                    {isCorrect && <CheckCircle className="w-5 h-5 text-green-600" />}
                                    {isWrong && <XCircle className="w-5 h-5 text-red-600" />}
                                </button>
                            );
                        })}
                    </div>

                    {result && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`mt-6 p-4 rounded-lg flex items-center gap-3 font-medium ${result.correct
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                                }`}
                        >
                            {result.correct ? (
                                <>
                                    <CheckCircle className="w-5 h-5" />
                                    <span>Correct!</span>
                                </>
                            ) : (
                                <>
                                    <XCircle className="w-5 h-5" />
                                    <span>Incorrect. The correct answer is {result.correct_answer}.</span>
                                </>
                            )}
                        </motion.div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
