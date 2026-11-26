import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { signIn } from "./api/mediastore";
import Home from "./pages/Home";
import Account from "./pages/Account";
import Player from "./components/Player";

export default function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Keep the viewer signed in across reloads.
    const saved = localStorage.getItem("acme_credentials");
    if (saved) {
      const { email, password } = JSON.parse(saved);
      signIn(email, password).finally(() => setReady(true));
    } else {
      setReady(true);
    }
  }, []);

  if (!ready) return null;
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/account" element={<Account />} />
        <Route path="/watch/:id" element={<Player />} />
      </Routes>
    </BrowserRouter>
  );
}
