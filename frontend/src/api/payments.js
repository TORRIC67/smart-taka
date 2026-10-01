// src/api/payments.js
// The HarakaPay API key is NEVER here - it lives only on the backend.
import { get, post } from "./client";

// Sends the USSD push to the customer's phone. The amount is decided by the server.
// altPhone: pay from a DIFFERENT phone just this once (doesn't change the account's phone).
export const collectPayment = (customerId, billingPeriod, altPhone) =>
  post("/payments/collect", { customer_id: customerId, billing_period: billingPeriod, phone: altPhone || undefined });

export const topUpWallet = (customerId, amount) => post("/payments/wallet/topup", { customer_id: customerId, amount });
export const payBillFromWallet = (customerId, billingPeriod) =>
  post("/payments/wallet/pay-bill", { customer_id: customerId, billing_period: billingPeriod });
export const getWallet = () => get("/payments/wallet");

// "pending" | "completed" | "failed" | "needs_review"
export const getPaymentStatus = (orderId) => get(`/payments/${encodeURIComponent(orderId)}`);
