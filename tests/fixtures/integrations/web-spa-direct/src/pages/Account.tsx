import { useEffect, useState } from "react";
import { getSubscriptions } from "../api/mediastore";

export default function Account() {
  const [subs, setSubs] = useState<any[]>([]);
  useEffect(() => {
    getSubscriptions(localStorage.getItem("cleeng_customer")!).then(setSubs);
  }, []);
  return (
    <ul>
      {subs.map((s) => (
        <li key={s.offerId}>{s.offerTitle}, renews {new Date(s.expiresAt * 1000).toLocaleDateString()}</li>
      ))}
    </ul>
  );
}
