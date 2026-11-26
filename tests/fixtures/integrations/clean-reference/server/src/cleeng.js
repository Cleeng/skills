import axios from "axios";
import axiosRetry from "axios-retry";

const coreUrl = process.env.CLEENG_CORE_URL; // https://api.cleeng.com/3.1 in production
const publisherToken = process.env.CLEENG_PUBLISHER_TOKEN;

export const core = axios.create({
  baseURL: coreUrl,
  timeout: 8000,
  headers: { "X-Publisher-Token": publisherToken },
});

// One delayed retry, reads only, network errors and 5xx only.
axiosRetry(core, {
  retries: 1,
  retryDelay: () => 1000,
  retryCondition: (e) => e.config?.method === "get" && (!e.response || e.response.status >= 500),
});

const entitlementCache = new Map(); // key: customerId, value: { at, items }
const TTL_MS = 5 * 60 * 1000;

export async function getEntitlements(customerId, { fresh = false } = {}) {
  const hit = entitlementCache.get(customerId);
  if (!fresh && hit && Date.now() - hit.at < TTL_MS) return hit.items;
  const res = await core.get("/entitlements", { params: { customerId } });
  entitlementCache.set(customerId, { at: Date.now(), items: res.data.items });
  return res.data.items;
}

export function dropEntitlements(customerId) {
  entitlementCache.delete(customerId);
}
