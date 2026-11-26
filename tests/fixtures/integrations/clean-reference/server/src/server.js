import crypto from "node:crypto";
import axios from "axios";
import express from "express";
import { createRemoteJWKSet, jwtVerify } from "jose";
import { getEntitlements, dropEntitlements } from "./cleeng.js";
import { users, processedDeliveries, queue, requireSession } from "./users.js";

const app = express();
app.set("trust proxy", 1);
const jwks = createRemoteJWKSet(new URL(process.env.CLEENG_JWKS_URL)); // identity.api.prod.cleeng.com in production
const mediastoreUrl = process.env.CLEENG_MEDIASTORE_URL;

// Webhooks: raw body, verified before parsing, de-duplicated, processed from a queue.
app.post("/webhooks/cleeng", express.raw({ type: "application/json" }), async (req, res) => {
  const expected = crypto.createHmac("sha256", process.env.CLEENG_WEBHOOK_SECRET).update(req.body).digest("base64");
  const given = req.get("X-Webhook-Signature") ?? "";
  if (given.length !== expected.length || !crypto.timingSafeEqual(Buffer.from(given), Buffer.from(expected))) {
    return res.sendStatus(401);
  }
  const deliveryId = req.get("X-Webhook-Delivery-Id");
  if (await processedDeliveries.seen(deliveryId)) return res.sendStatus(200);
  try {
    await queue.push({ deliveryId, event: JSON.parse(req.body) });
    await processedDeliveries.record(deliveryId);
    res.sendStatus(200);
  } catch {
    res.sendStatus(503); // transient: Cleeng retries 5xx
  }
});

app.use(express.json());

// Cleeng sign-in for a user the identity provider has signed in. The Cleeng customer id is stored once.
app.post("/sso/login", requireSession, async (req, res) => {
  const user = await users.findById(req.session.userId);
  const { data } = await axios.post(
    `${mediastoreUrl}/sso/auths`,
    { email: user.email, customerIP: req.ip },
    { headers: { "X-Publisher-Token": process.env.CLEENG_PUBLISHER_TOKEN }, timeout: 8000 },
  );
  if (!user.cleengCustomerId) {
    const { payload } = await jwtVerify(data.responseData.jwt, jwks, { algorithms: ["RS256"] });
    await users.saveCleengId(user.id, payload.customerId);
  }
  res.json({ jwt: data.responseData.jwt, refreshToken: data.responseData.refreshToken });
});

// Playback start: verified JWT, fresh entitlement check.
app.get("/playback/:offerId", async (req, res) => {
  const token = (req.get("Authorization") ?? "").replace("Bearer ", "");
  const { payload } = await jwtVerify(token, jwks, { algorithms: ["RS256"] });
  const items = await getEntitlements(payload.customerId, { fresh: true });
  const entitlement = items.find((e) => e.offerId === req.params.offerId);
  res.json({ allowed: entitlement?.accessGranted === true });
});

export async function handleEvent({ event }) {
  const user = await users.findByCleengId(event.data.customerId);
  if (!user) return;
  if (["subscriptionCreated", "subscriptionRenewed", "subscriptionTerminated", "subscriptionSwitched", "passCreated", "passTerminated"].includes(event.topic)) {
    dropEntitlements(event.data.customerId);
  }
}

app.listen(process.env.PORT ?? 3000);
