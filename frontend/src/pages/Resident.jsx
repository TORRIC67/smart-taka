import { useEffect, useState } from "react";
import Layout from "../components/Layout.jsx";
import MakePaymentButton from "../components/MakePaymentButton.jsx";
import { useAuth } from "../auth.jsx";
import { downloadFile, get, post } from "../api/client";
import { useI18n } from "../useI18n";

export default function Resident() {
  const { user, refresh } = useAuth();
  const { t } = useI18n();
  const customer = user.customer;
  const [rating, setRating] = useState(5);
  const [message, setMessage] = useState("");
  const [msg, setMsg] = useState(null);
  const [payments, setPayments] = useState([]);
  const [receiptBusy, setReceiptBusy] = useState(null); // order_id currently downloading

  useEffect(() => {
    if (customer) get("/payments/mine").then(setPayments).catch(() => {});
  }, [customer]);

  async function downloadReceipt(orderId) {
    setReceiptBusy(orderId);
    try {
      await downloadFile(`/payments/${orderId}/receipt`, `receipt-${orderId}.pdf`);
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setReceiptBusy(null);
    }
  }

  const STATUS_TEXT = { registered: t("status_registered"), billed: t("status_billed"), paid: t("status_paid") };
  const STATUS_BADGE = { registered: t("status_badge_registered"), billed: t("status_badge_billed"), paid: t("status_badge_paid") };

  async function sendComplaint(e) {
    e.preventDefault();
    try {
      await post("/complaints", { rating: Number(rating), message });
      setMsg({ ok: true, text: t("complaint_thanks") });
      setMessage("");
    } catch (err) {
      setMsg({ ok: false, text: err.message });
    }
  }

  if (!customer) return <Layout><p>{t("no_customer_profile")}</p></Layout>;

  return (
    <Layout>
      <div className="card">
        <h2>{t("welcome", { name: user.full_name })}</h2>
        <p className="muted">{customer.ward}{customer.address ? `, ${customer.address}` : ""}</p>
        <p>
          <span className={`badge ${customer.payment_status}`}>{STATUS_BADGE[customer.payment_status]}</span>{" "}
          {STATUS_TEXT[customer.payment_status]}
        </p>
        <p>{t("monthly_fee_label")} <strong>TZS {Number(user.monthly_fee_tzs).toLocaleString()}</strong></p>
        {/* After payment completes we reload the profile so the status changes to "paid" */}
        <MakePaymentButton
          customerId={customer.id}
          alreadyPaid={customer.payment_status === "paid"}
          onPaid={() => { refresh(); get("/payments/mine").then(setPayments).catch(() => {}); }}
        />
      </div>

      <div className="card">
        <h3>{t("payment_history_title")}</h3>
        {payments.length === 0 && <p className="muted">{t("no_payments_yet")}</p>}
        {payments.length > 0 && (
          <table>
            <thead>
              <tr><th>{t("th_period")}</th><th>{t("th_amount")}</th><th>{t("th_status")}</th><th></th></tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.order_id}>
                  <td>{p.billing_period}</td>
                  <td>TZS {Number(p.amount).toLocaleString()}</td>
                  <td><span className={`badge ${p.status === "completed" ? "paid" : ""}`}>{p.status}</span></td>
                  <td>
                    {p.status === "completed" && (
                      <button type="button" className="btn ghost" disabled={receiptBusy === p.order_id} onClick={() => downloadReceipt(p.order_id)}>
                        {receiptBusy === p.order_id ? t("saving") : t("download_receipt_btn")}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <form className="card form" onSubmit={sendComplaint}>
        <h3>{t("complaint_title")}</h3>
        <label>{t("service_rating_label")}
          <select value={rating} onChange={(e) => setRating(e.target.value)}>
            {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} / 5</option>)}
          </select>
        </label>
        <label>{t("message_label")}
          <textarea rows={3} value={message} onChange={(e) => setMessage(e.target.value)} required />
        </label>
        <button className="btn">{t("send")}</button>
        {msg && <p className={msg.ok ? "ok" : "err"} style={{ margin: 0 }}>{msg.text}</p>}
      </form>
    </Layout>
  );
}
