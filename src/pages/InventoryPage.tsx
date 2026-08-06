import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getInventoryList, type InventoryItem } from '../api/inventory';
import './InventoryPage.css';

export default function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [selectedExpiryBucket, setSelectedExpiryBucket] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    getInventoryList({
      category: selectedCategory || undefined,
      scenario: selectedScenario || undefined,
      expiry_bucket: selectedExpiryBucket || undefined,
      limit: 200,
    })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((err) => setError(err?.message ?? 'Failed to load inventory'))
      .finally(() => setLoading(false));
  }, [selectedCategory, selectedScenario, selectedExpiryBucket]);

  // Client-side search filter for SKU or Name or Lot
  const filteredItems = items.filter((item) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.sku_id.toLowerCase().includes(term) ||
      item.sku_name.toLowerCase().includes(term) ||
      item.lot_id.toLowerCase().includes(term)
    );
  });

  const CATEGORIES = [
    'Fresh Milk',
    'Nutritional Milk',
    'Nut Milk',
    'Soy Milk',
    'Ready-to-Drink Formula',
  ];

  const SCENARIOS = [
    { value: 'normal', label: 'Normal' },
    { value: 'stockout', label: 'Stock-out' },
    { value: 'expiry', label: 'Expiry Risk' },
    { value: 'transfer', label: 'Transfer Required' },
  ];

  const EXPIRY_BUCKETS = [
    { value: 'expired', label: 'Expired (<=0 days)' },
    { value: '<=30', label: 'Critical (1-30 days)' },
    { value: '31-60', label: 'High Risk (31-60 days)' },
    { value: '61-90', label: 'Medium Risk (61-90 days)' },
    { value: '>90', label: 'Safe (>90 days)' },
  ];

  const getScenarioBadge = (scenario: string) => {
    switch (scenario) {
      case 'stockout':
        return <span className="badge badge-stockout">Stock-out</span>;
      case 'expiry':
        return <span className="badge badge-expiry">Expiry Risk</span>;
      case 'transfer':
        return <span className="badge badge-transfer">Transfer</span>;
      default:
        return <span className="badge badge-normal">Normal</span>;
    }
  };

  const getExpiryBadge = (days: number) => {
    if (days <= 0) return <span className="expiry-tag tag-expired">{days}d (Expired)</span>;
    if (days <= 30) return <span className="expiry-tag tag-critical">{days}d</span>;
    if (days <= 60) return <span className="expiry-tag tag-high">{days}d</span>;
    if (days <= 90) return <span className="expiry-tag tag-medium">{days}d</span>;
    return <span className="expiry-tag tag-safe">{days}d</span>;
  };

  return (
    <div className="inventory-container">
      <header className="inventory-header">
        <div>
          <h1 className="inventory-title">Inventory Balances & FEFO Priority</h1>
          <p className="inventory-sub">
            Real-time stock status across pilot warehouse locations — Total Records: <strong>{total}</strong>
          </p>
        </div>
      </header>

      {/* Filter Control Bar */}
      <div className="inventory-filters-bar">
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
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <select
            className="filter-select"
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
          >
            <option value="">All Scenarios</option>
            {SCENARIOS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
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

        {(selectedCategory || selectedScenario || selectedExpiryBucket || searchTerm) && (
          <button
            className="clear-filters-btn"
            onClick={() => {
              setSelectedCategory('');
              setSelectedScenario('');
              setSelectedExpiryBucket('');
              setSearchTerm('');
            }}
          >
            Clear Filters
          </button>
        )}
      </div>

      {loading && (
        <div className="inventory-loading">
          <div className="inventory-spinner" />
          <span>Loading inventory balances from SQLite...</span>
        </div>
      )}

      {error && <div className="inventory-error">{error}</div>}

      {!loading && !error && (
        <div className="inventory-table-wrapper">
          <table className="inventory-table">
            <thead>
              <tr>
                <th>FEFO Priority</th>
                <th>SKU ID</th>
                <th>SKU Name</th>
                <th>Category</th>
                <th>Lot ID</th>
                <th>Location</th>
                <th>On Hand</th>
                <th>Available</th>
                <th>Reserved</th>
                <th>Quarantine</th>
                <th>Expiry Date</th>
                <th>Days Left</th>
                <th>Scenario</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={13} className="empty-row">
                    No inventory records match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr key={item.inventory_id}>
                    <td>
                      <span className="fefo-rank">#{item.fefo_priority}</span>
                    </td>
                    <td>
                      <code>{item.sku_id}</code>
                    </td>
                    <td className="sku-name-cell">{item.sku_name}</td>
                    <td>
                      <span className="category-tag">{item.category}</span>
                    </td>
                    <td>
                      <Link to={`/inventory/lots/${item.lot_id}`} className="lot-link">
                        {item.lot_id}
                      </Link>
                    </td>
                    <td className="location-cell">{item.location_name}</td>
                    <td className="qty-cell strong-qty">{item.on_hand_qty.toLocaleString()}</td>
                    <td className="qty-cell">{item.available_qty.toLocaleString()}</td>
                    <td className="qty-cell">{item.reserved_qty.toLocaleString()}</td>
                    <td className="qty-cell">{item.quarantine_qty.toLocaleString()}</td>
                    <td>{item.expiry_date}</td>
                    <td>{getExpiryBadge(item.days_to_expiry)}</td>
                    <td>{getScenarioBadge(item.scenario)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <footer className="inventory-disclaimer">
        Demonstration using public product master references and synthetic operational data — not actual Vinamilk operational data.
      </footer>
    </div>
  );
}
