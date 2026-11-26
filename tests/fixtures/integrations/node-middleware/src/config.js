export const config = {
  port: process.env.PORT ?? 3000,
  coreUrl: "https://api.cleeng.com/3.1",
  mediastoreUrl: "https://mediastoreapi.cleeng.com",
  publisherToken: "Ab3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5bC7dE9fG1hJ3",
  webhookSecret: process.env.CLEENG_WEBHOOK_SECRET,
};
