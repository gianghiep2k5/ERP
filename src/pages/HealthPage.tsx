import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import './HealthPage.css';

interface HealthData {
  status: string;
  db_row_counts: Record<string, number>;
  uptime_seconds: number;
}

const TABLE_LABELS: Record<string, string> = {
  public_products: 'Public Products',
  skus: 'SKUs',
  locations: 'Locations',
  users: 'Users',
  lots: 'Lots',
  inventory_balances: 'Inventory Balances',
  sales_history: 'Sales History',
  forecast_metrics: 'Forecast Metrics',
  forecast_results: 'Forecast Results',
  recommendations: 'Recommendations',
  audit_logs: 'Audit Logs',
};

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}m ${s}s`;
}

export default function HealthPage() {
  const [data, setData] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get<HealthData>('/api/health')
      .then((res) => setData(res.data))
      .catch((err) => setError(err?.message ?? 'Failed to reach backend'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="health-root">
      {/* ── Header ── */}
      <header className="health-header">
        <div className="health-logo">
          <span className="health-logo-icon">⬡</span>
          <span className="health-logo-text">V-IMS AI</span>
        </div>
        <p className="health-subtitle">
          Inventory Management System — Phase 1 Health Check
        </p>
      </header>

      {/* ── Status card ── */}
      <main className="health-main">
        {loading && (
          <div className="health-card health-loading">
            <div className="health-spinner" />
            <p>Connecting to backend…</p>
          </div>
        )}

        {error && !loading && (
          <div className="health-card health-error">
            <span className="health-status-dot health-dot-error" />
            <div>
              <h2>Backend Unreachable</h2>
              <p className="health-error-msg">{error}</p>
              <p className="health-hint">
                Start the backend:{' '}
                <code>uvicorn app.main:app --reload --port 8000</code>
              </p>
            </div>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Status banner */}
            <div
              className={`health-card health-status-banner ${
                data.status === 'ok' ? 'health-banner-ok' : 'health-banner-warn'
              }`}
            >
              <span
                className={`health-status-dot ${
                  data.status === 'ok' ? 'health-dot-ok' : 'health-dot-warn'
                }`}
              />
              <div className="health-banner-text">
                <h2>
                  Backend{' '}
                  <span className="health-status-label">
                    {data.status.toUpperCase()}
                  </span>
                </h2>
                <p>Uptime: {formatUptime(data.uptime_seconds)}</p>
              </div>
            </div>

            {/* Table counts grid */}
            <section className="health-tables-section">
              <h3 className="health-section-title">Database Tables</h3>
              <div className="health-grid">
                {Object.entries(data.db_row_counts).map(([key, count]) => (
                  <div key={key} className="health-tile">
                    <span className="health-tile-count">
                      {count.toLocaleString()}
                    </span>
                    <span className="health-tile-label">
                      {TABLE_LABELS[key] ?? key}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </main>

      {/* ── Disclaimer ── */}
      <footer className="health-footer">
        <p>
          Demonstration using public product master references and synthetic
          operational data — not actual Vinamilk operational data.
        </p>
      </footer>
    </div>
  );
}
