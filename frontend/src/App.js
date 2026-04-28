import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

const API = "/api";
axios.defaults.timeout = 15000;

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/* ── 5-petal flower loader ── */
function Loader() {
  return (
    <div className="loader-backdrop">
      <div className="loader-box">
        <div className="flower">
          {[0, 1, 2, 3, 4].map(i => (
            <span key={i} className="petal" style={{ "--n": i }} />
          ))}
          <span className="flower-core" />
        </div>
        <p className="loader-label">Analyzing...</p>
      </div>
    </div>
  );
}

/* ── Confidence bar ── */
function Confidence({ value, label }) {
  const good = label === "REAL";
  const tier = value >= 80 ? "High" : value >= 55 ? "Moderate" : "Low";
  return (
    <div className="conf">
      <div className="conf-row">
        <span className="conf-title">Confidence</span>
        <span className={`conf-num ${good ? "num-green" : "num-red"}`}>{value}%</span>
      </div>
      <div className="conf-rail">
        <div
          className={`conf-bar ${good ? "bar-green" : "bar-red"}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="conf-tier">{tier} confidence</span>
    </div>
  );
}

/* ── Theme toggle icon ── */
function ThemeIcon({ dark }) {
  return dark ? (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  ) : (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  );
}

export default function App() {
  const [dark, setDark] = useState(true);
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [histLoading, setHistLoading] = useState(false);
  const areaRef = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }, [dark]);

  const loadHistory = async () => {
    setHistLoading(true);
    try { const r = await axios.get(`${API}/history?limit=30`); setHistory(r.data); }
    catch { } finally { setHistLoading(false); }
  };

  useEffect(() => { loadHistory(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const r = await axios.post(`${API}/predict`, { text });
      setResult(r.data);
      loadHistory();
    } catch (err) {
      setError(err.response?.data?.error || "Could not reach the backend. Make sure it is running.");
    } finally { setLoading(false); }
  };

  const pickHistory = (item) => {
    setText(item.text);
    setResult({ label: item.label, confidence: item.confidence });
    setDrawerOpen(false);
    areaRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const removeItem = async (e, id) => {
    e.stopPropagation();
    await axios.delete(`${API}/history/${id}`);
    setHistory(h => h.filter(x => x.id !== id));
  };

  const clearAll = async () => {
    await axios.delete(`${API}/history`);
    setHistory([]);
  };

  return (
    <div className="app">

      {/* NAV */}
      <nav className="nav">
        <div className="nav-inner">
          <div className="brand">
            <div className="brand-dot" />
            <span className="brand-name">Fake<strong>Lens</strong></span>
          </div>

          <span className="nav-tag">Multilingual Fake News Detector</span>

          <div className="nav-actions">
            <button className="icon-btn" onClick={() => { setDrawerOpen(true); loadHistory(); }} title="History">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15.5 15.5"/>
              </svg>
              {history.length > 0 && <span className="nav-badge">{history.length}</span>}
            </button>
            <button className="icon-btn" onClick={() => setDark(d => !d)} title="Toggle theme">
              <ThemeIcon dark={dark} />
            </button>
          </div>
        </div>
      </nav>

      {/* MAIN */}
      <main className="main">

        {/* Search card */}
        <section className="panel">
          <h1 className="panel-title">Check News Authenticity</h1>
          <p className="panel-sub">Paste any news in Hindi · Telugu · Marathi · Gujarati</p>

          <form onSubmit={submit} className="form">
            <div className="field-wrap">
              <textarea
                ref={areaRef}
                className="field"
                rows={6}
                placeholder="Paste your news article or headline here..."
                value={text}
                onChange={e => setText(e.target.value)}
              />
              {text && (
                <button type="button" className="field-x"
                  onClick={() => { setText(""); setResult(null); setError(""); }}>
                  <svg width="9" height="9" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                    <line x1="1" y1="1" x2="9" y2="9"/><line x1="9" y1="1" x2="1" y2="9"/>
                  </svg>
                </button>
              )}
            </div>
            <p className="char-hint">{text.length} characters</p>

            <button type="submit" className={`analyze-btn${loading ? " busy" : ""}`}
              disabled={loading || !text.trim()}>
              {loading
                ? <><span className="spin3" />&nbsp; Analyzing...</>
                : <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                    </svg>
                    &nbsp; Analyze News
                  </>
              }
            </button>
          </form>

          {error && (
            <div className="err-bar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="13"/><circle cx="12" cy="17" r=".5" fill="currentColor"/>
              </svg>
              {error}
            </div>
          )}

          {/* Result */}
          {result && !loading && (
            <div className={`result-wrap ${result.label === "REAL" ? "rw-real" : "rw-fake"}`}>
              {/* verdict row */}
              <div className="verdict-row">
                <div className={`verdict-icon ${result.label === "REAL" ? "vi-real" : "vi-fake"}`}>
                  {result.label === "REAL"
                    ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    : <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  }
                </div>
                <div className="verdict-text">
                  <span className={`verdict-label ${result.label === "REAL" ? "vl-real" : "vl-fake"}`}>
                    {result.label === "REAL" ? "Real News" : "Fake News"}
                  </span>
                  <span className="verdict-desc">
                    {result.label === "REAL"
                      ? "This article appears to be authentic."
                      : "This article appears to be misleading or fabricated."}
                  </span>
                </div>
              </div>

              {/* confidence */}
              {result.confidence != null && (
                <Confidence value={result.confidence} label={result.label} />
              )}
            </div>
          )}
        </section>

        {/* Recent history */}
        {history.length > 0 && (
          <section className="panel hist-panel">
            <div className="hist-head">
              <span className="hist-head-title">Recent Searches</span>
              <button className="ghost-btn" onClick={clearAll}>Clear all</button>
            </div>
            <div className="hist-list">
              {history.slice(0, 5).map(item => (
                <HistRow key={item.id} item={item}
                  onClick={() => pickHistory(item)}
                  onDel={e => removeItem(e, item.id)} />
              ))}
            </div>
          </section>
        )}
      </main>

      {/* DRAWER */}
      <div className={`overlay${drawerOpen ? " on" : ""}`} onClick={() => setDrawerOpen(false)} />
      <aside className={`drawer${drawerOpen ? " on" : ""}`}>
        <div className="drawer-head">
          <span className="drawer-title">Search History</span>
          <button className="icon-btn" onClick={() => setDrawerOpen(false)}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="1" y1="1" x2="11" y2="11"/><line x1="11" y1="1" x2="1" y2="11"/>
            </svg>
          </button>
        </div>
        {history.length > 0 && (
          <button className="ghost-btn drawer-clear" onClick={clearAll}>Clear all</button>
        )}
        <div className="drawer-body">
          {histLoading
            ? <p className="drawer-empty">Loading...</p>
            : history.length === 0
            ? <p className="drawer-empty">No searches yet</p>
            : history.map(item => (
                <HistRow key={item.id} item={item}
                  onClick={() => pickHistory(item)}
                  onDel={e => removeItem(e, item.id)} />
              ))
          }
        </div>
      </aside>

      {loading && <Loader />}

      <footer className="foot">
        FakeLens &copy; {new Date().getFullYear()} &nbsp;&middot;&nbsp; AI-powered multilingual detection
      </footer>
    </div>
  );
}

function HistRow({ item, onClick, onDel }) {
  const real = item.label === "REAL";
  return (
    <div className={`hrow ${real ? "hrow-real" : "hrow-fake"}`} onClick={onClick}>
      <span className={`hrow-pip ${real ? "pip-real" : "pip-fake"}`} />
      <div className="hrow-body">
        <span className="hrow-text">
          {item.text.length > 78 ? item.text.slice(0, 78) + "…" : item.text}
        </span>
        <span className="hrow-meta">
          <span className={`hrow-tag ${real ? "tag-real" : "tag-fake"}`}>{item.label}</span>
          {item.confidence != null && <span className="hrow-conf">{item.confidence}%</span>}
          <span className="hrow-time">{timeAgo(item.timestamp)}</span>
        </span>
      </div>
      <button className="hrow-del" onClick={onDel}>
        <svg width="9" height="9" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
          <line x1="1" y1="1" x2="9" y2="9"/><line x1="9" y1="1" x2="1" y2="9"/>
        </svg>
      </button>
    </div>
  );
}
