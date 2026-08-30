import { useQuery } from "@tanstack/react-query";
import { getCurrentVitals } from "./api/client";
import { MonitoringPage } from "./monitoring/MonitoringPage";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AdminDashboardView } from "./dashboards/AdminDashboardView";
import { DoctorDashboardView } from "./dashboards/DoctorDashboardView";
import { NurseDashboardView } from "./dashboards/NurseDashboardView";
import { AlertPage } from "./alerts/AlertPage";

export function App() {
  return <AuthProvider><ProtectedRoute><RoleApp /></ProtectedRoute></AuthProvider>;
}
function RoleApp() {
  const { user } = useAuth();
  const query = useQuery({
    queryKey: ["current-vitals", "P-1042"],
    queryFn: () => getCurrentVitals("P-1042"),
    retry: false,
  });

  if (query.isLoading) {
    return <MonitoringPage />;
  }

  return <main><header><strong>{user?.display_name}</strong><span> {user?.role}</span></header>{user?.role === "admin" ? <AdminDashboardView /> : user?.role === "doctor" ? <DoctorDashboardView /> : <NurseDashboardView />}<MonitoringPage observation={query.data} freshnessOverride={query.data?.freshness ?? "unavailable"} />{user?.role !== "nurse" ? <AlertPage /> : null}</main>;
}
