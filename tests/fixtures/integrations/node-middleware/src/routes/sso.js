import axios from "axios";
import { Router } from "express";
import { config } from "../config.js";

export const sso = Router();

// Called by the apps after the identity provider confirms the user.
sso.post("/sso/login", async (req, res) => {
  const { data } = await axios.post(
    `${config.mediastoreUrl}/sso/auths`,
    { email: req.body.email },
    { headers: { "X-Publisher-Token": config.publisherToken } },
  );
  res.json({ jwt: data.responseData.jwt, refreshToken: data.responseData.refreshToken });
});
