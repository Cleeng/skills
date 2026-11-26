type Tokens = { jwt: string; refreshToken: string };

const BASE = import.meta.env.VITE_MEDIASTORE_URL; // per-build value, production in .env.production
let inflight: Promise<Tokens> | null = null;

function load(): Tokens | null {
  const raw = localStorage.getItem("cleeng_tokens");
  return raw ? JSON.parse(raw) : null;
}

function save(tokens: Tokens | null) {
  if (tokens) localStorage.setItem("cleeng_tokens", JSON.stringify(tokens));
  else localStorage.removeItem("cleeng_tokens");
}

function expiresSoon(jwt: string): boolean {
  const { exp } = JSON.parse(atob(jwt.split(".")[1]));
  return exp * 1000 - Date.now() < 60_000;
}

async function doRefresh(refreshToken: string): Promise<Tokens> {
  const res = await fetch(`${BASE}/auths/refresh_token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshToken }),
    signal: AbortSignal.timeout(8000),
  });
  if (res.status === 401) {
    if (load()?.refreshToken === refreshToken) save(null); // only clear tokens nobody has replaced
    throw new Error("signed-out");
  }
  if (!res.ok) throw new Error(`refresh failed: ${res.status}`);
  const { jwt, refreshToken: next } = (await res.json()).responseData;
  const tokens = { jwt, refreshToken: next };
  save(tokens);
  return tokens;
}

// One refresh at a time across tabs (Web Locks) and within a tab (shared promise).
export async function currentJwt(): Promise<string | null> {
  const tokens = load();
  if (!tokens) return null;
  if (!expiresSoon(tokens.jwt)) return tokens.jwt;
  inflight ??= navigator.locks
    .request("cleeng-refresh", async () => {
      const latest = load();
      if (!latest) throw new Error("signed-out");
      return expiresSoon(latest.jwt) ? doRefresh(latest.refreshToken) : latest; // another tab may have refreshed
    })
    .finally(() => {
      inflight = null;
    });
  return (await inflight).jwt;
}

export function signOut() {
  save(null);
}
