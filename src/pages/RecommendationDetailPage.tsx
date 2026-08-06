import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  getRecommendationDetail,
  modifyRecommendationQuantity,
  approveRecommendation,
  rejectRecommendation,
  type RecommendationDetailResponse,
} from '../api/recommendations';
import { useAuth } from '../auth/AuthContext';
import './RecommendationDetailPage.css';

export default function RecommendationDetailPage() {
  const { recommendationId } = useParams<{ recommendationId: string }>();
  const { user, canApprove } = useAuth();

  const [detail, setDetail] = useState<RecommendationDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mutation form states
  const [modifyQtyInput, setModifyQtyInput] = useState<string>('');
  const [modifyComment, setModifyComment] = useState<string>('');

  const [approveComment, setApproveComment] = useState<string>('');
  const [rejectComment, setRejectComment] = useState<string>('');

  const [submittingAction, setSubmittingAction] = useState<string | null>(null); // 'modify', 'approve', 'reject'
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [actionErrorMsg, setActionErrorMsg] = useState<string | null>(null);
  const [conflictMsg, setConflictMsg] = useState<string | null>(null);

  // Modals / Confirmations
  const [showModifyConfirm, setShowModifyConfirm] = useState(false);
  const [showApproveConfirm, setShowApproveConfirm] = useState(false);
  const [showRejectConfirm, setShowRejectConfirm] = useState(false);

  const fetchDetail = (id: string) => {
    setLoading(true);
    getRecommendationDetail(id)
      .then((data) => {
        setDetail(data);
        setModifyQtyInput(
          data.adjusted_qty !== null && data.adjusted_qty !== undefined
            ? String(data.adjusted_qty)
            : String(data.proposed_qty)
        );
      })
      .catch((err) => setError(err?.message ?? `Failed to load recommendation ${id}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (recommendationId) {
      fetchDetail(recommendationId);
    }
  }, [recommendationId]);

  const handleModifyQuantitySubmit = async () => {
    if (!detail || !recommendationId) return;
    const qty = parseInt(modifyQtyInput, 10);
    if (isNaN(qty) || qty <= 0) {
      setActionErrorMsg('Quantity must be a positive integer greater than zero.');
      return;
    }
    if (!modifyComment.trim()) {
      setActionErrorMsg('Comment is mandatory for quantity modification.');
      return;
    }

    setSubmittingAction('modify');
    setActionErrorMsg(null);
    setActionSuccessMsg(null);
    setConflictMsg(null);

    try {
      const updated = await modifyRecommendationQuantity(recommendationId, qty, modifyComment.trim());
      setDetail(updated);
      setActionSuccessMsg(`Quantity modified to ${qty.toLocaleString()} units.`);
      setModifyComment('');
      setShowModifyConfirm(false);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setConflictMsg('This recommendation has already been processed.');
        fetchDetail(recommendationId);
      } else {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Failed to modify quantity.';
        setActionErrorMsg(msg);
      }
    } finally {
      setSubmittingAction(null);
    }
  };

  const handleApproveSubmit = async () => {
    if (!detail || !recommendationId) return;
    if (!approveComment.trim()) {
      setActionErrorMsg('Comment is mandatory for approval.');
      return;
    }

    setSubmittingAction('approve');
    setActionErrorMsg(null);
    setActionSuccessMsg(null);
    setConflictMsg(null);

    try {
      const updated = await approveRecommendation(recommendationId, approveComment.trim());
      setDetail(updated);
      setActionSuccessMsg('Recommendation APPROVED successfully.');
      setApproveComment('');
      setShowApproveConfirm(false);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setConflictMsg('This recommendation has already been processed.');
        fetchDetail(recommendationId);
      } else {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Failed to approve recommendation.';
        setActionErrorMsg(msg);
      }
    } finally {
      setSubmittingAction(null);
    }
  };

  const handleRejectSubmit = async () => {
    if (!detail || !recommendationId) return;
    if (!rejectComment.trim()) {
      setActionErrorMsg('Comment is mandatory for rejection.');
      return;
    }

    setSubmittingAction('reject');
    setActionErrorMsg(null);
    setActionSuccessMsg(null);
    setConflictMsg(null);

    try {
      const updated = await rejectRecommendation(recommendationId, rejectComment.trim());
      setDetail(updated);
      setActionSuccessMsg('Recommendation REJECTED.');
      setRejectComment('');
      setShowRejectConfirm(false);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setConflictMsg('This recommendation has already been processed.');
        fetchDetail(recommendationId);
      } else {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Failed to reject recommendation.';
        setActionErrorMsg(msg);
      }
    } finally {
      setSubmittingAction(null);
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
    <div className="recdetail-container">
      <div className="recdetail-topbar">
        <Link to="/recommendations" className="back-link">
          &larr; Back to System Recommendations
        </Link>
        <span className="analysis-badge">
          Decision Support Prototype &bull; No direct DB inventory mutation
        </span>
      </div>

      {loading && (
        <div className="recdetail-loading">
          <div className="recdetail-spinner" />
          <span>Loading recommendation detail and audit history...</span>
        </div>
      )}

      {error && <div className="recdetail-error">{error}</div>}

      {detail && !loading && (
        <div className="recdetail-content">
          {/* Header Card */}
          <header className="recdetail-header">
            <div className="header-meta">
              <div className="badge-row">
                <span className="rec-id-badge">{detail.recommendation_id}</span>
                <span className="type-badge-lg">{detail.recommendation_type}</span>
                {getStatusBadge(detail.status)}
              </div>
              <h1 className="header-sku-title">{detail.sku_name}</h1>
              <p className="header-sub-info">
                Category: <strong>{detail.category}</strong> | Pack Size: <strong>{detail.pack_size ?? 'N/A'}</strong>
              </p>
            </div>
            <div className="effective-qty-box">
              <span className="qty-val-lg">{detail.effective_qty.toLocaleString()}</span>
              <span className="qty-val-label">Effective Quantity (units)</span>
            </div>
          </header>

          {/* Conflict 409 Notice Banner */}
          {conflictMsg && (
            <div className="conflict-banner">
              ⚠️ <strong>Notice:</strong> {conflictMsg}
            </div>
          )}

          {actionSuccessMsg && <div className="action-feedback msg-success">{actionSuccessMsg}</div>}
          {actionErrorMsg && <div className="action-feedback msg-error">{actionErrorMsg}</div>}

          {/* Details 3-Column Grid */}
          <div className="details-grid">
            {/* Card 1: Quantities & Locations */}
            <div className="detail-card">
              <h2 className="card-title">📦 Quantity Breakdown &amp; Locations</h2>
              <div className="info-list">
                <div className="info-row">
                  <span>Proposed Qty (System):</span>
                  <strong>{detail.proposed_qty.toLocaleString()}</strong>
                </div>
                <div className="info-row">
                  <span>Adjusted Qty (Manager):</span>
                  <strong className={detail.adjusted_qty !== null && detail.adjusted_qty !== undefined ? 'text-adjusted' : ''}>
                    {detail.adjusted_qty !== null && detail.adjusted_qty !== undefined ? detail.adjusted_qty.toLocaleString() : '—'}
                  </strong>
                </div>
                <div className="info-row">
                  <span>Effective Qty:</span>
                  <strong className="qty-highlight">{detail.effective_qty.toLocaleString()}</strong>
                </div>
                <div className="info-row">
                  <span>Source Location:</span>
                  <span>{detail.source_location_name ?? detail.source_location_id ?? 'LOC01'}</span>
                </div>
                <div className="info-row">
                  <span>Target Location:</span>
                  <span>{detail.target_location_name ?? detail.target_location_id ?? 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Card 2: Lot & Expiry Context */}
            <div className="detail-card">
              <h2 className="card-title">🏷️ Lot &amp; Expiry Risk Context</h2>
              <div className="info-list">
                <div className="info-row">
                  <span>Lot ID:</span>
                  {detail.lot_id ? (
                    <Link to={`/inventory/lots/${detail.lot_id}`} className="lot-id-link">
                      {detail.lot_id} &rarr;
                    </Link>
                  ) : (
                    <span>N/A</span>
                  )}
                </div>
                <div className="info-row">
                  <span>Expiry Date:</span>
                  <strong>{detail.expiry_date ?? 'N/A'}</strong>
                </div>
                <div className="info-row">
                  <span>Days to Expiry:</span>
                  <strong className={detail.days_to_expiry && detail.days_to_expiry <= 30 ? 'text-danger' : ''}>
                    {detail.days_to_expiry !== null && detail.days_to_expiry !== undefined
                      ? `${detail.days_to_expiry} days`
                      : 'N/A'}
                  </strong>
                </div>
                <div className="info-row">
                  <span>Expiry Risk Assessment:</span>
                  {detail.lot_id ? (
                    <Link to={`/expiry-risk/${detail.lot_id}`} className="risk-center-link">
                      View Risk Score Breakdown &rarr;
                    </Link>
                  ) : (
                    <span>N/A</span>
                  )}
                </div>
              </div>
            </div>

            {/* Card 3: AI Recommendation Rationale */}
            <div className="detail-card">
              <h2 className="card-title">🤖 Proposal Rationale</h2>
              <p className="reason-paragraph">"{detail.reason}"</p>
              <div className="info-list">
                <div className="info-row">
                  <span>Created At:</span>
                  <span>{detail.created_at}</span>
                </div>
                <div className="info-row">
                  <span>Data Status:</span>
                  <span>{detail.data_status}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Warehouse Manager Decision & Action Panel */}
          <section className="action-panel-section">
            <h2 className="panel-title">🛡️ Managerial Action Panel</h2>
            {canApprove ? (
              detail.status === 'PENDING' ? (
                <div className="action-panel-content">
                  {/* Step 1: Optional Quantity Modification */}
                  <div className="action-block block-modify">
                    <h3 className="block-title">Step 1: Modify Quantity (Optional)</h3>
                    <p className="block-desc">
                      Adjust the recommended quantity before approving. Modification leaves status as PENDING and creates a MODIFIED audit entry.
                    </p>
                    <div className="form-group-inline">
                      <div className="input-box">
                        <label htmlFor="mod-qty-input">Adjusted Quantity:</label>
                        <input
                          id="mod-qty-input"
                          type="number"
                          min={1}
                          className="action-input"
                          value={modifyQtyInput}
                          onChange={(e) => setModifyQtyInput(e.target.value)}
                        />
                      </div>
                      <div className="input-box flex-grow">
                        <label htmlFor="mod-comment">Modification Comment (Mandatory):</label>
                        <input
                          id="mod-comment"
                          type="text"
                          className="action-input"
                          placeholder="e.g. Adjusted down due to outlet storage limits..."
                          value={modifyComment}
                          onChange={(e) => setModifyComment(e.target.value)}
                        />
                      </div>
                      <button
                        type="button"
                        className="btn-action btn-modify"
                        onClick={() => setShowModifyConfirm(true)}
                        disabled={submittingAction !== null || !modifyComment.trim()}
                      >
                        Save Quantity Adjustment
                      </button>
                    </div>
                  </div>

                  {/* Step 2: Approve or Reject */}
                  <div className="action-block block-decision">
                    <h3 className="block-title">Step 2: Approve or Reject Recommendation</h3>
                    <p className="block-desc">
                      Finalize decision on the effective quantity (<strong>{detail.effective_qty.toLocaleString()} units</strong>).
                    </p>

                    <div className="decision-grid">
                      {/* Approve Box */}
                      <div className="decision-box box-approve">
                        <h4>Approve Recommendation</h4>
                        <label htmlFor="approve-comment-input">Decision Comment (Mandatory):</label>
                        <textarea
                          id="approve-comment-input"
                          className="action-textarea"
                          rows={2}
                          placeholder="e.g. Approved effective quantity for immediate dispatch..."
                          value={approveComment}
                          onChange={(e) => setApproveComment(e.target.value)}
                        />
                        <button
                          type="button"
                          className="btn-action btn-approve"
                          onClick={() => setShowApproveConfirm(true)}
                          disabled={submittingAction !== null || !approveComment.trim()}
                        >
                          ✓ Approve Proposal
                        </button>
                      </div>

                      {/* Reject Box */}
                      <div className="decision-box box-reject">
                        <h4>Reject Recommendation</h4>
                        <label htmlFor="reject-comment-input">Rejection Comment (Mandatory):</label>
                        <textarea
                          id="reject-comment-input"
                          className="action-textarea"
                          rows={2}
                          placeholder="e.g. Rejected due to sufficient safety stock..."
                          value={rejectComment}
                          onChange={(e) => setRejectComment(e.target.value)}
                        />
                        <button
                          type="button"
                          className="btn-action btn-reject"
                          onClick={() => setShowRejectConfirm(true)}
                          disabled={submittingAction !== null || !rejectComment.trim()}
                        >
                          ✕ Reject Proposal
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="completed-notice">
                  ✅ <strong>Decision Processed:</strong> This recommendation is <strong>{detail.status}</strong> and cannot be further modified.
                </div>
              )
            ) : (
              <div className="readonly-notice">
                ℹ️ <strong>Read-Only Mode:</strong> Logged in as <strong>{user?.username}</strong> ({user?.role}). Only users with the <strong>Warehouse Manager</strong> role are authorized to modify quantity, approve, or reject recommendations.
              </div>
            )}
          </section>

          {/* Audit Timeline Section */}
          <section className="audit-timeline-section">
            <h2 className="panel-title">📜 Immutable Audit History</h2>
            {detail.audit_history.length === 0 ? (
              <p className="no-audit-text">No audit log entries recorded yet.</p>
            ) : (
              <div className="timeline-wrapper">
                <table className="audit-table">
                  <thead>
                    <tr>
                      <th>Audit ID</th>
                      <th>Action</th>
                      <th>Actor</th>
                      <th>Status Change</th>
                      <th>Comment</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.audit_history.map((a) => (
                      <tr key={a.audit_id}>
                        <td>
                          <code>{a.audit_id}</code>
                        </td>
                        <td>
                          <span className={`action-badge action-${a.action.toLowerCase()}`}>{a.action}</span>
                        </td>
                        <td>
                          <strong>{a.actor_username}</strong>
                        </td>
                        <td>
                          <span className="status-flow">
                            {a.before_status} &rarr; {a.after_status}
                          </span>
                        </td>
                        <td className="comment-text-cell">{a.comment ?? '—'}</td>
                        <td className="timestamp-cell">{a.action_timestamp}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}

      {/* Confirmation Dialog Modals */}
      {showModifyConfirm && (
        <div className="modal-overlay">
          <div className="modal-box">
            <h3>Confirm Quantity Adjustment</h3>
            <p>
              Are you sure you want to adjust the recommended quantity for <strong>{detail?.recommendation_id}</strong> to{' '}
              <strong>{parseInt(modifyQtyInput, 10).toLocaleString()} units</strong>?
            </p>
            <div className="modal-actions">
              <button type="button" className="btn-modal-cancel" onClick={() => setShowModifyConfirm(false)}>
                Cancel
              </button>
              <button type="button" className="btn-modal-confirm" onClick={handleModifyQuantitySubmit}>
                Confirm Adjustment
              </button>
            </div>
          </div>
        </div>
      )}

      {showApproveConfirm && (
        <div className="modal-overlay">
          <div className="modal-box">
            <h3>Confirm Recommendation Approval</h3>
            <p>
              Are you sure you want to <strong>APPROVE</strong> recommendation <strong>{detail?.recommendation_id}</strong> with an effective quantity of{' '}
              <strong>{detail?.effective_qty.toLocaleString()} units</strong>?
            </p>
            <div className="modal-actions">
              <button type="button" className="btn-modal-cancel" onClick={() => setShowApproveConfirm(false)}>
                Cancel
              </button>
              <button type="button" className="btn-modal-confirm btn-confirm-approve" onClick={handleApproveSubmit}>
                Confirm Approval
              </button>
            </div>
          </div>
        </div>
      )}

      {showRejectConfirm && (
        <div className="modal-overlay">
          <div className="modal-box">
            <h3>Confirm Recommendation Rejection</h3>
            <p>
              Are you sure you want to <strong>REJECT</strong> recommendation <strong>{detail?.recommendation_id}</strong>?
            </p>
            <div className="modal-actions">
              <button type="button" className="btn-modal-cancel" onClick={() => setShowRejectConfirm(false)}>
                Cancel
              </button>
              <button type="button" className="btn-modal-confirm btn-confirm-reject" onClick={handleRejectSubmit}>
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      <footer className="recdetail-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
