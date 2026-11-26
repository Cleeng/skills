const CORE_URL = import.meta.env.VITE_CORE_URL;

// Used by the player to double-check access for the current viewer.
export async function getCoreEntitlements(customerId: number) {
  const res = await fetch(`${CORE_URL}/entitlements?customerId=${customerId}`, {
    headers: { "X-Publisher-Token": import.meta.env.VITE_CLEENG_PUBLISHER_TOKEN },
  });
  return (await res.json()).items;
}
