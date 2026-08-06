import { useEffect, useState, useMemo } from 'react';
import {
  getForecastSKUs,
  getForecastSKUDetail,
  submitPlannerReview,
  type ForecastSKUListItem,
  type ForecastSKUDetailResponse,
} from '../api/forecast';
import { useAuth } from '../auth/AuthContext';
import './ForecastPage.css';

export default function ForecastPage() {
  const { user } = useAuth();
  const isPlanner = user?.role === 'Planner';

  const [skuList, setSkuList] = useState<ForecastSKUListItem[]>([]);
  const [selectedSkuId, setSelectedSkuId] = useState<string>('SKU001');
  const [detail, setDetail] = useState<ForecastSKUDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search filter for SKU dropdown
  const [skuSearch, setSkuSearch] = useState('');

  // Planner Review form state
  const [reviewStatus, setReviewStatus] = useState<string>('ACCEPTED_AS_BASELINE');
  const [plannerComment, setPlannerComment] = useState<string>('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);
  const [reviewErrorMsg, setReviewErrorMsg] = useState<string | null>(null);

  // Hover state for chart tooltip
  const [hoverPoint, setHoverPoint] = useState<{
    date: string;
    value: number;
    type: 'actual' | 'forecast';
    x: number;
    y: number;
  } | null>(null);

  // 1. Fetch SKU list on mount
  useEffect(() => {
    getForecastSKUs()
      .then((items) => {
        setSkuList(items);
        if (items.length > 0) {
          setSelectedSkuId(items[0].sku_id);
        }
      })
      .catch((err) => setError(err?.message ?? 'Failed to load forecast SKU list'));
  }, []);

  // 2. Fetch detail when selectedSkuId changes
  useEffect(() => {
    if (!selectedSkuId) return;
    setLoading(true);
    setReviewSuccessMsg(null);
    setReviewErrorMsg(null);

    getForecastSKUDetail(selectedSkuId)
      .then((data) => {
        setDetail(data);
        if (data.latest_review) {
          setReviewStatus(data.latest_review.review_status);
        } else {
          setReviewStatus('ACCEPTED_AS_BASELINE');
        }
        setPlannerComment('');
      })
      .catch((err) => setError(err?.message ?? `Failed to load forecast for ${selectedSkuId}`))
      .finally(() => setLoading(false));
  }, [selectedSkuId]);

  // Handle Review submission
  const handleSaveReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPlanner || !detail) return;

    if (!plannerComment.trim()) {
      setReviewErrorMsg('Planner comment is mandatory and cannot be blank.');
      return;
    }

    setSubmittingReview(true);
    setReviewErrorMsg(null);
    setReviewSuccessMsg(null);

    try {
      const newReview = await submitPlannerReview(detail.sku_id, {
        review_status: reviewStatus,
        planner_comment: plannerComment.trim(),
      });

      setReviewSuccessMsg('Planner review saved and persisted successfully.');
      setPlannerComment('');

      // Reload detail to update history & status
      const updated = await getForecastSKUDetail(detail.sku_id);
      setDetail(updated);

      // Update local SKU list status badge
      setSkuList((prev) =>
        prev.map((item) =>
          item.sku_id === detail.sku_id
            ? { ...item, review_status: newReview.review_status }
            : item
        )
      );
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to save planner review.';
      setReviewErrorMsg(msg);
    } finally {
      setSubmittingReview(false);
    }
  };

  const filteredSKUs = useMemo(() => {
    if (!skuSearch) return skuList;
    const term = skuSearch.toLowerCase();
    return skuList.filter(
      (s) => s.sku_id.toLowerCase().includes(term) || s.sku_name.toLowerCase().includes(term)
    );
  }, [skuList, skuSearch]);

  // SVG Chart layout calculations with distinct, non-overlapping series & boundary
  const chartData = useMemo(() => {
    if (!detail) return null;
    const actuals = detail.actual_sales;
    const forecasts = detail.forecast_results;

    const allValues = [
      ...actuals.map((a) => a.quantity_sold),
      ...forecasts.map((f) => f.forecast_qty),
    ];
    const maxVal = Math.max(...allValues, 100);
    const minVal = 0;

    const width = 900;
    const height = 320;
    const padding = { top: 30, right: 30, bottom: 40, left: 55 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const totalPoints = actuals.length + forecasts.length; // 365 + 30 = 395 points
    const stepX = chartW / (totalPoints - 1);

    const getY = (val: number) =>
      padding.top + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;

    // Actual points (0 to 364) -> dates 2025-08-06 to 2026-08-05
    const actualPoints = actuals.map((a, i) => ({
      x: padding.left + i * stepX,
      y: getY(a.quantity_sold),
      date: a.sales_date,
      value: a.quantity_sold,
      type: 'actual' as const,
    }));

    // Boundary X positioned halfway between 2026-08-05 (index 364) and 2026-08-06 (index 365)
    const boundaryX = padding.left + (actuals.length - 0.5) * stepX;

    // Forecast points (365 to 394) -> dates 2026-08-06 to 2026-09-04 (no overlap with actuals)
    const forecastPoints = forecasts.map((f, i) => ({
      x: padding.left + (actuals.length + i) * stepX,
      y: getY(f.forecast_qty),
      date: f.forecast_date,
      value: f.forecast_qty,
      type: 'forecast' as const,
    }));

    const actualD = actualPoints.reduce(
      (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
      ''
    );

    const forecastD = forecastPoints.reduce(
      (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
      ''
    );

    return {
      width,
      height,
      padding,
      chartW,
      chartH,
      maxVal,
      boundaryX,
      actualPoints,
      forecastPoints,
      actualD,
      forecastD,
    };
  }, [detail]);

  const getStatusBadge = (status?: string | null) => {
    if (!status) return <span className="status-chip chip-none">NEEDS REVIEW</span>;
    switch (status) {
      case 'ACCEPTED_AS_BASELINE':
        return <span className="status-chip chip-accepted">ACCEPTED BASELINE</span>;
      case 'ADJUSTMENT_REQUIRED':
        return <span className="status-chip chip-adjustment">ADJUSTMENT REQUIRED</span>;
      case 'MONITOR':
        return <span className="status-chip chip-monitor">MONITOR</span>;
      default:
        return <span className="status-chip">{status}</span>;
    }
  };

  return (
    <div className="forecast-container">
      <header className="forecast-header">
        <div>
          <h1 className="forecast-title">Demand Forecast &amp; Planner Review</h1>
          <p className="forecast-sub">
            Evaluate 365 days of actual sales history and 30 days of baseline forecast outputs.
          </p>
        </div>
      </header>

      {/* SKU Selector Bar */}
      <div className="sku-selector-bar">
        <div className="search-group">
          <label htmlFor="sku-search">Search SKU:</label>
          <input
            id="sku-search"
            type="text"
            className="sku-search-input"
            placeholder="Filter SKU name or ID..."
            value={skuSearch}
            onChange={(e) => setSkuSearch(e.target.value)}
          />
        </div>

        <div className="dropdown-group">
          <label htmlFor="sku-select">Select SKU ({filteredSKUs.length} available):</label>
          <select
            id="sku-select"
            className="sku-select-dropdown"
            value={selectedSkuId}
            onChange={(e) => setSelectedSkuId(e.target.value)}
          >
            {filteredSKUs.map((s) => (
              <option key={s.sku_id} value={s.sku_id}>
                {s.sku_id} - {s.sku_name} ({s.category})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="forecast-loading">
          <div className="forecast-spinner" />
          <span>Fetching actual sales observations and forecast baseline...</span>
        </div>
      )}

      {error && <div className="forecast-error">{error}</div>}

      {detail && !loading && (
        <div className="forecast-content">
          {/* SKU Header Card */}
          <div className="sku-meta-card">
            <div className="sku-meta-info">
              <div className="sku-title-row">
                <span className="sku-id-badge">{detail.sku_id}</span>
                <span className="sku-category-tag">{detail.category}</span>
                {getStatusBadge(detail.latest_review?.review_status)}
              </div>
              <h2 className="sku-name-heading">{detail.sku_name}</h2>
              <p className="sku-run-details">
                Model: <strong>{detail.model_name}</strong> | Run ID: <code>{detail.forecast_run_id}</code> | Evaluation Window: <strong>{detail.evaluation_window_days} days</strong>
              </p>
            </div>
          </div>

          {/* Metric KPI Cards */}
          <div className="metric-kpi-grid">
            <div className="metric-card">
              <span className="metric-label">Forecast WAPE</span>
              <span className="metric-val">{(detail.wape * 100).toFixed(2)}%</span>
              <span className="metric-desc">Weighted Absolute Percentage Error (stored metric)</span>
            </div>

            <div className="metric-card">
              <span className="metric-label">Forecast Bias</span>
              <span className="metric-val">
                {detail.bias >= 0 ? `+${(detail.bias * 100).toFixed(2)}%` : `${(detail.bias * 100).toFixed(2)}%`}
              </span>
              <span className="metric-desc" title="Stored metric evaluated on run date 2026-08-05 across the 30-day evaluation window.">
                Directional variance from evaluation baseline
              </span>
            </div>

            <div className="metric-card card-review">
              <span className="metric-label">Planner Review</span>
              <span className="metric-val review-val">
                {detail.latest_review ? detail.latest_review.review_status : 'PENDING'}
              </span>
              <span className="metric-desc">
                {detail.latest_review
                  ? `Reviewed by ${detail.latest_review.reviewer_username}`
                  : 'Awaiting Planner evaluation'}
              </span>
            </div>
          </div>

          {/* Forecast Chart Section */}
          <section className="chart-section">
            <div className="chart-header-row">
              <div>
                <h3 className="chart-title">Demand Trajectory &amp; Baseline Forecast</h3>
                <p className="chart-notice">
                  365 days of actual sales and 30 days of forecast.
                </p>
              </div>
              <div className="chart-legend">
                <span className="legend-item">
                  <span className="legend-line line-actual" /> 12-month Actual Sales
                </span>
                <span className="legend-item">
                  <span className="legend-line line-forecast" /> 30-day Forecast
                </span>
                <span className="legend-item">
                  <span className="legend-boundary-marker" /> Forecast begins: 2026-08-06
                </span>
              </div>
            </div>

            {/* Responsive Interactive SVG Line Chart */}
            {chartData && (
              <div className="svg-chart-container">
                <svg
                  viewBox={`0 0 ${chartData.width} ${chartData.height}`}
                  className="svg-chart"
                >
                  {/* Grid Lines */}
                  {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                    const y = chartData.padding.top + chartData.chartH * (1 - ratio);
                    const val = Math.round(chartData.maxVal * ratio);
                    return (
                      <g key={ratio}>
                        <line
                          x1={chartData.padding.left}
                          y1={y}
                          x2={chartData.width - chartData.padding.right}
                          y2={y}
                          stroke="rgba(255, 255, 255, 0.07)"
                          strokeDasharray="4 4"
                        />
                        <text
                          x={chartData.padding.left - 8}
                          y={y + 4}
                          fill="#64748b"
                          fontSize="10"
                          textAnchor="end"
                        >
                          {val.toLocaleString()}
                        </text>
                      </g>
                    );
                  })}

                  {/* Vertical Forecast Boundary Line positioned between 2026-08-05 and 2026-08-06 */}
                  <line
                    x1={chartData.boundaryX}
                    y1={chartData.padding.top}
                    x2={chartData.boundaryX}
                    y2={chartData.height - chartData.padding.bottom}
                    stroke="#38bdf8"
                    strokeWidth="2"
                    strokeDasharray="6 4"
                  />
                  <text
                    x={chartData.boundaryX}
                    y={chartData.padding.top - 8}
                    fill="#38bdf8"
                    fontSize="11"
                    fontWeight="700"
                    textAnchor="middle"
                  >
                    Forecast begins: 2026-08-06
                  </text>

                  {/* 12-month Actual Sales Line (Solid Indigo) */}
                  <path
                    d={chartData.actualD}
                    fill="none"
                    stroke="#818cf8"
                    strokeWidth="2"
                  />

                  {/* 30-day Forecast Line (Dashed Green) - starts at 2026-08-06 */}
                  <path
                    d={chartData.forecastD}
                    fill="none"
                    stroke="#34d399"
                    strokeWidth="2.5"
                    strokeDasharray="5 4"
                  />

                  {/* Interactive Hover Circles */}
                  {chartData.actualPoints.map((p, idx) => (
                    <circle
                      key={`act-${idx}`}
                      cx={p.x}
                      cy={p.y}
                      r={3}
                      fill="transparent"
                      className="chart-hover-circle"
                      onMouseEnter={() => setHoverPoint(p)}
                      onMouseLeave={() => setHoverPoint(null)}
                    />
                  ))}
                  {chartData.forecastPoints.map((p, idx) => (
                    <circle
                      key={`fc-${idx}`}
                      cx={p.x}
                      cy={p.y}
                      r={4}
                      fill="#34d399"
                      className="chart-hover-circle"
                      onMouseEnter={() => setHoverPoint(p)}
                      onMouseLeave={() => setHoverPoint(null)}
                    />
                  ))}

                  {/* X-axis date labels */}
                  <text
                    x={chartData.padding.left}
                    y={chartData.height - 12}
                    fill="#64748b"
                    fontSize="10"
                  >
                    {detail.actual_start_date} (Actuals Start)
                  </text>
                  <text
                    x={chartData.boundaryX}
                    y={chartData.height - 12}
                    fill="#38bdf8"
                    fontSize="10"
                    textAnchor="middle"
                  >
                    2026-08-05 | 2026-08-06
                  </text>
                  <text
                    x={chartData.width - chartData.padding.right}
                    y={chartData.height - 12}
                    fill="#34d399"
                    fontSize="10"
                    textAnchor="end"
                  >
                    {detail.forecast_end_date} (30d Forecast End)
                  </text>
                </svg>

                {/* Hover Tooltip */}
                {hoverPoint && (
                  <div
                    className="chart-tooltip"
                    style={{
                      left: `${(hoverPoint.x / chartData.width) * 100}%`,
                      top: `${(hoverPoint.y / chartData.height) * 100}%`,
                    }}
                  >
                    <span className="tooltip-date">{hoverPoint.date}</span>
                    <span className="tooltip-val">
                      {hoverPoint.type === 'actual' ? 'Actual Sales' : 'Forecast Qty'}:{' '}
                      <strong>{hoverPoint.value.toLocaleString()} units</strong>
                    </span>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* Planner Review Panel */}
          <section className="review-section">
            <h3 className="section-title">Planner Review Panel</h3>
            {isPlanner ? (
              <form onSubmit={handleSaveReview} className="review-form">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="review-status-select">Review Status:</label>
                    <select
                      id="review-status-select"
                      className="form-select"
                      value={reviewStatus}
                      onChange={(e) => setReviewStatus(e.target.value)}
                    >
                      <option value="ACCEPTED_AS_BASELINE">ACCEPTED AS BASELINE</option>
                      <option value="ADJUSTMENT_REQUIRED">ADJUSTMENT REQUIRED</option>
                      <option value="MONITOR">MONITOR</option>
                    </select>
                  </div>

                  <div className="form-group flex-2">
                    <label htmlFor="planner-comment">Planner Comment (Mandatory):</label>
                    <textarea
                      id="planner-comment"
                      className="form-textarea"
                      rows={2}
                      placeholder="Enter rationale for forecast review..."
                      value={plannerComment}
                      onChange={(e) => setPlannerComment(e.target.value)}
                      required
                    />
                  </div>
                </div>

                {reviewErrorMsg && <div className="review-msg msg-error">{reviewErrorMsg}</div>}
                {reviewSuccessMsg && <div className="review-msg msg-success">{reviewSuccessMsg}</div>}

                <div className="form-actions">
                  <button
                    type="submit"
                    className="btn-save-review"
                    disabled={submittingReview || !plannerComment.trim()}
                  >
                    {submittingReview ? 'Saving Review...' : 'Save Planner Review'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="readonly-review-notice">
                <p className="readonly-text">
                  ℹ️ <strong>Read-Only Access:</strong> You are logged in as <strong>{user?.username}</strong> ({user?.role}). Only users with the <strong>Planner</strong> role can submit or edit forecast reviews.
                </p>
                {detail.latest_review ? (
                  <div className="latest-review-box">
                    <div>Status: {getStatusBadge(detail.latest_review.review_status)}</div>
                    <div>Reviewer: <strong>{detail.latest_review.reviewer_username}</strong></div>
                    <div>Reviewed At: <span>{detail.latest_review.reviewed_at}</span></div>
                    <div className="comment-box">Comment: "{detail.latest_review.planner_comment}"</div>
                  </div>
                ) : (
                  <p className="no-reviews-msg">No Planner reviews recorded for this baseline yet.</p>
                )}
              </div>
            )}

            {/* Review History Traceability */}
            {detail.review_history.length > 0 && (
              <div className="history-section">
                <h4 className="history-heading">Review Audit History</h4>
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>Review ID</th>
                      <th>Status</th>
                      <th>Planner</th>
                      <th>Comment</th>
                      <th>Reviewed At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.review_history.map((rev) => (
                      <tr key={rev.review_id}>
                        <td><code>{rev.review_id}</code></td>
                        <td>{getStatusBadge(rev.review_status)}</td>
                        <td><strong>{rev.reviewer_username}</strong></td>
                        <td className="comment-cell">{rev.planner_comment}</td>
                        <td className="time-cell">{rev.reviewed_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}

      <footer className="forecast-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
