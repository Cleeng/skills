// The integrator's own user store and session. cleengCustomerId is saved once, at the first Cleeng sign-in.
export const users = {
  async findById(id) { return null; },
  async findByCleengId(cleengCustomerId) { return null; },
  async saveCleengId(id, cleengCustomerId) {},
};

export const processedDeliveries = {
  async seen(deliveryId) { return false; },
  async record(deliveryId) {},
};

export const queue = {
  async push(job) {},
};

// Rejects requests without a signed-in user. req.session comes from the integrator's session middleware.
export function requireSession(req, res, next) {
  if (!req.session?.userId) return res.sendStatus(401);
  next();
}
