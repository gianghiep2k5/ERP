import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getExpiryRiskDetail, type ExpiryRiskItem } from '../api/expiryRisk';
import './ExpiryRiskDetailPage.css';

export default function ExpiryRiskDetailPage() {
  const { lotId } = useParams<{ lotId: string }>();
  const [detail, setDetail] = useState<ExpiryRiskItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lotId) return;
    setLoading(true);
    getExpiryRiskDetail(lotId)
      .then((data) => setDetail(data))
      .catch((err) => setError(err?.message ?? `Failed to load risk detail for ${lotId}`))
      .finally(() => setLoading(false));
  }, [lotId]);

  return (
    <div className="riskdetail-container">
      <div className="riskdetail-topbar">
        <Link to="/expiry-risk" className="back-link">
          &larr; Back to Expiry Risk Centre
        </Link>
        <span className="analysis-badge">
          Fixed Analysis Date: <code>{detail?.analysis_date ?? '2026-08-05'}</code>
        </span>
      </div>

      {loading && (
        <div className="riskdetail-loading">
          <div className="riskdetail-spinner" />
          <span>Computing transparent scoring breakdown...</span>
        </div>
      )}

      {error && <div className="riskdetail-error">{error}</div>}

      {detail && !loading && (
        <div className="riskdetail-content">
          {/* Header */}
          <header className="riskdetail-header-card">
            <div className="title-area">
              <span className={`risk-badge-lg band-${detail.risk_band.toLowerCase()}`}>
                {detail.risk_band.toUpperCase()} RISK
              </span>
              <h1 className="header-title">Interpretable Expiry-risk Scoring</h1>
              <p className="header-subtitle">
                Lot <code>{detail.lot_id}</code> &bull; SKU: <strong>{detail.sku_name}</strong> (<code>{detail.sku_id}</code>)
              </p>
            </div>
            <div className="score-box">
              <span className="score-num">{detail.risk_score}</span>
              <span className="score-label">Composite Risk Score (0 - 100)</span>
            </div>
          </header>

          {/* Decision Support Notice */}
          <div className="decision-notice-banner">
            ℹ️ <strong>Decision Support Notice:</strong> This prototype provides decision support and does not execute stock transactions automatically.
          </div>

          {/* Transparent Calculation Breakdown Table */}
          <section className="breakdown-section">
            <h2 className="section-heading">Transparent Step-by-Step Calculation Breakdown</h2>
            <div className="breakdown-grid">
              <div className="step-card">
                <span className="step-num">Step 1</span>
                <span className="step-label">Days to Expiry</span>
                <span className="step-val">{detail.days_to_expiry} days</span>
                <p className="step-desc">
                  Calculated as <code>{detail.expiry_date}</code> minus analysis date (<code>{detail.analysis_date}</code>).
                </p>
              </div>

              <div className="step-card">
                <span className="step-num">Step 2</span>
                <span className="step-label">30-Day Demand Baseline</span>
                <span className="step-val">{detail.recent_average_daily_demand.toFixed(2)} units/day</span>
                <p className="step-desc">
                  Based on <code>{detail.recent_30d_sales_qty.toLocaleString()}</code> total units sold across representative outlets in the past 30 days.
                </p>
              </div>

              <div className="step-card">
                <span className="step-num">Step 3</span>
                <span className="step-label">Expected Consumption</span>
                <span className="step-val">{Math.round(detail.forecast_consumption_before_expiry).toLocaleString()} units</span>
                <p className="step-desc">
                  Method: <strong>{detail.forecast_method}</strong> up to expiry date.
                </p>
              </div>

              <div className="step-card step-highlight">
                <span className="step-num">Step 4</span>
                <span className="step-label">Projected Surplus / Shortage</span>
                <span className="step-val surplus-text">
                  {detail.projected_surplus > 0
                    ? `+${Math.round(detail.projected_surplus).toLocaleString()} surplus`
                    : `-${Math.round(detail.projected_shortage).toLocaleString()} shortage`}
                </span>
                <p className="step-desc">
                  Available Stock: <code>{detail.available_qty.toLocaleString()}</code> minus Expected Consumption (<code>{Math.round(detail.forecast_consumption_before_expiry).toLocaleString()}</code>).
                </p>
              </div>

              <div className="step-card">
                <span className="step-num">Step 5</span>
                <span className="step-label">Surplus Ratio</span>
                <span className="step-val">{(detail.surplus_ratio * 100).toFixed(1)}%</span>
                <p className="step-desc">
                  Formula: <code>Projected Surplus / Available Qty</code> (weighted at 65% of final score).
                </p>
              </div>

              <div className="step-card">
                <span className="step-num">Step 6</span>
                <span className="step-label">Urgency Factor</span>
                <span className="step-val">{(detail.urgency_factor * 100).toFixed(1)}%</span>
                <p className="step-desc">
                  Formula: <code>MAX(0, (60 - Days Left) / 60)</code> (weighted at 35% of final score).
                </p>
              </div>
            </div>
          </section>

          {/* Explanation & Proposed Actions Grid */}
          <div className="actions-explanation-grid">
            <div className="panel-card">
              <h2 className="panel-title">📝 Generated Explanation</h2>
              <p className="explanation-paragraph">{detail.explanation}</p>
              <div className="meta-list">
                <div><span>FEFO Priority Position:</span> <strong>#{detail.fefo_position}</strong></div>
                <div><span>Location:</span> <strong>{detail.location_name}</strong> (<code>{detail.location_id}</code>)</div>
                <div><span>On-Hand / Available:</span> <strong>{detail.on_hand_qty.toLocaleString()} / {detail.available_qty.toLocaleString()}</strong></div>
              </div>
            </div>

            <div className="panel-card">
              <h2 className="panel-title">🛡️ Deterministic Proposed Actions</h2>
              <ul className="proposed-actions-list">
                {detail.proposed_actions.map((act, i) => (
                  <li key={i} className="action-item">
                    <span className="action-check">&bull;</span>
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <footer className="riskdetail-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
