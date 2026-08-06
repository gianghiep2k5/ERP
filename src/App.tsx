import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import RequireAuth from './auth/RequireAuth';
import AppShell from './components/layout/AppShell';
import HealthPage from './pages/HealthPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import InventoryPage from './pages/InventoryPage';
import LotDetailPage from './pages/LotDetailPage';
import ExpiryRiskPage from './pages/ExpiryRiskPage';
import ExpiryRiskDetailPage from './pages/ExpiryRiskDetailPage';
import ForecastPage from './pages/ForecastPage';
import RecommendationsPage from './pages/RecommendationsPage';
import RecommendationDetailPage from './pages/RecommendationDetailPage';
import AuditPage from './pages/AuditPage';

/**
 * RootRedirect handles / route:
 * - if unauthenticated -> redirects to /login
 * - if authenticated -> redirects to /dashboard
 */
function RootRedirect() {
  const { user, isLoading } = useAuth();
  if (isLoading) return null;
  return user ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Root redirect */}
          <Route path="/" element={<RootRedirect />} />

          {/* Public / Diagnostic routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/health" element={<HealthPage />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <AppShell>
                  <DashboardPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/inventory"
            element={
              <RequireAuth>
                <AppShell>
                  <InventoryPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/inventory/lots/:lotId"
            element={
              <RequireAuth>
                <AppShell>
                  <LotDetailPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/expiry-risk"
            element={
              <RequireAuth>
                <AppShell>
                  <ExpiryRiskPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/expiry-risk/:lotId"
            element={
              <RequireAuth>
                <AppShell>
                  <ExpiryRiskDetailPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/forecast"
            element={
              <RequireAuth>
                <AppShell>
                  <ForecastPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/recommendations"
            element={
              <RequireAuth>
                <AppShell>
                  <RecommendationsPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/recommendations/:recommendationId"
            element={
              <RequireAuth>
                <AppShell>
                  <RecommendationDetailPage />
                </AppShell>
              </RequireAuth>
            }
          />
          <Route
            path="/audit"
            element={
              <RequireAuth>
                <AppShell>
                  <AuditPage />
                </AppShell>
              </RequireAuth>
            }
          />

          {/* Catch-all: redirect to root */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
