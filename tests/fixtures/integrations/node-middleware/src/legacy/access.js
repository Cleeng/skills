import axios from "axios";

// Still used by the old TV apps.
export async function hasAccess(customerToken, offerId) {
  const { data } = await axios.post("https://api.cleeng.com/3.0/json-rpc", {
    jsonrpc: "2.0",
    id: 1,
    method: "getAccessStatus",
    params: { customerToken, offerId },
  });
  return data.result.accessGranted;
}
