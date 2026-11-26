import { useEffect, useState } from "react";
import { getSubscriptions } from "../api/mediastore";

export default function Home() {
  const [subs, setSubs] = useState<any[]>([]);
  useEffect(() => {
    getSubscriptions(localStorage.getItem("cleeng_customer")!).then(setSubs);
  }, []);
  return <main>{subs.length ? <p>Welcome back</p> : <a href="/plans">See plans</a>}</main>;
}
