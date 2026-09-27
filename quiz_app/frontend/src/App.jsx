import { useEffect, useState } from 'react';
import './App.css';
import PracticeApp from './components/PracticeApp';
import ThemeToggle from './components/ThemeToggle';

const navigationLinks = [
  { label: 'How it works', href: '/#how-it-works' },
  { label: 'Features', href: '/#features' },
  { label: 'Pricing', href: '/pricing' },
];

function SiteHeader({ theme, onToggle }) {
  return (
    <header className="site-header">
      <a className="brand" href="/" aria-label="Studying For Dummies home">
        <span className="brand-mark" aria-hidden="true">S</span>
        <span>Studying For Dummies</span>
      </a>
      <nav className="main-navigation" aria-label="Main navigation">
        {navigationLinks.map((link) => (
          <a key={link.label} href={link.href}>{link.label}</a>
        ))}
      </nav>
      <ThemeToggle theme={theme} onToggle={onToggle} />
      <a className="login-link" href="/practice">Start practicing</a>
    </header>
  );
}

function ImagePlaceholder({ className = '', label = 'Image placeholder' }) {
  return (
    <div className={`image-placeholder ${className}`} role="img" aria-label={label}>
      <span className="placeholder-icon" aria-hidden="true">＋</span>
      <span>{label}</span>
    </div>
  );
}

function LandingPage({ theme, onToggle }) {
  return (
    <>
      <SiteHeader theme={theme} onToggle={onToggle} />
      <main>
        <section className="hero page-width">
          <div className="hero-copy">
            <p className="eyebrow"><span className="eyebrow-dot" /> A calmer way to study code</p>
            <h1>Make code click.<br /><span>One question at a time.</span></h1>
            <p className="hero-description">
              Build confidence reading code with focused practice, helpful explanations, and quizzes made for computer science students.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href="/practice">Start practicing <span aria-hidden="true">↗</span></a>
              <a className="text-link" href="#how-it-works">See how it works <span aria-hidden="true">↓</span></a>
            </div>
            <p className="hero-note">A little practice goes a long way.</p>
          </div>
          <div className="hero-art" aria-label="Study workspace image area">
            <ImagePlaceholder className="hero-image" label="Add a study workspace image" />
            <div className="floating-note"><span className="check-mark">✓</span><span><strong>Small steps.</strong><br />Real understanding.</span></div>
            <span className="art-sparkle" aria-hidden="true">✳</span>
          </div>
        </section>

        <section className="intro-band" id="how-it-works">
          <div className="page-width intro-content">
            <p className="eyebrow">Practice that makes sense</p>
            <h2>Turn “I think I get it”<br />into <span>“I’ve got this.”</span></h2>
            <p>Work through bite-sized code questions at your own pace. Learn from each answer and see your score when you finish.</p>
          </div>
        </section>

        <section className="features page-width" id="features">
          <div className="section-heading">
            <div><p className="eyebrow">Your study sidekick</p><h2>Less cramming.<br /><span>More understanding.</span></h2></div>
            <p>Build a steady study habit with tools designed to make tricky topics feel manageable.</p>
          </div>
          <div className="feature-grid">
            <article className="feature-card feature-card-large">
              <div className="feature-copy"><span className="feature-number">01</span><h3>Practice by doing</h3><p>Answer code-reading questions and learn to follow what a program is really doing.</p></div>
              <ImagePlaceholder className="feature-image" label="Add a code practice image" />
            </article>
            <article className="feature-card feature-card-green">
              <span className="feature-number">02</span><span className="feature-icon" aria-hidden="true">↗</span>
              <h3>Make it your own</h3><p>Bring a topic you’re working on and turn it into a focused practice session.</p>
            </article>
            <article className="feature-card feature-card-soft">
              <span className="feature-number">03</span><span className="feature-icon" aria-hidden="true">◎</span>
              <h3>See your result</h3><p>Review missed questions and try the same set again.</p>
            </article>
          </div>
        </section>

        <section className="closing-callout page-width">
          <div><p className="eyebrow">Ready when you are</p><h2>Let’s make your next<br />study session count.</h2><a className="button button-light" href="/practice">Get started <span aria-hidden="true">↗</span></a></div>
          <ImagePlaceholder className="closing-image" label="Add a student study image" />
          <span className="closing-decoration" aria-hidden="true">✳</span>
        </section>
      </main>
      <footer className="site-footer page-width"><a className="brand footer-brand" href="/">Studying For Dummies</a><p>Made for curious minds and future problem solvers.</p><a href="/pricing">Pricing</a></footer>
    </>
  );
}

const plans = [
  { name: 'Free', description: 'Explore code-reading practice.', features: ['Create practice sets', 'Answer at your own pace', 'Review explanations'], action: 'Start practicing' },
  { name: 'Monthly', description: 'For a steady study routine.', features: ['More monthly generations', 'Saved practice sets', 'Review previous attempts'], action: 'Explore practice' },
  { name: 'Credits', description: 'For focused exam preparation.', features: ['Buy generations when needed', 'Use credits on your schedule', 'Keep your completed sets'], action: 'Explore practice' },
];

function PricingPage({ theme, onToggle }) {
  return <><SiteHeader theme={theme} onToggle={onToggle} /><main className="pricing-page page-width">
    <p className="eyebrow">Pricing</p><h1>Practice that fits your pace.</h1>
    <p className="pricing-intro">Plans and prices are being worked out. Here’s the shape of what we’re considering.</p>
    <div className="pricing-grid">{plans.map((plan) => <article className="pricing-card" key={plan.name}>
      <p className="pricing-plan">{plan.name}</p><h2>{plan.description}</h2><p className="pricing-placeholder">Price coming soon</p>
      <ul>{plan.features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
      <a className="button button-primary" href="/practice">{plan.action} <span aria-hidden="true">↗</span></a>
    </article>)}</div>
  </main></>;
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const update = (event) => { if (!localStorage.getItem('theme')) setTheme(event.matches ? 'dark' : 'light'); };
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);
  const toggleTheme = () => setTheme((current) => {
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', next);
    return next;
  });
  const currentPath = window.location.pathname;
  if (currentPath === '/practice') return <PracticeApp theme={theme} onToggleTheme={toggleTheme} />;
  if (currentPath === '/pricing') return <PricingPage theme={theme} onToggle={toggleTheme} />;
  return <LandingPage theme={theme} onToggle={toggleTheme} />;
}
