import { useEffect, useState } from "react";
import { get } from "../../api/client";
import { useI18n } from "../../useI18n";

export default function Complaints() {
  const { t } = useI18n();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    get("/complaints").then(setRows).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="err">{error}</p>;
  if (!rows) return <p>{t("loading")}</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{t("th_date")}</th><th>{t("th_customer")}</th><th>{t("th_ward")}</th>
            <th>{t("th_rating")}</th><th>{t("th_message")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id}>
              <td>{new Date(c.created_at).toLocaleString()}</td>
              <td>{c.customer_name}</td>
              <td>{c.ward}</td>
              <td>{c.rating} / 5</td>
              <td>{c.message}</td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={5} className="muted">{t("no_complaints")}</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
