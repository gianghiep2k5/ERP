import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getRecommendations,
  type RecommendationListItem,
  type RecommendationSummaryCounts,
} from '../api/recommendations';
import './RecommendationsPage.css';

export default function RecommendationsPage() {
  const [items, setItems] = useState<RecommendationListItem[]>([]);
  const [summary, setSummary] = useState<RecommendationSummaryCounts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    getRecommendations({
      status: statusFilter || undefined,
      recommendation_type: typeFilter || undefined,
      search: searchTerm || undefined,
    })
      .then((data) => {
        setItems(data.items);
        setSummary(data.summary);
      })
      .catch((err) => setError(err?.message ?? 'Failed to load recommendations'))
      .finally(() => setLoading(false));
  }, [statusFilter, typeFilter, searchTerm]);

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'REPLENISHMENT':
        return <span className="type-badge type-replenishment">REPLENISHMENT</span>;
      case 'TRANSFER':
        return <span className="type-badge type-transfer">TRANSFER</span>;
      case 'EXPIRY_ACTION':
        return <span className="type-badge type-expiry">EXPIRY ACTION</span>;
      default:
        return <span className="type-badge">{type}</span>;
    }
  };

  const getStatusBadge = (statusStr: string) => {
    switch (statusStr) {
      case 'APPROVED':
        return <span className="rec-status-tag status-approved">APPROVED</span>;
      case 'REJECTED':
        return <span className="rec-status-tag status-rejected">REJECTED</span>;
      default:
        return <span className="rec-status-tag status-pending">PENDING</span>;
    }
  };

  return (
    <div className="recs-container">
      <header className="recs-header">
        <div>
          <h1 className="recs-title">System Recommendations</h1>
          <p className="recs-sub">
            Review AI-generated replenishment, transfer, and expiry action proposals requiring managerial decision.
          </p>
        </div>
      </header>

      {/* Summary KPI Cards */}
      {summary && (
        <div className="recs-summary-grid">
          <div
            className={`recs-summary-card card-pending ${statusFilter === 'PENDING' ? 'active-card' : ''}`}
            onClick={() => setStatusFilter(statusFilter === 'PENDING' ? '' : 'PENDING')}
          >
            <span className="card-label">Pending Decision</span>
            <span className="card-val">{summary.pending_count}</span>
            <span className="card-hint">Awaiting Warehouse Manager review</span>
          </div>

          <div
            className={`recs-summary-card card-approved ${statusFilter === 'APPROVED' ? 'active-card' : ''}`}
            onClick={() => setStatusFilter(statusFilter === 'APPROVED' ? '' : 'APPROVED')}
          >
            <span className="card-label">Approved</span>
            <span className="card-val">{summary.approved_count}</span>
            <span className="card-hint">Confirmed proposals</span>
          </div>

          <div
            className={`recs-summary-card card-rejected ${statusFilter === 'REJECTED' ? 'active-card' : ''}`}
            onClick={() => setStatusFilter(statusFilter === 'REJECTED' ? '' : 'REJECTED')}
          >
            <span className="card-label">Rejected</span>
            <span className="card-val">{summary.rejected_count}</span>
            <span className="card-hint">Declined proposals</span>
          </div>

          <div className="recs-summary-card card-total">
            <span className="card-label">Total Recommendations</span>
            <span className="card-val">{summary.total_count}</span>
            <span className="card-hint">Seeded prototype items</span>
          </div>
        </div>
      )}

      {/* Filter Control Bar */}
      <div className="recs-filters-bar">
        <div className="filter-group">
          <input
            type="text"
            className="filter-input"
            placeholder="Search Rec ID or SKU name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="PENDING">PENDING</option>
            <option value="APPROVED">APPROVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>

        <div className="filter-group">
          <select
            className="filter-select"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All Proposal Types</option>
            <option value="REPLENISHMENT">REPLENISHMENT</option>
            <option value="TRANSFER">TRANSFER</option>
            <option value="EXPIRY_ACTION">EXPIRY_ACTION</option>
          </select>
        </div>

        {(statusFilter || typeFilter || searchTerm) && (
          <button
            className="clear-filters-btn"
            onClick={() => {
              setStatusFilter('');
              setTypeFilter('');
              setSearchTerm('');
            }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {loading && (
        <div className="recs-loading">
          <div className="recs-spinner" />
          <span>Fetching system recommendations...</span>
        </div>
      )}

      {error && <div className="recs-error">{error}</div>}

      {!loading && !error && (
        <div className="recs-table-wrapper">
          <table className="recs-table">
            <thead>
              <tr>
                <th>Rec ID</th>
                <th>Type</th>
                <th>SKU ID &amp; Name</th>
                <th>Lot ID</th>
                <th>Locations</th>
                <th>Proposed Qty</th>
                <th>Adjusted Qty</th>
                <th>Effective Qty</th>
                <th>Status</th>
                <th>Reason</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={11} className="empty-row">
                    No recommendations match the selected filters.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.recommendation_id}>
                    <td>
                      <code className="rec-id-text">{item.recommendation_id}</code>
                    </td>
                    <td>{getTypeBadge(item.recommendation_type)}</td>
                    <td>
                      <div className="sku-cell">
                        <code>{item.sku_id}</code>
                        <span className="sku-name-text">{item.sku_name}</span>
                      </div>
                    </td>
                    <td>
                      {item.lot_id ? (
                        <Link to={`/inventory/lots/${item.lot_id}`} className="lot-link">
                          {item.lot_id}
                        </Link>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="location-cell">
                      {item.recommendation_type === 'TRANSFER' ? (
                        <span>
                          {item.source_location_id ?? 'LOC01'} &rarr; {item.target_location_id ?? 'LOC02'}
                        </span>
                      ) : (
                        <span>{item.target_location_id ?? item.source_location_id ?? 'LOC01'}</span>
                      )}
                    </td>
                    <td className="qty-num">{item.proposed_qty.toLocaleString()}</td>
                    <td className="qty-num">
                      {item.adjusted_qty !== null && item.adjusted_qty !== undefined ? (
                        <strong className="text-adjusted">{item.adjusted_qty.toLocaleString()}</strong>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="qty-num effective-qty-text">
                      <strong>{item.effective_qty.toLocaleString()}</strong>
                    </td>
                    <td>{getStatusBadge(item.status)}</td>
                    <td className="reason-text-cell">{item.reason}</td>
                    <td>
                      <Link to={`/recommendations/${item.recommendation_id}`} className="review-link-btn">
                        Review &rarr;
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <footer className="recs-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
