import crypto from "node:crypto";
import express, { Router } from "express";
import { config } from "../config.js";
import { db } from "../db.js";

export const webhooks = Router();

webhooks.post("/webhooks/cleeng", express.json(), async (req, res) => {
  const signature = req.get("X-Webhook-Signature");
  const expected = crypto
    .createHmac("sha256", config.webhookSecret)
    .update(JSON.stringify(req.body))
    .digest("base64");
  if (signature !== expected) return res.status(401).end();

  const { topic, data } = req.body;
  const user = await db.users.findByCleengId(data.customerId);
  if (!user) return res.status(404).json({ error: "unknown customer" });

  if (topic === "subscriptionRenewed") {
    await db.users.extendAccess(user.id, 30);
    await db.emails.sendRenewalReceipt(user.email);
  }
  if (topic === "subscriptionReadyForTermination") {
    await db.users.revokeAccess(user.id);
  }
  res.status(200).end();
});
