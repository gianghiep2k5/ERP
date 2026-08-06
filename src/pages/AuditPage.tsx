import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAuditLogs, type AuditListItem } from '../api/audit';
import './AuditPage.css';

export default function AuditPage() {
  const [items, setItems] = useState<AuditListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [recFilter, setRecFilter] = useState('');
  const [actorFilter, setActorFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  useEffect(() => {
    setLoading(true);
    getAuditLogs({
      recommendation_id: recFilter || undefined,
      actor_username: actorFilter || undefined,
      action: actionFilter || undefined,
    })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((err) => setError(err?.message ?? 'Failed to load audit logs'))
      .finally(() => setLoading(false));
  }, [recFilter, actorFilter, actionFilter]);

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'MODIFIED':
        return <span className="action-badge action-modified">MODIFIED</span>;
      case 'APPROVED':
        return <span className="action-badge action-approved">APPROVED</span>;
      case 'REJECTED':
        return <span className="action-badge action-rejected">REJECTED</span>;
      default:
        return <span className="action-badge">{action}</span>;
    }
  };

  return (
    <div className="auditpage-container">
      <header className="auditpage-header">
        <div>
          <h1 className="auditpage-title">Immutable Audit Trail</h1>
          <p className="auditpage-sub">
            Chronological audit log of all recommendation quantity adjustments, approvals, and rejections.
          </p>
        </div>
      </header>

      {/* Filter Control Bar */}
      <div className="audit-filters-bar">
        <div className="filter-group">
          <input
            type="text"
            className="filter-input"
            placeholder="Filter by Recommendation ID (e.g. REC0001)..."
            value={recFilter}
            onChange={(e) => setRecFilter(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <input
            type="text"
            className="filter-input"
            placeholder="Filter by Actor Username (e.g. warehouse.manager)..."
            value={actorFilter}
            onChange={(e) => setActorFilter(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <select
            className="filter-select"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          >
            <option value="">All Audit Actions</option>
            <option value="MODIFIED">MODIFIED</option>
            <option value="APPROVED">APPROVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>

        {(recFilter || actorFilter || actionFilter) && (
          <button
            className="clear-filters-btn"
            onClick={() => {
              setRecFilter('');
              setActorFilter('');
              setActionFilter('');
            }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {loading && (
        <div className="audit-loading">
          <div className="audit-spinner" />
          <span>Loading immutable audit records...</span>
        </div>
      )}

      {error && <div className="audit-error">{error}</div>}

      {!loading && !error && (
        <div className="audit-table-wrapper">
          <div className="table-header-meta">
            <span>Showing <strong>{items.length}</strong> of <strong>{total}</strong> audit log entries</span>
          </div>
          <table className="audit-table">
            <thead>
              <tr>
                <th>Audit ID</th>
                <th>Rec ID</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Status Transition</th>
                <th>Comment</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-row">
                    No audit records match the selected filters.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.audit_id}>
                    <td>
                      <code className="audit-id-text">{item.audit_id}</code>
                    </td>
                    <td>
                      <Link to={`/recommendations/${item.recommendation_id}`} className="rec-link">
                        {item.recommendation_id}
                      </Link>
                    </td>
                    <td>
                      <strong className="actor-text">{item.actor_username}</strong>
                    </td>
                    <td>{getActionBadge(item.action)}</td>
                    <td>
                      <span className="flow-text">
                        {item.before_status} &rarr; {item.after_status}
                      </span>
                    </td>
                    <td className="comment-text-cell">{item.comment ?? '—'}</td>
                    <td className="timestamp-text">{item.action_timestamp}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <footer className="auditpage-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
