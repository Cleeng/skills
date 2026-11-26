const BASE = import.meta.env.VITE_MEDIASTORE_URL;

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem("cleeng_jwt")}` };
}

export async function signIn(email: string, password: string) {
  const res = await fetch(`${BASE}/auths`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, offerId: import.meta.env.VITE_OFFER_ID }),
  });
  const { responseData } = await res.json();
  localStorage.setItem("cleeng_jwt", responseData.jwt);
  localStorage.setItem("cleeng_refresh", responseData.refreshToken);
  localStorage.setItem("cleeng_customer", String(responseData.customerId));
  return responseData;
}

export async function refreshJwt() {
  const res = await fetch(`${BASE}/auths/refresh_token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshToken: localStorage.getItem("cleeng_refresh") }),
  });
  const { responseData } = await res.json();
  localStorage.setItem("cleeng_jwt", responseData.jwt);
  return responseData.jwt;
}

export async function getSubscriptions(customerId: string) {
  const res = await fetch(`${BASE}/customers/${customerId}/subscriptions`, { headers: authHeaders() });
  return (await res.json()).responseData.items;
}

export async function getEntitlement(offerId: string) {
  const res = await fetch(`${BASE}/entitlements/${offerId}`, { headers: authHeaders() });
  return (await res.json()).responseData;
}
