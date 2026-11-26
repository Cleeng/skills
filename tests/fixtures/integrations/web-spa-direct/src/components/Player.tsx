import { useEffect, useState } from "react";
import { getEntitlement, getSubscriptions } from "../api/mediastore";

const OFFER_ID = import.meta.env.VITE_OFFER_ID;

export default function Player() {
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    getSubscriptions(localStorage.getItem("cleeng_customer")!).then((subs) => {
      const sub = subs.find((s) => s.offerId === OFFER_ID);
      setAllowed(Boolean(sub) && sub.expiresAt * 1000 > Date.now());
    });

    const timer = setInterval(async () => {
      const ent = await getEntitlement(OFFER_ID);
      setAllowed(ent.accessGranted);
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  return allowed ? <video src="/stream.m3u8" controls autoPlay /> : <p>Subscribe to watch</p>;
}
