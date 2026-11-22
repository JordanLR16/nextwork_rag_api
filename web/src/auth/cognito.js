import { InMemoryWebStorage, UserManager, WebStorageStateStore } from "oidc-client-ts";

const region = import.meta.env.VITE_COGNITO_REGION;
const poolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;
const domain = (import.meta.env.VITE_COGNITO_DOMAIN || "").replace(/\/$/, "");
const issuer = `https://cognito-idp.${region}.amazonaws.com/${poolId}`;

export const authConfigured = Boolean(region && poolId && clientId && domain);
export const userManager = authConfigured ? new UserManager({
  authority: issuer,
  client_id: clientId,
  redirect_uri: `${window.location.origin}/auth/callback`,
  response_type: "code",
  scope: "openid email profile",
  // Keep tokens in memory; only the short-lived PKCE transaction uses sessionStorage.
  userStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
  stateStore: new WebStorageStateStore({ store: window.sessionStorage }),
  automaticSilentRenew: true,
  loadUserInfo: false,
  metadata: {
    issuer,
    authorization_endpoint: `${domain}/oauth2/authorize`,
    token_endpoint: `${domain}/oauth2/token`,
    jwks_uri: `${issuer}/.well-known/jwks.json`,
    revocation_endpoint: `${domain}/oauth2/revoke`,
  },
}) : null;

// React StrictMode mounts effects twice. Redeem a callback code only once.
let initialization;
export function initializeAuth() {
  initialization ??= (async () => {
    if (!userManager) return null;
    await userManager.clearStaleState();
    if (window.location.pathname === "/auth/callback") {
      try {
        return await userManager.signinRedirectCallback();
      } finally {
        window.history.replaceState({}, document.title, "/");
      }
    }
    return userManager.getUser();
  })();
  return initialization;
}

export async function getAccessToken() {
  if (!userManager) throw new Error("Sign-in is not configured.");
  let user = await userManager.getUser();
  if (user?.expired && user.refresh_token) {
    user = await userManager.signinSilent();
  }
  if (!user || user.expired) throw new Error("Please sign in to continue.");
  return user.access_token;
}

export async function signIn() {
  if (!userManager) throw new Error("Sign-in is not configured.");
  await userManager.signinRedirect();
}

export async function signOut() {
  if (!userManager) return;
  userManager.stopSilentRenew();
  try {
    // Cognito's revoke endpoint supports refresh-token revocation.
    await userManager.revokeTokens(["refresh_token"]);
  } finally {
    await userManager.removeUser();
    const url = new URL(`${domain}/logout`);
    url.searchParams.set("client_id", clientId);
    url.searchParams.set("logout_uri", `${window.location.origin}/`);
    window.location.assign(url.toString());
  }
}

export async function clearAuthentication() {
  await userManager?.removeUser();
}
