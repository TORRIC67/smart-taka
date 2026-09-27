import { useState } from "react";
import Layout from "../components/Layout.jsx";
import Overview from "./admin/Overview.jsx";
import Residents from "./admin/Residents.jsx";
import Register from "./admin/Register.jsx";
import RoutesTab from "./admin/Routes.jsx";
import Complaints from "./admin/Complaints.jsx";
import { useI18n } from "../useI18n";

const TAB_IDS = [
  ["overview", "tab_overview", Overview],
  ["residents", "tab_residents", Residents],
  ["register", "tab_register", Register],
  ["routes", "tab_routes", RoutesTab],
  ["complaints", "tab_complaints", Complaints],
];

export default function Admin() {
  const { t } = useI18n();
  const [tab, setTab] = useState("overview");
  const Current = TAB_IDS.find(([id]) => id === tab)[2];
  const nav = (
    <nav className="tabs">
      {TAB_IDS.map(([id, labelKey]) => (
        <button key={id} className={`tab ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}>{t(labelKey)}</button>
      ))}
    </nav>
  );
  return <Layout nav={nav}><Current /></Layout>;
}
