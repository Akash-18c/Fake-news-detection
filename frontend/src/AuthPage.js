import React, { useState } from "react";
import axios from "axios";
import "./AuthPage.css";

/* ── 5-petal flower (reused on auth page too) ── */
function FlowerLoader() {
  return (
    <div className="fl-overlay">
      <div className="fl-box">
        <div className="fl-flower">
          {[0,1,2,3,4].map(i => (
            <span key={i} className="fl-petal" style={{"--n": i}} />
          ))}
          <span className="fl-core" />
        </div>
        <p className="fl-label">Please wait...</p>
      </div>
    </div>
  );
}

/* ── Eye icon ── */
function EyeIcon({ open }) {
  return open ? (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  ) : (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  );
}

export default function AuthPage({ onAuth }) {
  const [mode, setMode]       = useState("login");
  const [form, setForm]       = useState({ name: "", email: "", password: "" });
  const [showPass, setShowPass] = useState(false);
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const switchMode = (m) => {
    setMode(m);
    setError("");
    setShowPass(false);
    setForm({ name: "", email: "", password: "" });
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const url = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const payload = mode === "login"
        ? { email: form.email, password: form.password }
        : { name: form.name, email: form.email, password: form.password };
      const res = await axios.post(url, payload);
      localStorage.setItem("fl_token", res.data.token);
      localStorage.setItem("fl_name",  res.data.name);
      onAuth(res.data.token, res.data.name);
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong. Check your connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-bg">
      {/* ambient blobs */}
      <div className="blob blob1" />
      <div className="blob blob2" />

      <div className="auth-card">

        {/* brand */}
        <div className="auth-brand">
          <span className="auth-brand-dot" />
          <span className="auth-brand-name">Fake<strong>Lens</strong></span>
        </div>
        <p className="auth-sub">Multilingual Fake News Detector</p>

        {/* sliding tab switcher */}
        <div className="auth-tabs">
          <div
            className="auth-tab-slider"
            style={{ transform: mode === "login" ? "translateX(0)" : "translateX(100%)" }}
          />
          <button
            className={`auth-tab ${mode === "login" ? "at-active" : ""}`}
            onClick={() => switchMode("login")}
            type="button"
          >Sign In</button>
          <button
            className={`auth-tab ${mode === "register" ? "at-active" : ""}`}
            onClick={() => switchMode("register")}
            type="button"
          >Create Account</button>
        </div>

        {/* form — slides on mode change */}
        <form onSubmit={submit} className="auth-form" key={mode}>

          {mode === "register" && (
            <div className="af-field">
              <label>Full Name</label>
              <div className="af-input-wrap">
                <input
                  type="text"
                  placeholder="Your full name"
                  value={form.name}
                  onChange={e => set("name", e.target.value)}
                  required
                  autoComplete="name"
                />
              </div>
            </div>
          )}

          <div className="af-field">
            <label>Email Address</label>
            <div className="af-input-wrap">
              <input
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={e => set("email", e.target.value)}
                required
                autoComplete="email"
              />
            </div>
          </div>

          <div className="af-field">
            <label>Password</label>
            <div className="af-input-wrap">
              <input
                type={showPass ? "text" : "password"}
                placeholder={mode === "register" ? "Min 6 characters" : "Your password"}
                value={form.password}
                onChange={e => set("password", e.target.value)}
                required
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
              <button
                type="button"
                className="eye-btn"
                onClick={() => setShowPass(s => !s)}
                tabIndex={-1}
              >
                <EyeIcon open={showPass} />
              </button>
            </div>
          </div>

          {error && (
            <div className="auth-err">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="13"/>
                <circle cx="12" cy="17" r=".5" fill="currentColor"/>
              </svg>
              {error}
            </div>
          )}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading
              ? <AuthFlower />
              : mode === "login" ? "Sign In" : "Create Account"
            }
          </button>
        </form>

        <p className="auth-footer-text">
          {mode === "login"
            ? <>Don't have an account?&nbsp;
                <button type="button" onClick={() => switchMode("register")}>Sign up free</button>
              </>
            : <>Already have an account?&nbsp;
                <button type="button" onClick={() => switchMode("login")}>Sign in</button>
              </>
          }
        </p>
      </div>

      {/* full-screen loader on submit */}
      {loading && <FlowerLoader />}
    </div>
  );
}

/* small inline flower for button state */
function AuthFlower() {
  return (
    <span className="auth-flower-mini">
      {[0,1,2,3,4].map(i => (
        <span key={i} className="afm-petal" style={{"--n": i}} />
      ))}
      <span className="afm-core" />
    </span>
  );
}
