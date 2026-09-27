import { Link } from "react-router-dom";
import FormCard from "../components/FormCard.jsx";
import LanguageSwitcher from "../components/LanguageSwitcher.jsx";
import { customerFields } from "../fields.js";
import { post } from "../api/client";
import { useI18n } from "../useI18n";

// Optional self-registration for residents (the admin can also register them)
export default function SelfRegister() {
  const { t } = useI18n();
  return (
    <div className="login" style={{ maxWidth: 560 }}>
      <div className="row" style={{ justifyContent: "flex-end" }}><LanguageSwitcher /></div>
      <FormCard
        title={t("register_resident_title")}
        hint={t("register_resident_hint")}
        fields={customerFields}
        withLocation
        submitLabel={t("register_submit")}
        onSubmit={async (v) => {
          await post("/auth/register", v);
          return t("registered_success");
        }}
      />
      <p className="muted"><Link to="/login">{t("back_to_login")}</Link></p>
    </div>
  );
}
