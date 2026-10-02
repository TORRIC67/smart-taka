import { useState } from "react";
import {
  LayoutDashboard, Users, UserPlus, Trash2, Truck, Route, MessageSquare,
  BarChart3, Shield, Building2,
} from "lucide-react";
import AdminLayout from "../components/AdminLayout.jsx";
import Overview from "./admin/Overview.jsx";
import Residents from "./admin/Residents.jsx";
import Register from "./admin/Register.jsx";
import Bins from "./admin/Bins.jsx";
import Fleet from "./admin/Fleet.jsx";
import RoutesTab from "./admin/Routes.jsx";
import Complaints from "./admin/Complaints.jsx";
import Reports from "./admin/Reports.jsx";
import Admins from "./admin/Admins.jsx";
import Providers from "./admin/Providers.jsx";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../useI18n";

const ICON_SIZE = 18;
const TAB_IDS = [
  ["overview", "tab_overview", Overview, <LayoutDashboard size={ICON_SIZE} />],
  ["residents", "tab_residents", Residents, <Users size={ICON_SIZE} />],
  ["register", "tab_register", Register, <UserPlus size={ICON_SIZE} />],
  ["bins", "tab_bins", Bins, <Trash2 size={ICON_SIZE} />],
  ["fleet", "tab_fleet", Fleet, <Truck size={ICON_SIZE} />],
  ["routes", "tab_routes", RoutesTab, <Route size={ICON_SIZE} />],
  ["complaints", "tab_complaints", Complaints, <MessageSquare size={ICON_SIZE} />],
  ["reports", "tab_reports", Reports, <BarChart3 size={ICON_SIZE} />],
];
// Only the super admin manages zones and other admins, so only they get these tabs
const SUPER_ADMIN_TABS = [
  ["providers", "tab_providers", Providers, <Building2 size={ICON_SIZE} />],
  ["admins", "tab_admins", Admins, <Shield size={ICON_SIZE} />],
];

export default function Admin() {
  const { t } = useI18n();
  const { user } = useAuth();
  const allTabs = user?.role === "super_admin" ? [...TAB_IDS, ...SUPER_ADMIN_TABS] : TAB_IDS;
  const [tab, setTab] = useState("overview");
  const Current = (allTabs.find(([id]) => id === tab) || allTabs[0])[2];

  const items = allTabs.map(([id, labelKey, , icon]) => ({
    id, icon, label: t(labelKey), active: tab === id, onClick: () => setTab(id),
  }));

  return <AdminLayout items={items}><Current /></AdminLayout>;
}
