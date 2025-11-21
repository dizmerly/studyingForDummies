import React from 'react';
import { motion } from 'framer-motion';
import { Play, History, Upload } from 'lucide-react';

export default function LandingScreen({ onStart, onHistory }) {
    return (
        <div className="flex flex-col items-center justify-center text-center">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="mb-16"
            >
                <h1 className="text-5xl font-extrabold mb-6 gradient-text">
                    Quiz Generation Made Easy
                </h1>
                <p className="text-xl text-secondary mb-12 max-w-2xl mx-auto leading-relaxed">
                    Upload or paste your notes to generate quizzes. Generate quizzes for free by using
                    AI chatbots, and pasting the formatted questions here!
                </p>

                <div className="flex sm:flex-row gap-4 justify-center">
                    <button
                        onClick={onStart}
                        className="btn btn-primary text-lg px-8 py-4"
                    >
                        <Play className="w-5 h-5 fill-current" />
                        Start New Quiz
                    </button>

                    <button
                        onClick={onHistory}
                        className="btn btn-secondary text-lg px-8 py-4"
                    >
                        <History className="w-5 h-5" />
                        View History
                    </button>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.5 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left max-w-4xl w-full"
            >
                <div className="feature-card">
                    <div className="feature-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                        <Upload className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-bold mb-2">Easy Upload</h3>
                    <p className="text-secondary text-sm">Simply upload your text file or paste your questions directly.</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon" style={{ background: 'rgba(168, 85, 247, 0.1)', color: '#a855f7' }}>
                        <CodeIcon className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-bold mb-2">Code Support</h3>
                    <p className="text-secondary text-sm">Beautiful syntax highlighting for your programming questions.</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon" style={{ background: 'rgba(236, 72, 153, 0.1)', color: '#ec4899' }}>
                        <History className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-bold mb-2">Track Progress</h3>
                    <p className="text-secondary text-sm">Keep track of your scores and see how you improve over time.</p>
                </div>
            </motion.div>
        </div>
    );
}

function CodeIcon({ className }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
        </svg>
    );
}
