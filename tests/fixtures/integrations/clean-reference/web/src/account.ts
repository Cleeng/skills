import { currentJwt } from "./session";

const BASE = import.meta.env.VITE_MEDIASTORE_URL;
let cached: { customerId: string; subscriptions: unknown[] } | null = null;

// Read once per session; reload after a purchase or on the account screen.
export async function subscriptions(customerId: string, { reload = false } = {}) {
  if (cached && cached.customerId === customerId && !reload) return cached.subscriptions;
  const res = await fetch(`${BASE}/customers/${customerId}/subscriptions`, {
    headers: { Authorization: `Bearer ${await currentJwt()}` },
    signal: AbortSignal.timeout(8000),
  });
  if (res.status === 429 && cached?.customerId === customerId) return cached.subscriptions; // rate limited: keep the cached list
  if (!res.ok) throw new Error(`subscriptions failed: ${res.status}`);
  cached = { customerId, subscriptions: (await res.json()).responseData.items };
  return cached.subscriptions;
}
