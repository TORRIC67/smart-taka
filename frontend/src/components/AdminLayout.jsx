import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../useI18n";
import LanguageSwitcher from "./LanguageSwitcher.jsx";

// items: [{ id, label, icon: <Component/>, onClick, active }]
export default function AdminLayout({ items, children }) {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const [open, setOpen] = useState(false); // mobile sidebar drawer

  return (
    <div className="admin-shell">
      <div className={`admin-sidebar-overlay ${open ? "open" : ""}`} onClick={() => setOpen(false)} />

      <aside className={`admin-sidebar ${open ? "open" : ""}`}>
        <div className="admin-sidebar-brand">
          🌿 Smart Taka
          <small>{t("sidebar_tagline")}</small>
          <button className="admin-sidebar-close" style={{ marginLeft: "auto", color: "#fff" }} onClick={() => setOpen(false)} aria-label="close">
            <X size={20} />
          </button>
        </div>
        <nav className="admin-nav">
          {items.map((item) => (
            <button
              key={item.id}
              className={`admin-nav-item ${item.active ? "active" : ""}`}
              onClick={() => { item.onClick(); setOpen(false); }}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>
        <div className="admin-sidebar-footer">
          <Link to="/change-password" className="admin-nav-item" style={{ textDecoration: "none" }}>{t("change_password_link")}</Link>
          <button className="admin-nav-item" onClick={logout}>{t("logout")}</button>
        </div>
      </aside>

      <div className="admin-main">
        <header className="admin-topbar">
          <button className="admin-sidebar-toggle" onClick={() => setOpen(true)} aria-label="menu">
            <Menu size={22} />
          </button>
          <div className="grow" />
          <LanguageSwitcher />
          <span className="who-name">{user?.full_name}</span>
        </header>
        <main className="admin-content">{children}</main>
      </div>
    </div>
  );
}
