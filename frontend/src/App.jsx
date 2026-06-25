import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <div className="app">
      <h1>Technosprint 2026</h1>
      <p>Backend: {status}</p>
    </div>
  );
}

export default App;
