import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import FormCard from "../components/FormCard.jsx";
import LanguageSwitcher from "../components/LanguageSwitcher.jsx";
import { customerFields } from "../fields.js";
import { get, post } from "../api/client";
import { useI18n } from "../useI18n";

// Optional self-registration for residents (the admin can also register them).
// Needs a zone (Service Provider) picked from the public list - no login required to see it.
export default function SelfRegister() {
  const { t } = useI18n();
  const [providers, setProviders] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    get("/providers").then(setProviders).catch((e) => setError(e.message));
  }, []);

  const fields = [
    ...customerFields,
    {
      name: "provider_id", labelKey: "field_zone", type: "select", numeric: true, required: true,
      placeholder: t("field_zone_placeholder"),
      options: providers.map((p) => ({ value: p.id, label: p.name })),
    },
  ];

  return (
    <div className="login" style={{ maxWidth: 560 }}>
      <div className="row" style={{ justifyContent: "flex-end" }}><LanguageSwitcher /></div>
      {error && <p className="err">{error}</p>}
      <FormCard
        title={t("register_resident_title")}
        hint={t("register_resident_hint")}
        fields={fields}
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
