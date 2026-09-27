// src/api/payments.js
// The HarakaPay API key is NEVER here - it lives only on the backend.
import { get, post } from "./client";

// Sends the USSD push to the customer's phone. The amount is decided by the server.
export const collectPayment = (customerId, billingPeriod) =>
  post("/payments/collect", { customer_id: customerId, billing_period: billingPeriod });

// "pending" | "completed" | "failed" | "needs_review"
export const getPaymentStatus = (orderId) => get(`/payments/${encodeURIComponent(orderId)}`);
