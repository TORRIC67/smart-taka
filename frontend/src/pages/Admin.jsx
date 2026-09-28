import { useState } from "react";
import Layout from "../components/Layout.jsx";
import Overview from "./admin/Overview.jsx";
import Residents from "./admin/Residents.jsx";
import Register from "./admin/Register.jsx";
import Bins from "./admin/Bins.jsx";
import Fleet from "./admin/Fleet.jsx";
import RoutesTab from "./admin/Routes.jsx";
import Complaints from "./admin/Complaints.jsx";
import Admins from "./admin/Admins.jsx";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../useI18n";

const TAB_IDS = [
  ["overview", "tab_overview", Overview],
  ["residents", "tab_residents", Residents],
  ["register", "tab_register", Register],
  ["bins", "tab_bins", Bins],
  ["fleet", "tab_fleet", Fleet],
  ["routes", "tab_routes", RoutesTab],
  ["complaints", "tab_complaints", Complaints],
];
// Only the super admin can add/remove other admins, so only they get this tab
const ADMINS_TAB = ["admins", "tab_admins", Admins];

export default function Admin() {
  const { t } = useI18n();
  const { user } = useAuth();
  const tabs = user?.role === "super_admin" ? [...TAB_IDS, ADMINS_TAB] : TAB_IDS;
  const [tab, setTab] = useState("overview");
  const Current = (tabs.find(([id]) => id === tab) || tabs[0])[2];
  const nav = (
    <nav className="tabs">
      {tabs.map(([id, labelKey]) => (
        <button key={id} className={`tab ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}>{t(labelKey)}</button>
      ))}
    </nav>
  );
  return <Layout nav={nav}><Current /></Layout>;
}
