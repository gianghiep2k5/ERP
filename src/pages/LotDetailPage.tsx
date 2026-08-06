import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getLotDetail, type LotDetail } from '../api/lots';
import './LotDetailPage.css';

export default function LotDetailPage() {
  const { lotId } = useParams<{ lotId: string }>();
  const [lot, setLot] = useState<LotDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lotId) return;
    setLoading(true);
    getLotDetail(lotId)
      .then((data) => setLot(data))
      .catch((err) => setError(err?.message ?? `Failed to load detail for lot ${lotId}`))
      .finally(() => setLoading(false));
  }, [lotId]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <span className="status-tag tag-approved">APPROVED</span>;
      case 'REJECTED':
        return <span className="status-tag tag-rejected">REJECTED</span>;
      default:
        return <span className="status-tag tag-pending">PENDING</span>;
    }
  };

  return (
    <div className="lotdetail-container">
      <div className="lotdetail-topbar">
        <Link to="/inventory" className="back-link">
          ← Back to Inventory Balances
        </Link>
        <span className="analysis-date-badge">
          Fixed Analysis Date: <code>{lot?.analysis_date ?? '2026-08-05'}</code>
        </span>
      </div>

      {loading && (
        <div className="lotdetail-loading">
          <div className="lotdetail-spinner" />
          <span>Loading lot specifications and joins...</span>
        </div>
      )}

      {error && <div className="lotdetail-error">{error}</div>}

      {lot && !loading && (
        <div className="lotdetail-content">
          {/* Header Card */}
          <div className="lotdetail-header-card">
            <div className="header-title-row">
              <div>
                <span className="lot-id-badge">{lot.lot_id}</span>
                <h1 className="lot-sku-title">{lot.sku_name}</h1>
                <p className="lot-sku-sub">
                  Category: <strong>{lot.category}</strong> | Pack Size: <strong>{lot.pack_size ?? lot.public_pack_size ?? 'N/A'}</strong>
                </p>
              </div>
              <div className="fefo-badge-box">
                <span className="fefo-position-num">
                  #{lot.fefo_position} of {lot.fefo_total}
                </span>
                <span className="fefo-position-label">FEFO Priority Rank</span>
              </div>
            </div>
          </div>

          {/* 3 Column Information Grid */}
          <div className="detail-cards-grid">
            {/* Card 1: Lot Lifecycle & Expiry */}
            <div className="detail-card">
              <h2 className="card-title">📅 Lot Lifecycle & Shelf Life</h2>
              <div className="info-list">
                <div className="info-row">
                  <span>Manufacturing Date:</span>
                  <strong>{lot.manufacturing_date}</strong>
                </div>
                <div className="info-row">
                  <span>Expiry Date:</span>
                  <strong className="text-warning">{lot.expiry_date}</strong>
                </div>
                <div className="info-row">
                  <span>Days to Expiry:</span>
                  <strong className={lot.days_to_expiry <= 30 ? 'text-critical' : 'text-success'}>
                    {lot.days_to_expiry} days
                  </strong>
                </div>
                <div className="info-row">
                  <span>Default Shelf Life:</span>
                  <span>{lot.default_shelf_life_days} days</span>
                </div>
                <div className="info-row">
                  <span>Data Status:</span>
                  <span className="status-chip">{lot.lot_data_status}</span>
                </div>
              </div>
            </div>

            {/* Card 2: Inventory & Location Balances */}
            <div className="detail-card">
              <h2 className="card-title">📦 Stock Balances & Location</h2>
              <div className="info-list">
                <div className="info-row">
                  <span>Location:</span>
                  <strong>{lot.location_name}</strong>
                </div>
                <div className="info-row">
                  <span>Scenario Tag:</span>
                  <span className="scenario-chip">{lot.scenario}</span>
                </div>
                <div className="info-row">
                  <span>On-Hand Quantity:</span>
                  <strong className="qty-value">{lot.on_hand_qty.toLocaleString()} units</strong>
                </div>
                <div className="info-row">
                  <span>Available Quantity:</span>
                  <span>{lot.available_qty.toLocaleString()} units</span>
                </div>
                <div className="info-row">
                  <span>Reserved / Quarantine:</span>
                  <span>
                    {lot.reserved_qty} / {lot.quarantine_qty}
                  </span>
                </div>
              </div>
            </div>

            {/* Card 3: Public Product Reference (Vinamilk) */}
            <div className="detail-card">
              <h2 className="card-title">🌐 Public Product Master Ref</h2>
              <div className="info-list">
                <div className="info-row">
                  <span>Public Product ID:</span>
                  <code>{lot.public_product_id}</code>
                </div>
                <div className="info-row">
                  <span>Product Name:</span>
                  <strong>{lot.product_name}</strong>
                </div>
                <div className="info-row">
                  <span>Unit Cost:</span>
                  <span>{lot.unit_cost_vnd.toLocaleString()} VND</span>
                </div>
                <div className="info-row">
                  <span>Variant Status:</span>
                  <span>{lot.variant_status}</span>
                </div>
                <div className="info-row">
                  <span>Source URL:</span>
                  <a
                    href={lot.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="source-url-link"
                  >
                    View Official Vinamilk Ref ↗
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Linked Recommendations Section */}
          <section className="recommendations-section">
            <h2 className="section-title">🤖 Linked AI Recommendations</h2>
            {lot.recommendations.length === 0 ? (
              <p className="no-recs-text">No active recommendations linked to this lot.</p>
            ) : (
              <div className="recs-table-wrapper">
                <table className="recs-table">
                  <thead>
                    <tr>
                      <th>Rec ID</th>
                      <th>Type</th>
                      <th>Proposed Qty</th>
                      <th>Adjusted Qty</th>
                      <th>Effective Qty</th>
                      <th>Status</th>
                      <th>AI Reason</th>
                      <th>Created At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lot.recommendations.map((rec) => (
                      <tr key={rec.recommendation_id}>
                        <td>
                          <code>{rec.recommendation_id}</code>
                        </td>
                        <td>
                          <span className="rec-type-chip">{rec.recommendation_type}</span>
                        </td>
                        <td>{rec.proposed_qty.toLocaleString()}</td>
                        <td>
                          {rec.adjusted_qty !== null ? (
                            <strong className="text-adjusted">{rec.adjusted_qty.toLocaleString()}</strong>
                          ) : (
                            <span className="text-muted">—</span>
                          )}
                        </td>
                        <td>
                          <strong>{rec.effective_qty.toLocaleString()}</strong>
                        </td>
                        <td>{getStatusBadge(rec.status)}</td>
                        <td className="reason-cell">{rec.reason}</td>
                        <td className="time-cell">{rec.created_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}

      <footer className="lotdetail-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
