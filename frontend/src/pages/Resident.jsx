import { useEffect, useRef, useState } from "react";
import Layout from "../components/Layout.jsx";
import MakePaymentButton from "../components/MakePaymentButton.jsx";
import { useAuth } from "../auth.jsx";
import { downloadFile, get, post } from "../api/client";
import { getPaymentStatus, getWallet, payBillFromWallet, topUpWallet } from "../api/payments";
import { useI18n } from "../useI18n";

// Top-up has its own small USSD-wait flow, same idea as MakePaymentButton but for an
// amount the customer chooses themselves instead of the fixed monthly fee.
function WalletTopup({ customerId, onDone }) {
  const { t } = useI18n();
  const [amount, setAmount] = useState("");
  const [state, setState] = useState("idle"); // idle | sending | waiting | done | error
  const [error, setError] = useState("");
  const aliveRef = useRef(true);
  useEffect(() => () => { aliveRef.current = false; }, []);

  function poll(orderId, attempt = 1) {
    setTimeout(async () => {
      if (!aliveRef.current) return;
      try {
        const p = await getPaymentStatus(orderId);
        if (p.status === "completed") { setState("done"); onDone(); return; }
        if (p.status === "failed") { setState("error"); setError(t("pay_failed")); return; }
      } catch { /* keep trying */ }
      if (attempt >= 45) { setState("error"); setError(t("pay_timeout")); return; }
      poll(orderId, attempt + 1);
    }, 4000);
  }

  async function submit(e) {
    e.preventDefault();
    setState("sending");
    setError("");
    try {
      const payment = await topUpWallet(customerId, Number(amount));
      setState("waiting");
      poll(payment.order_id);
    } catch (err) {
      setState("error");
      setError(err.message);
    }
  }

  if (state === "waiting" || state === "sending") return <p className="muted">{t("pay_waiting")}</p>;
  return (
    <form className="row" onSubmit={submit} style={{ alignItems: "center" }}>
      <input type="number" min={1000} step={500} placeholder={t("topup_amount_placeholder")} value={amount} onChange={(e) => setAmount(e.target.value)} required style={{ width: 160 }} />
      <button className="btn">{t("topup_submit_btn")}</button>
      {error && <span className="err">{error}</span>}
    </form>
  );
}

export default function Resident() {
  const { user, refresh } = useAuth();
  const { t } = useI18n();
  const customer = user.customer;
  const [rating, setRating] = useState(5);
  const [message, setMessage] = useState("");
  const [msg, setMsg] = useState(null);
  const [payments, setPayments] = useState([]);
  const [receiptBusy, setReceiptBusy] = useState(null); // order_id currently downloading
  const [wallet, setWallet] = useState(null);
  const [payFromWalletBusy, setPayFromWalletBusy] = useState(false);

  const reloadPayments = () => get("/payments/mine").then(setPayments).catch(() => {});
  const reloadWallet = () => getWallet().then((w) => setWallet(w.wallet_balance_tzs)).catch(() => {});

  useEffect(() => {
    if (customer) { reloadPayments(); reloadWallet(); }
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

  async function payFromWallet() {
    setPayFromWalletBusy(true);
    setMsg(null);
    try {
      await payBillFromWallet(customer.id);
      await Promise.all([refresh(), reloadPayments(), reloadWallet()]);
      setMsg({ ok: true, text: t("paid_from_wallet_success") });
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setPayFromWalletBusy(false);
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
  const canPayFromWallet = customer.payment_status !== "paid" && wallet !== null && wallet >= user.monthly_fee_tzs;

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
        <div className="row" style={{ alignItems: "center" }}>
          <MakePaymentButton
            customerId={customer.id}
            alreadyPaid={customer.payment_status === "paid"}
            onPaid={() => { refresh(); reloadPayments(); }}
          />
          {canPayFromWallet && (
            <button className="btn ghost" disabled={payFromWalletBusy} onClick={payFromWallet}>
              {payFromWalletBusy ? t("saving") : t("pay_from_wallet_btn")}
            </button>
          )}
        </div>
        {msg && <p className={msg.ok ? "ok" : "err"}>{msg.text}</p>}
      </div>

      <div className="card">
        <h3>{t("wallet_title")}</h3>
        <p><b>TZS {Number(wallet ?? 0).toLocaleString()}</b> <span className="muted">{t("wallet_balance_label")}</span></p>
        <WalletTopup customerId={customer.id} onDone={reloadWallet} />
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
                  <td>{p.billing_period === "WALLET" ? t("wallet_topup_label") : p.billing_period}</td>
                  <td>TZS {Number(p.amount).toLocaleString()}</td>
                  <td><span className={`badge ${p.status === "completed" ? "paid" : ""}`}>{p.status}</span></td>
                  <td>
                    {p.status === "completed" && p.billing_period !== "WALLET" && (
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
      </form>
    </Layout>
  );
}
