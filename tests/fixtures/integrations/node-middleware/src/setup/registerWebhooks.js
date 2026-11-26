import { core } from "../cleeng.js";

const RECEIVER = "https://api.acme.example/webhooks/cleeng";

export async function registerWebhooks() {
  for (const topic of ["subscriptionRenewed", "subscriptionReadyForTermination"]) {
    await core.put(`/webhook_subscriptions/${topic}`, [{ url: RECEIVER }]);
  }
}
