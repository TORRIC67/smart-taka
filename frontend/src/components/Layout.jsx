import { useAuth } from "../auth.jsx";
import { useI18n } from "../useI18n";
import LanguageSwitcher from "./LanguageSwitcher.jsx";

// Green top bar with the app name, optional navigation (tabs) and the logout button
export default function Layout({ nav, children }) {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  return (
    <div>
      <header className="topbar">
        <div className="brand">Smart Taka</div>
        {nav}
        <div className="who">
          <LanguageSwitcher dark />
          <span>{user?.full_name}</span>
          <button className="btn ghost" onClick={logout}>{t("logout")}</button>
        </div>
      </header>
      <main className="page">{children}</main>
    </div>
  );
}
