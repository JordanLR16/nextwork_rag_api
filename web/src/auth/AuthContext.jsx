import { createContext, useContext, useEffect, useRef, useState } from "react";
import { authConfigured, initializeAuth, signIn, signOut, userManager } from "./cognito";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const signingOut = useRef(false);

  useEffect(() => {
    let active = true;
    const loaded = (value) => {
      if (!signingOut.current) { setUser(value); setError(""); }
    };
    const unloaded = () => setUser(null);
    const failed = () => { setUser(null); setError("Your session ended. Please sign in again."); };
    userManager?.events.addUserLoaded(loaded);
    userManager?.events.addUserUnloaded(unloaded);
    userManager?.events.addAccessTokenExpired(failed);
    userManager?.events.addSilentRenewError(failed);
    initializeAuth().then((value) => {
      if (active) setUser(value && !value.expired ? value : null);
    }).catch(() => {
      if (active) setError("Sign-in could not be completed. Please try again.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => {
      active = false;
      userManager?.events.removeUserLoaded(loaded);
      userManager?.events.removeUserUnloaded(unloaded);
      userManager?.events.removeAccessTokenExpired(failed);
      userManager?.events.removeSilentRenewError(failed);
    };
  }, []);

  async function login() {
    signingOut.current = false;
    setError("");
    try { await signIn(); }
    catch { setError("Unable to start sign-in. Please try again."); }
  }

  async function logout() {
    // Unmount private pages immediately, before contacting Cognito.
    signingOut.current = true;
    setUser(null);
    setLoading(true);
    try { await signOut(); }
    catch { setError("Signed out locally. Please close this tab if the login page does not open."); }
    finally { setLoading(false); }
  }

  return <AuthContext.Provider value={{ user, loading, error, login, logout, configured: authConfigured }}>
    {children}
  </AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

export function SignInPanel() {
  const { loading, error, login, configured } = useAuth();
  return <section className="panel">
    <h1>Your personal recipe book</h1>
    <p>Sign in to save recipes, manage your pantry, and ask questions from your own knowledge base.</p>
    {loading ? <p role="status">Checking sign-in...</p> : configured ?
      <button onClick={login}>Sign in or create an account</button> :
      <p role="alert">Sign-in is not configured. Add the Cognito settings and restart the frontend.</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </section>;
}

export function AccountControls() {
  const { user, logout, login, loading, configured } = useAuth();
  if (loading || !configured) return null;
  return <div className="account-controls">
    {user ? <>
      <span>{user.profile.email || "Signed in"}</span>
      <button onClick={logout}>Sign out</button>
    </> : <button onClick={login}>Sign in</button>}
  </div>;
}
