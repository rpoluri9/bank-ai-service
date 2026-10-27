import { useEffect, useState } from "react";
import { bankingApi, aiApi } from "./api.js";

// Demo credentials are prefilled for convenience. This is a LOCAL DEMO ONLY:
// the banking API's demo user (see project README "Demo auth"). Nothing here
// is a real credential, and the demo password is never used anywhere else.
const DEMO_USER = "demo";
const DEMO_PASS = "demo123";

function shortId(id) {
  return id ? id.slice(0, 8) + "…" : "";
}

function Money({ value }) {
  const n = Number(value);
  return <span>{Number.isFinite(n) ? "$" + n.toFixed(2) : value}</span>;
}

export default function App() {
  const [auth, setAuth] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("bankai-auth") || "null");
      return saved || { username: DEMO_USER, password: DEMO_PASS };
    } catch {
      return { username: DEMO_USER, password: DEMO_PASS };
    }
  });
  const [loggedIn, setLoggedIn] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [newOwner, setNewOwner] = useState("");
  const [newType, setNewType] = useState("SAVINGS");
  const [newBalance, setNewBalance] = useState("1000");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [toAccountId, setToAccountId] = useState("");

  const [question, setQuestion] = useState("What is the overdraft fee?");
  const [aiAnswer, setAiAnswer] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiHealth, setAiHealth] = useState("");

  async function loadAccounts() {
    try {
      const list = await bankingApi.listAccounts(auth);
      setAccounts(list);
      setError("");
    } catch (e) {
      handleApiError(e);
    }
  }

  async function loadDetail(id) {
    try {
      const [acc, txs] = await Promise.all([
        bankingApi.getAccount(auth, id),
        bankingApi.transactions(auth, id),
      ]);
      setDetail(acc);
      setTransactions(txs);
      setSelectedId(id);
      setError("");
    } catch (e) {
      handleApiError(e);
    }
  }

  function handleApiError(e) {
    if (e.status === 401) {
      setError("Not authorized (401). Check the login name and password, then log in again.");
      setLoggedIn(false);
    } else {
      setError(e.message);
    }
  }

  function login(e) {
    e.preventDefault();
    localStorage.setItem("bankai-auth", JSON.stringify(auth));
    setLoggedIn(true);
    setNotice("");
    loadAccounts();
  }

  function logout() {
    localStorage.removeItem("bankai-auth");
    setLoggedIn(false);
    setAccounts([]);
    setDetail(null);
    setSelectedId(null);
  }

  useEffect(() => {
    // Try the saved demo login on first load; a 401 drops back to the form.
    loadAccounts().then(() => setLoggedIn(true)).catch(() => {});
    aiApi.health().then(
      (h) => setAiHealth(`AI service ok (provider: ${h.provider})`),
      () => setAiHealth("AI service not reachable on :8081")
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createAccount(e) {
    e.preventDefault();
    try {
      const acc = await bankingApi.createAccount(auth, {
        ownerName: newOwner,
        accountType: newType,
        openingBalance: Number(newBalance),
      });
      setNotice(`Account created for ${acc.ownerName}.`);
      setNewOwner("");
      await loadAccounts();
      await loadDetail(acc.id);
    } catch (err) {
      handleApiError(err);
    }
  }

  async function moneyOp(kind) {
    try {
      let acc;
      if (kind === "deposit") {
        acc = await bankingApi.deposit(auth, selectedId, { amount: Number(amount), description });
      } else if (kind === "withdraw") {
        acc = await bankingApi.withdraw(auth, selectedId, { amount: Number(amount), description });
      } else {
        acc = await bankingApi.transfer(auth, selectedId, {
          toAccountId,
          amount: Number(amount),
          description,
        });
      }
      setNotice(`${kind} succeeded. New balance: $${Number(acc.balance).toFixed(2)}.`);
      setAmount("");
      setDescription("");
      await loadDetail(selectedId);
      await loadAccounts();
    } catch (err) {
      handleApiError(err);
    }
  }

  async function askAi(e) {
    e.preventDefault();
    setAiLoading(true);
    setAiAnswer(null);
    try {
      const res = await aiApi.ask(question, selectedId);
      setAiAnswer(res);
    } catch (err) {
      setAiAnswer({ answer: `AI service error: ${err.message}`, sources: [], tools_used: [] });
    } finally {
      setAiLoading(false);
    }
  }

  if (!loggedIn) {
    return (
      <div className="page">
        <h1>Bank AI Platform</h1>
        <p className="muted">
          Banking demo: React frontend, Spring Boot + Spring Security backend, MySQL.
        </p>
        <form className="card" onSubmit={login}>
          <h2>Log in</h2>
          <label>
            Username
            <input value={auth.username} onChange={(e) => setAuth({ ...auth, username: e.target.value })} />
          </label>
          <label>
            Password
            <input type="password" value={auth.password} onChange={(e) => setAuth({ ...auth, password: e.target.value })} />
          </label>
          <button type="submit">Log in</button>
          <p className="muted small">
            Local demo only — the demo user is <code>demo</code> / <code>demo123</code> (see README).
            The banking API must be running on :8080.
          </p>
          {error && <p className="error">{error}</p>}
        </form>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="topbar">
        <h1>Bank AI Platform</h1>
        <div>
          <span className="muted">{auth.username} · </span>
          <button onClick={logout}>Log out</button>
        </div>
      </header>
      {error && <p className="error">{error}</p>}
      {notice && <p className="notice">{notice}</p>}
      <p className="muted small">{aiHealth}</p>

      <div className="grid">
        <section className="card">
          <h2>Accounts</h2>
          <ul className="acclist">
            {accounts.map((a) => (
              <li key={a.id}>
                <button
                  className={selectedId === a.id ? "selected" : ""}
                  onClick={() => loadDetail(a.id)}
                >
                  {a.ownerName} ({a.accountType}) — <Money value={a.balance} />
                  <span className="muted"> · {shortId(a.id)}</span>
                </button>
              </li>
            ))}
            {accounts.length === 0 && <li className="muted">No accounts yet — create one below.</li>}
          </ul>
          <form onSubmit={createAccount}>
            <h3>Create account</h3>
            <label>
              Owner name
              <input value={newOwner} onChange={(e) => setNewOwner(e.target.value)} required />
            </label>
            <label>
              Type
              <select value={newType} onChange={(e) => setNewType(e.target.value)}>
                <option value="SAVINGS">SAVINGS</option>
                <option value="CHECKING">CHECKING</option>
              </select>
            </label>
            <label>
              Opening balance
              <input type="number" min="0" step="0.01" value={newBalance} onChange={(e) => setNewBalance(e.target.value)} required />
            </label>
            <button type="submit">Create</button>
          </form>
        </section>

        <section className="card">
          <h2>Account detail</h2>
          {!detail && <p className="muted">Select an account to see its balance and history.</p>}
          {detail && (
            <>
              <p>
                <strong>{detail.ownerName}</strong> ({detail.accountType}) — balance{" "}
                <strong><Money value={detail.balance} /></strong>
                <span className="muted"> · id {detail.id}</span>
              </p>
              <label>
                Amount
                <input type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} />
              </label>
              <label>
                Description
                <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Paycheck, ATM, Rent…" />
              </label>
              <div className="row">
                <button onClick={() => moneyOp("deposit")} disabled={!amount}>Deposit</button>
                <button onClick={() => moneyOp("withdraw")} disabled={!amount}>Withdraw</button>
              </div>
              <label>
                Transfer to account id
                <input value={toAccountId} onChange={(e) => setToAccountId(e.target.value)} placeholder="Paste another account id" />
              </label>
              <button onClick={() => moneyOp("transfer")} disabled={!amount || !toAccountId}>Transfer</button>
              <h3>Transaction history</h3>
              <table>
                <thead>
                  <tr><th>Type</th><th>Amount</th><th>Balance after</th><th>Description</th></tr>
                </thead>
                <tbody>
                  {transactions.map((t) => (
                    <tr key={t.id}>
                      <td>{t.type}</td>
                      <td><Money value={t.amount} /></td>
                      <td><Money value={t.balanceAfter} /></td>
                      <td>{t.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>

        <section className="card">
          <h2>AI assistant</h2>
          <p className="muted small">
            Ask about fees or policies (answered from bank documents), or ask about your own
            money — the assistant calls the banking API with live data, never guesses.
          </p>
          <form onSubmit={askAi}>
            <label>
              Question
              <input value={question} onChange={(e) => setQuestion(e.target.value)} required />
            </label>
            <label>
              Account id (optional — defaults to the selected account)
              <input value={selectedId || ""} readOnly placeholder="Select an account first" />
            </label>
            <button type="submit" disabled={aiLoading}>{aiLoading ? "Asking…" : "Ask"}</button>
          </form>
          {aiAnswer && (
            <div className="answer">
              <p>{aiAnswer.answer}</p>
              {aiAnswer.sources && aiAnswer.sources.length > 0 && (
                <p className="muted small">Sources: {aiAnswer.sources.join(", ")}</p>
              )}
              {aiAnswer.tools_used && aiAnswer.tools_used.length > 0 && (
                <p className="muted small">Tools used: {aiAnswer.tools_used.join(", ")}</p>
              )}
            </div>
          )}
        </section>
      </div>
      <footer className="muted small">
        Portfolio demo — fictional bank, fictional data. No real money, no real credentials.
      </footer>
    </div>
  );
}
