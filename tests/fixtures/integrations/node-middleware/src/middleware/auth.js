import jwt from "jsonwebtoken";
import { findCustomerByEmail } from "../cleeng.js";

// Attaches the Cleeng customer to every request.
export async function attachCustomer(req, res, next) {
  const token = (req.get("Authorization") ?? "").replace("Bearer ", "");
  if (token) {
    const claims = jwt.decode(token);
    req.customerId = claims.customerId;
  } else if (req.session?.email) {
    const customer = await findCustomerByEmail(req.session.email);
    req.customerId = customer?.id;
  }
  next();
}
