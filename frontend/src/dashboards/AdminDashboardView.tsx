import { AdminKpiView } from "../admin/AdminKpiView";
import { AdminManagementView } from "../admin/AdminManagementView";
import { DispatchPage } from "../dispatch/DispatchPage";

export function AdminDashboardView() {
  return <><AdminKpiView /><AdminManagementView /><DispatchPage /></>;
}