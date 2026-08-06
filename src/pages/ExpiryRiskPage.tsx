import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getExpiryRiskList,
  type ExpiryRiskItem,
  type ExpiryRiskSummaryCounts,
} from '../api/expiryRisk';
import './ExpiryRiskPage.css';

export default function ExpiryRiskPage() {
  const [items, setItems] = useState<ExpiryRiskItem[]>([]);
  const [summary, setSummary] = useState<ExpiryRiskSummaryCounts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [selectedRiskBand, setSelectedRiskBand] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedExpiryBucket, setSelectedExpiryBucket] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    getExpiryRiskList({
      risk_band: selectedRiskBand || undefined,
      category: selectedCategory || undefined,
      expiry_bucket: selectedExpiryBucket || undefined,
      search: searchTerm || undefined,
    })
      .then((data) => {
        setItems(data.items);
        setSummary(data.summary);
      })
      .catch((err) => setError(err?.message ?? 'Failed to load expiry risk data'))
      .finally(() => setLoading(false));
  }, [selectedRiskBand, selectedCategory, selectedExpiryBucket, searchTerm]);

  const CATEGORIES = [
    'Fresh Milk',
    'Nutritional Milk',
    'Nut Milk',
    'Soy Milk',
    'Ready-to-Drink Formula',
  ];

  const RISK_BANDS = ['Expired', 'Critical', 'High', 'Medium', 'Low'];

  const EXPIRY_BUCKETS = [
    { value: 'expired', label: 'Expired (<=0 days)' },
    { value: '<=30', label: '<= 30 days' },
    { value: '31-60', label: '31 - 60 days' },
    { value: '61-90', label: '61 - 90 days' },
    { value: '>90', label: '> 90 days' },
  ];

  const getRiskBadge = (band: string) => {
    switch (band) {
      case 'Expired':
        return <span className="risk-badge band-expired">EXPIRED</span>;
      case 'Critical':
        return <span className="risk-badge band-critical">CRITICAL</span>;
      case 'High':
        return <span className="risk-badge band-high">HIGH</span>;
      case 'Medium':
        return <span className="risk-badge band-medium">MEDIUM</span>;
      default:
        return <span className="risk-badge band-low">LOW</span>;
    }
  };

  return (
    <div className="expiry-risk-container">
      <header className="expiry-risk-header">
        <div>
          <h1 className="expiry-risk-title">Explainable Expiry Risk Centre</h1>
          <p className="expiry-risk-sub">
            Prioritises inventory consumption risks beyond FEFO by evaluating projected demand against expiry horizons.
          </p>
        </div>
      </header>

      {/* Summary KPI Cards */}
      {summary && (
        <div className="summary-grid">
          <div
            className={`summary-card card-expired ${selectedRiskBand === 'Expired' ? 'active-filter' : ''}`}
            onClick={() => setSelectedRiskBand(selectedRiskBand === 'Expired' ? '' : 'Expired')}
          >
            <span className="summary-label">Expired</span>
            <span className="summary-val">{summary.expired_count}</span>
            <span className="summary-hint">days_to_expiry &le; 0</span>
          </div>

          <div
            className={`summary-card card-critical ${selectedRiskBand === 'Critical' ? 'active-filter' : ''}`}
            onClick={() => setSelectedRiskBand(selectedRiskBand === 'Critical' ? '' : 'Critical')}
          >
            <span className="summary-label">Critical Risk</span>
            <span className="summary-val">{summary.critical_count}</span>
            <span className="summary-hint">Surplus &ge; 50% or &le; 14d</span>
          </div>

          <div
            className={`summary-card card-high ${selectedRiskBand === 'High' ? 'active-filter' : ''}`}
            onClick={() => setSelectedRiskBand(selectedRiskBand === 'High' ? '' : 'High')}
          >
            <span className="summary-label">High Risk</span>
            <span className="summary-val">{summary.high_count}</span>
            <span className="summary-hint">Surplus &ge; 30% or &le; 30d</span>
          </div>

          <div
            className={`summary-card card-medium ${selectedRiskBand === 'Medium' ? 'active-filter' : ''}`}
            onClick={() => setSelectedRiskBand(selectedRiskBand === 'Medium' ? '' : 'Medium')}
          >
            <span className="summary-label">Medium Risk</span>
            <span className="summary-val">{summary.medium_count}</span>
            <span className="summary-hint">Surplus &ge; 10% or &le; 60d</span>
          </div>

          <div
            className={`summary-card card-low ${selectedRiskBand === 'Low' ? 'active-filter' : ''}`}
            onClick={() => setSelectedRiskBand(selectedRiskBand === 'Low' ? '' : 'Low')}
          >
            <span className="summary-label">Low Risk</span>
            <span className="summary-val">{summary.low_count}</span>
            <span className="summary-hint">Normal FEFO stock</span>
          </div>

          <div className="summary-card card-surplus">
            <span className="summary-label">Total Projected Surplus</span>
            <span className="summary-val surplus-val">{Math.round(summary.total_projected_surplus).toLocaleString()}</span>
            <span className="summary-hint">Units unconsumed before expiry</span>
          </div>
        </div>
      )}

      {/* Filter Control Bar */}
      <div className="expiry-filters-bar">
        <div className="filter-group">
          <input
            type="text"
            className="filter-input"
            placeholder="Search SKU ID, Name or Lot..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <select
            className="filter-select"
            value={selectedRiskBand}
            onChange={(e) => setSelectedRiskBand(e.target.value)}
          >
            <option value="">All Risk Bands</option>
            {RISK_BANDS.map((b) => (
              <option key={b} value={b}>
                {b} Risk
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <select
            className="filter-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <select
            className="filter-select"
            value={selectedExpiryBucket}
            onChange={(e) => setSelectedExpiryBucket(e.target.value)}
          >
            <option value="">All Expiry Horizons</option>
            {EXPIRY_BUCKETS.map((b) => (
              <option key={b.value} value={b.value}>
                {b.label}
              </option>
            ))}
          </select>
        </div>

        {(selectedRiskBand || selectedCategory || selectedExpiryBucket || searchTerm) && (
          <button
            className="clear-filters-btn"
            onClick={() => {
              setSelectedRiskBand('');
              setSelectedCategory('');
              setSelectedExpiryBucket('');
              setSearchTerm('');
            }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {loading && (
        <div className="expiry-loading">
          <div className="expiry-spinner" />
          <span>Computing explainable expiry risk assessments...</span>
        </div>
      )}

      {error && <div className="expiry-error">{error}</div>}

      {!loading && !error && (
        <div className="expiry-table-wrapper">
          <table className="expiry-table">
            <thead>
              <tr>
                <th>Risk Band</th>
                <th>Score</th>
                <th>Lot ID</th>
                <th>SKU ID & Name</th>
                <th>Expiry Date</th>
                <th>Days Left</th>
                <th>Available Qty</th>
                <th>Projected Surplus</th>
                <th>Surplus Ratio</th>
                <th>Explanation & Actions</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={11} className="empty-row">
                    No risk items match the selected filter parameters.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.lot_id} className={`row-band-${item.risk_band.toLowerCase()}`}>
                    <td>{getRiskBadge(item.risk_band)}</td>
                    <td>
                      <span className="risk-score-pill">{item.risk_score}</span>
                    </td>
                    <td>
                      <Link to={`/inventory/lots/${item.lot_id}`} className="lot-id-link">
                        {item.lot_id}
                      </Link>
                    </td>
                    <td>
                      <div className="sku-info-cell">
                        <code>{item.sku_id}</code>
                        <span className="sku-name-text">{item.sku_name}</span>
                      </div>
                    </td>
                    <td>{item.expiry_date}</td>
                    <td>
                      <span className={`days-pill ${item.days_to_expiry <= 30 ? 'pill-danger' : ''}`}>
                        {item.days_to_expiry}d
                      </span>
                    </td>
                    <td className="num-cell">{item.available_qty.toLocaleString()}</td>
                    <td className="num-cell strong-surplus">
                      {item.projected_surplus > 0 ? (
                        <span className="surplus-text">{Math.round(item.projected_surplus).toLocaleString()}</span>
                      ) : (
                        <span className="text-muted">0</span>
                      )}
                    </td>
                    <td className="num-cell">{(item.surplus_ratio * 100).toFixed(1)}%</td>
                    <td className="explanation-cell">
                      <p className="explanation-text">{item.explanation}</p>
                      <ul className="action-list">
                        {item.proposed_actions.slice(0, 2).map((action, idx) => (
                          <li key={idx}>• {action}</li>
                        ))}
                      </ul>
                    </td>
                    <td>
                      <Link to={`/expiry-risk/${item.lot_id}`} className="breakdown-btn">
                        Score Breakdown &rarr;
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <footer className="expiry-risk-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
