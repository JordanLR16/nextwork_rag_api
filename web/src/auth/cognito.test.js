import { afterEach, beforeEach, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  getUser: vi.fn(), signinRedirectCallback: vi.fn(), signinRedirect: vi.fn(),
  signinSilent: vi.fn(), clearStaleState: vi.fn(), removeUser: vi.fn(),
}));

vi.mock("oidc-client-ts", () => ({
  InMemoryWebStorage: class {},
  WebStorageStateStore: class { constructor(settings) { this.settings = settings; } },
  UserManager: class { constructor(settings) { this.settings = settings; Object.assign(this, mocks); } },
}));

beforeEach(() => {
  vi.resetModules();
  vi.resetAllMocks();
  vi.stubEnv("VITE_COGNITO_REGION", "us-east-1");
  vi.stubEnv("VITE_COGNITO_USER_POOL_ID", "us-east-1_test");
  vi.stubEnv("VITE_COGNITO_CLIENT_ID", "public-client");
  vi.stubEnv("VITE_COGNITO_DOMAIN", "https://login.example.com/");
  window.history.replaceState({}, "", "/");
});

afterEach(() => { vi.unstubAllEnvs(); });

it("uses authorization code login, isolated memory token storage, and session-scoped PKCE state", async () => {
  const { userManager, signIn } = await import("./cognito");
  expect(userManager.settings.response_type).toBe("code");
  expect(userManager.settings.scope).toBe("openid email");
  expect(userManager.settings.disablePKCE).not.toBe(true);
  expect(userManager.settings.client_secret).toBeUndefined();
  expect(userManager.settings.stateStore.settings.store).toBe(window.sessionStorage);
  expect(userManager.settings.userStore.settings.store).not.toBe(window.sessionStorage);
  expect(userManager.settings.metadata.authorization_endpoint).toBe("https://login.example.com/oauth2/authorize");
  await signIn();
  expect(mocks.signinRedirect).toHaveBeenCalledOnce();
});

it("redeems a callback once and removes its code from the address bar", async () => {
  window.history.replaceState({}, "", "/auth/callback?code=one-use-code&state=test");
  mocks.signinRedirectCallback.mockResolvedValue({ access_token: "access" });
  const { initializeAuth } = await import("./cognito");
  const [first, second] = await Promise.all([initializeAuth(), initializeAuth()]);
  expect(first).toEqual(second);
  expect(mocks.signinRedirectCallback).toHaveBeenCalledOnce();
  expect(window.location.pathname).toBe("/");
  expect(window.location.search).toBe("");
});

it("cleans up failed callbacks and does not reuse their authorization code", async () => {
  window.history.replaceState({}, "", "/auth/callback?error=access_denied");
  mocks.signinRedirectCallback.mockRejectedValue(new Error("denied"));
  const { initializeAuth } = await import("./cognito");
  await expect(initializeAuth()).rejects.toThrow("denied");
  expect(window.location.pathname).toBe("/");
  expect(window.location.search).toBe("");
});

it("uses access tokens and renews an expired session when possible", async () => {
  mocks.getUser.mockResolvedValue({ expired: true, refresh_token: "refresh", id_token: "id" });
  mocks.signinSilent.mockResolvedValue({ expired: false, access_token: "renewed-access" });
  const { getAccessToken } = await import("./cognito");
  expect(await getAccessToken()).toBe("renewed-access");
  expect(mocks.signinSilent).toHaveBeenCalledOnce();
});

it("fails closed when no session or configuration exists", async () => {
  const { getAccessToken } = await import("./cognito");
  mocks.getUser.mockResolvedValue(null);
  await expect(getAccessToken()).rejects.toThrow("Please sign in");
  vi.resetModules();
  vi.stubEnv("VITE_COGNITO_CLIENT_ID", "");
  const unconfigured = await import("./cognito");
  expect(unconfigured.authConfigured).toBe(false);
  await expect(unconfigured.getAccessToken()).rejects.toThrow("not configured");
});
