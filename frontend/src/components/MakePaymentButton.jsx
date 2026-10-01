// src/components/MakePaymentButton.jsx
//
// One button that runs the whole payment flow for a customer:
//   click -> USSD push sent -> "check your phone" -> we poll our backend -> paid
//
// Works in two places with no changes:
//   - Admin's Residents table  (admin pays/triggers for any customer)
//   - Resident's own dashboard (backend only allows a resident to pay for themselves)
//
// Props:
//   customerId  number   which customer this payment is for
//   alreadyPaid boolean  true if the table row already says "paid"
//   onPaid      function called once when payment completes (use it to refresh the table/map)

import { useEffect, useRef, useState } from "react";
import { collectPayment, getPaymentStatus } from "../api/payments";
import { useI18n } from "../useI18n";

const POLL_MS = 4000; // ask the backend every 4 seconds
const MAX_POLLS = 45; // 45 x 4s = about 3 minutes, then we stop and show "check again"

const green = "#16a34a";
const styles = {
  wrap: { display: "inline-flex", flexDirection: "column", gap: 4, alignItems: "flex-start" },
  btn: {
    background: green, color: "#fff", border: "none", borderRadius: 6,
    padding: "6px 14px", fontSize: 14, cursor: "pointer",
  },
  btnOff: { opacity: 0.6, cursor: "default" },
  badge: { color: green, fontWeight: 600, fontSize: 14 },
  note: { fontSize: 13, color: "#374151", maxWidth: 260 },
  noteBad: { fontSize: 13, color: "#b91c1c", maxWidth: 260 },
};

export default function MakePaymentButton({ customerId, alreadyPaid = false, onPaid }) {
  const { t } = useI18n();
  // idle | sending | waiting | paid | failed | review | timeout | error
  const [state, setState] = useState(alreadyPaid ? "paid" : "idle");
  const [error, setError] = useState("");
  const [altPhone, setAltPhone] = useState("");
  const [showAltPhone, setShowAltPhone] = useState(false);
  const orderRef = useRef(null); // HarakaPay order_id of the payment we are waiting for
  const timerRef = useRef(null);
  const aliveRef = useRef(true); // false after unmount, so we don't update a dead component

  useEffect(() => {
    aliveRef.current = true;
    return () => {
      aliveRef.current = false;
      clearTimeout(timerRef.current); // stop polling when the row disappears
    };
  }, []);

  // Ask the backend for the payment status every few seconds until it is final.
  function poll(attempt = 1) {
    timerRef.current = setTimeout(async () => {
      try {
        const p = await getPaymentStatus(orderRef.current);
        if (!aliveRef.current) return;
        if (p.status === "completed") { setState("paid"); onPaid?.(p); return; }
        if (p.status === "failed") { setState("failed"); return; }
        if (p.status === "needs_review") { setState("review"); return; }
        // "pending" -> keep waiting
      } catch {
        // network hiccup: ignore and try again on the next tick
      }
      if (!aliveRef.current) return;
      if (attempt >= MAX_POLLS) { setState("timeout"); return; }
      poll(attempt + 1);
    }, POLL_MS);
  }

  async function handlePay() {
    setState("sending");
    setError("");
    try {
      const payment = await collectPayment(customerId, undefined, showAltPhone ? altPhone : undefined);
      if (!aliveRef.current) return;
      orderRef.current = payment.order_id;
      setState("waiting");
      poll();
    } catch (e) {
      if (!aliveRef.current) return;
      if (e.status === 409) { setState("paid"); onPaid?.(); return; } // already paid this month
      setError(e.message);
      setState("error");
    }
  }

  function handleRecheck() {
    setState("waiting");
    poll();
  }

  return (
    <span style={styles.wrap}>
      {state === "idle" && (
        <>
          {!showAltPhone ? (
            <button type="button" style={{ ...styles.note, background: "none", border: "none", padding: 0, textDecoration: "underline", cursor: "pointer" }} onClick={() => setShowAltPhone(true)}>
              {t("pay_different_phone_link")}
            </button>
          ) : (
            <input type="tel" placeholder="0712345678" value={altPhone} onChange={(e) => setAltPhone(e.target.value)} style={{ width: 140, fontSize: 13 }} />
          )}
        </>
      )}
      {(state === "idle" || state === "failed" || state === "error") && (
        <button style={styles.btn} onClick={handlePay}>
          {state === "idle" ? t("pay_button") : t("pay_retry")}
        </button>
      )}
      {state === "sending" && (
        <button style={{ ...styles.btn, ...styles.btnOff }} disabled>{t("pay_sending")}</button>
      )}
      {state === "waiting" && <span style={styles.note}>{t("pay_waiting")}</span>}
      {state === "paid" && <span style={styles.badge}>{t("pay_paid")}</span>}
      {state === "failed" && <span style={styles.noteBad}>{t("pay_failed")}</span>}
      {state === "error" && <span style={styles.noteBad}>{error}</span>}
      {state === "review" && <span style={styles.noteBad}>{t("pay_review")}</span>}
      {state === "timeout" && (
        <>
          <span style={styles.note}>{t("pay_timeout")}</span>
          <button style={styles.btn} onClick={handleRecheck}>{t("pay_recheck")}</button>
        </>
      )}
    </span>
  );
}
