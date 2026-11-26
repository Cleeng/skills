import express from "express";
import { config } from "./config.js";
import { attachCustomer } from "./middleware/auth.js";
import { sso } from "./routes/sso.js";
import { webhooks } from "./routes/webhooks.js";
import { getEntitlements } from "./cleeng.js";

const app = express();
app.use(webhooks);
app.use(express.json());
app.use(attachCustomer);
app.use(sso);

app.get("/me/access", async (req, res) => {
  res.json(await getEntitlements(req.customerId));
});

app.listen(config.port);
