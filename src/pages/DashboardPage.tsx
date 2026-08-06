import { useEffect, useState } from 'react';
import { getDashboardSummary, type DashboardSummary } from '../api/dashboard';
import { useAuth } from '../auth/AuthContext';
import './DashboardPage.css';

export default function DashboardPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardSummary()
      .then((data) => setSummary(data))
      .catch((err) => setError(err?.message ?? 'Failed to load dashboard summary'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Operational Dashboard</h1>
          <p className="dashboard-sub">
            Welcome back, <strong>{user?.username}</strong> ({user?.role}) — Fixed Analysis Date: <code>{summary?.analysis_date ?? '2026-08-05'}</code>
          </p>
        </div>
      </header>

      {loading && (
        <div className="dashboard-loading">
          <div className="dashboard-spinner" />
          <span>Calculating live metrics from SQLite...</span>
        </div>
      )}

      {error && <div className="dashboard-error">{error}</div>}

      {summary && !loading && (
        <div className="dashboard-content">
          {/* Main KPI Cards Grid */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <span className="kpi-icon">📦</span>
              <div className="kpi-data">
                <span className="kpi-val">{summary.total_skus.toLocaleString()}</span>
                <span className="kpi-label">Total Active SKUs</span>
              </div>
            </div>

            <div className="kpi-card">
              <span className="kpi-icon">🏷️</span>
              <div className="kpi-data">
                <span className="kpi-val">{summary.total_lots.toLocaleString()}</span>
                <span className="kpi-label">Total Inventory Lots</span>
              </div>
            </div>

            <div className="kpi-card">
              <span className="kpi-icon">📊</span>
              <div className="kpi-data">
                <span className="kpi-val">{summary.total_on_hand_qty.toLocaleString()}</span>
                <span className="kpi-label">Total On-Hand Quantity</span>
              </div>
            </div>

            <div className="kpi-card kpi-card-highlight">
              <span className="kpi-icon">📋</span>
              <div className="kpi-data">
                <span className="kpi-val">{summary.pending_recommendations.toLocaleString()}</span>
                <span className="kpi-label">Pending AI Recommendations</span>
              </div>
            </div>
          </div>

          {/* Scenario Distribution Cards */}
          <section className="scenarios-section">
            <h2 className="section-heading">Operational Scenario Counts</h2>
            <div className="scenario-grid">
              <div className="scenario-card scenario-stockout">
                <div className="scenario-header">
                  <span className="scenario-dot dot-stockout" />
                  <span className="scenario-title">Stock-out Risk</span>
                </div>
                <div className="scenario-count">{summary.stockout_count}</div>
                <p className="scenario-desc">Lots flagged with high stock-out probability</p>
              </div>

              <div className="scenario-card scenario-expiry">
                <div className="scenario-header">
                  <span className="scenario-dot dot-expiry" />
                  <span className="scenario-title">Expiry Risk</span>
                </div>
                <div className="scenario-count">{summary.expiry_count}</div>
                <p className="scenario-desc">Lots nearing default shelf-life limits</p>
              </div>

              <div className="scenario-card scenario-transfer">
                <div className="scenario-header">
                  <span className="scenario-dot dot-transfer" />
                  <span className="scenario-title">Transfer Required</span>
                </div>
                <div className="scenario-count">{summary.transfer_count}</div>
                <p className="scenario-desc">Lots requiring outlet group redistribution</p>
              </div>

              <div className="scenario-card scenario-normal">
                <div className="scenario-header">
                  <span className="scenario-dot dot-normal" />
                  <span className="scenario-title">Normal Operations</span>
                </div>
                <div className="scenario-count">{summary.normal_count}</div>
                <p className="scenario-desc">Balanced stock within safety thresholds</p>
              </div>
            </div>
          </section>

          {/* Metadata Footer bar */}
          <div className="dashboard-meta-bar">
            <span>🕒 Latest Database Snapshot Update: <strong>{summary.latest_update ?? 'N/A'}</strong></span>
            <span>📍 Location Scope: <strong>TVB Pilot Finished-Goods Warehouse (LOC01)</strong></span>
          </div>
        </div>
      )}

      <footer className="dashboard-footer-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
