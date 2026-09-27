import { LANGUAGES } from "../i18n";
import { useI18n } from "../useI18n";

// Small dropdown: Kiswahili / English / Français. Works anywhere - Login, register, or the top bar.
export default function LanguageSwitcher({ dark = false }) {
  const { lang, setLang } = useI18n();
  return (
    <select
      value={lang}
      onChange={(e) => setLang(e.target.value)}
      aria-label="Language / Lugha / Langue"
      style={dark ? { background: "transparent", color: "#fff", border: "1px solid #fff" } : undefined}
    >
      {Object.entries(LANGUAGES).map(([code, name]) => (
        <option key={code} value={code} style={{ color: "#000" }}>{name}</option>
      ))}
    </select>
  );
}
