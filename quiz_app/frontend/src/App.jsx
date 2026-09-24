import './App.css';

const navigationLinks = [
  { label: 'How it works', href: '/#how-it-works' },
  { label: 'Features', href: '/#features' },
  { label: 'Pricing', href: '/pricing.html' },
];

function SiteHeader() {
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
      <a className="login-link" href="/login.html">Log in</a>
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

function LandingPage() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="hero page-width">
          <div className="hero-copy">
            <p className="eyebrow"><span className="eyebrow-dot" /> A calmer way to study code</p>
            <h1>Make code click.<br /><span>One question at a time.</span></h1>
            <p className="hero-description">
              Build confidence reading code with focused practice, helpful explanations, and quizzes made for computer science students.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href="/login.html">Start practicing <span aria-hidden="true">↗</span></a>
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
            <p>Work through bite-sized code questions at your own pace. Learn from each answer, keep track of your progress, and come back stronger.</p>
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
              <h3>See your progress</h3><p>Keep your practice history in one place and notice how far you’ve come.</p>
            </article>
          </div>
        </section>

        <section className="closing-callout page-width">
          <div><p className="eyebrow">Ready when you are</p><h2>Let’s make your next<br />study session count.</h2><a className="button button-light" href="/login.html">Get started <span aria-hidden="true">↗</span></a></div>
          <ImagePlaceholder className="closing-image" label="Add a student study image" />
          <span className="closing-decoration" aria-hidden="true">✳</span>
        </section>
      </main>
      <footer className="site-footer page-width"><a className="brand footer-brand" href="/">Studying For Dummies</a><p>Made for curious minds and future problem solvers.</p><a href="/pricing.html">Pricing</a></footer>
    </>
  );
}

function SimplePage({ title, description }) {
  return <><SiteHeader /><main className="simple-page page-width"><p className="eyebrow">Studying For Dummies</p><h1>{title}</h1><p>{description}</p><a className="button button-primary" href="/">Back to home <span aria-hidden="true">↗</span></a><ImagePlaceholder className="simple-image" label="Page image placeholder" /></main></>;
}

export default function App() {
  const currentPath = window.location.pathname;

  if (currentPath.endsWith('/pricing.html')) {
    return <SimplePage title="Simple plans for steady progress." description="Pricing details are coming soon. For now, explore the practice experience and see if it fits the way you study." />;
  }

  if (currentPath.endsWith('/login.html')) {
    return <SimplePage title="Welcome back." description="The sign-in page is being prepared. Your next focused study session is just around the corner." />;
  }

  return <LandingPage />;
}
