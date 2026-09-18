import { useState } from "react";
import "./index.css";

const API_URL = "https://businessintel-ai.onrender.com";

function App() {
  const [website, setWebsite] = useState("");
  const [businessGoal, setBusinessGoal] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyzeBusiness() {
    setError("");
    setResult(null);

    if (!website.trim() || !businessGoal.trim()) {
      setError("Please enter both the website and business goal.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          website: website.trim(),
          business_goal: businessGoal.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Business analysis failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="brand-mark">B</div>

          <div>
            <h1>BusinessIntel AI</h1>
            <p>AI-powered business research & strategy</p>
          </div>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          AI Engine Online
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <div className="badge">BUSINESS INTELLIGENCE</div>

          <h2>
            Turn a business website into
            <span> actionable strategy.</span>
          </h2>

          <p>
            Research a company, understand its business model, identify
            growth opportunities, and generate strategic recommendations.
          </p>
        </section>

        <section className="input-card">
          <div className="field">
            <label>Business Website</label>

            <input
              type="url"
              placeholder="https://company.com"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
            />
          </div>

          <div className="field">
            <label>Business Goal</label>

            <textarea
              placeholder="Example: Find opportunities to improve lead generation and automate business processes."
              value={businessGoal}
              onChange={(e) => setBusinessGoal(e.target.value)}
              rows={4}
            />
          </div>

          <button
            className="analyze-button"
            onClick={analyzeBusiness}
            disabled={loading}
          >
            {loading ? "Analyzing Business..." : "Analyze Business"}
          </button>

          {loading && (
            <div className="loading-box">
              <div className="spinner"></div>

              <div>
                <strong>Researching business...</strong>
                <p>
                  BusinessIntel AI is researching the website, validating
                  evidence, and generating strategy.
                </p>
              </div>
            </div>
          )}

          {error && <div className="error-box">{error}</div>}
        </section>

        {result && (
          <section className="results">
            <div className="results-header">
              <div>
                <div className="badge">ANALYSIS COMPLETE</div>
                <h2>Business Intelligence Report</h2>
              </div>
            </div>

            <CompanyProfile profile={result.company_profile} />

            <StrategySection
              title="Marketing Observations"
              items={result.business_strategy.marketing_observations}
              renderItem={(item) => (
                <>
                  <h4>{item.observation}</h4>
                  <p>{item.implication}</p>
                  <Evidence evidence={item.supporting_evidence} />
                </>
              )}
            />

            <StrategySection
              title="Lead Generation Opportunities"
              items={result.business_strategy.lead_generation_opportunities}
              renderItem={(item) => (
                <>
                  <h4>{item.opportunity}</h4>
                  <p>{item.rationale}</p>

                  <strong>Suggested Approach</strong>
                  <p>{item.suggested_approach}</p>

                  <Evidence evidence={item.supporting_evidence} />
                </>
              )}
            />

            <StrategySection
              title="Automation Opportunities"
              items={result.business_strategy.automation_opportunities}
              renderItem={(item) => (
                <>
                  <h4>{item.process}</h4>
                  <p>{item.automation_idea}</p>

                  <strong>Expected Benefit</strong>
                  <p>{item.expected_benefit}</p>

                  <Evidence evidence={item.supporting_evidence} />
                </>
              )}
            />

            <StrategySection
              title="Recommended Actions"
              items={result.business_strategy.recommended_actions}
              renderItem={(item) => (
                <>
                  <h4>{item.action}</h4>
                  <p>{item.reason}</p>

                  <strong>Expected Outcome</strong>
                  <p>{item.expected_outcome}</p>
                </>
              )}
            />
          </section>
        )}
      </main>
    </div>
  );
}

function CompanyProfile({ profile }) {
  return (
    <section className="profile-card">
      <div className="section-title">
        <span>01</span>
        Company Profile
      </div>

      <div className="profile-grid">
        <ProfileItem label="Company" value={profile.company_name} />
        <ProfileItem label="Industry" value={profile.industry} />
        <ProfileItem label="Description" value={profile.description} />
        <ProfileItem label="Offer" value={profile.offer} />
        <ProfileItem
          label="Target Audience"
          value={profile.target_audience}
        />
        <ProfileItem
          label="Problem Solved"
          value={profile.problem_solved}
        />
        <ProfileItem
          label="Business Model"
          value={profile.business_model}
        />
      </div>

      <div className="evidence-section">
        <h3>Evidence</h3>

        {profile.evidence?.map((item, index) => (
          <div className="evidence-item" key={index}>
            <strong>{item.source_title}</strong>

            <p>{item.claim}</p>

            <a
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
            >
              View source →
            </a>
          </div>
        ))}
      </div>
    </section>
  );
}

function ProfileItem({ label, value }) {
  return (
    <div className="profile-item">
      <span>{label}</span>
      <p>{value}</p>
    </div>
  );
}

function StrategySection({ title, items = [], renderItem }) {
  return (
    <section className="strategy-card">
      <div className="section-title">
        <span>+</span>
        {title}
      </div>

      <div className="strategy-list">
        {items.map((item, index) => (
          <article className="strategy-item" key={index}>
            <div className="item-number">
              {String(index + 1).padStart(2, "0")}
            </div>

            <div className="item-content">
              {renderItem(item)}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Evidence({ evidence = [] }) {
  if (!evidence.length) {
    return null;
  }

  return (
    <div className="supporting-evidence">
      <span>Supporting Evidence</span>

      {evidence.map((item, index) => (
        <p key={index}>{item}</p>
      ))}
    </div>
  );
}

export default App;