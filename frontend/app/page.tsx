import { DashboardShell } from "@/components/dashboard-shell";
import { fetchDashboardSummary } from "@/lib/api";

export default async function HomePage() {
  const dashboardData = await fetchDashboardSummary();

  return <DashboardShell data={dashboardData} />;
}
