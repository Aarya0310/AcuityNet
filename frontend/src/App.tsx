import { useQuery } from "@tanstack/react-query";
import { getCurrentVitals } from "./api/client";
import { MonitoringPage } from "./monitoring/MonitoringPage";

export function App() {
  const query = useQuery({
    queryKey: ["current-vitals", "P-1042"],
    queryFn: () => getCurrentVitals("P-1042"),
    retry: false,
  });

  if (query.isLoading) {
    return <MonitoringPage />;
  }

  return <MonitoringPage observation={query.data} freshnessOverride={query.data?.freshness ?? "unavailable"} />;
}
