import axios from "axios";
import axiosRetry from "axios-retry";
import { config } from "./config.js";

export const core = axios.create({
  baseURL: config.coreUrl,
  headers: { "X-Publisher-Token": config.publisherToken },
});

axiosRetry(core, { retries: 5, retryCondition: () => true });

export async function findCustomerByEmail(email) {
  const res = await core.get("/customers?email=" + email);
  return res.data.items[0];
}

export async function getEntitlements(customerId) {
  const res = await core.get(`/entitlements?customerId=${customerId}`);
  return res.data.items;
}
