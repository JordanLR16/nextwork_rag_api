import { act, cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";

const mocks = vi.hoisted(() => ({
  initializeAuth: vi.fn(), signOut: vi.fn(), signIn: vi.fn(), handlers: {},
}));
vi.mock("./cognito", () => ({
  authConfigured: true,
  initializeAuth: mocks.initializeAuth,
  signOut: mocks.signOut,
  signIn: mocks.signIn,
  userManager: {
    events: Object.fromEntries(["UserLoaded", "UserUnloaded", "AccessTokenExpired", "SilentRenewError"].flatMap((event) => [
      [`add${event}`, (handler) => { mocks.handlers[event] = handler; }],
      [`remove${event}`, () => { delete mocks.handlers[event]; }],
    ])),
  },
}));

function PrivatePage() {
  const { user, logout } = useAuth();
  return user ? <><p>Private recipes for {user.profile.sub}</p><button onClick={logout}>Sign out</button></> : <p>Sign in required</p>;
}

beforeEach(() => { vi.clearAllMocks(); });
afterEach(cleanup);

it("hides private content on session expiry", async () => {
  mocks.initializeAuth.mockResolvedValue({ profile: { sub: "alice" } });
  render(<AuthProvider><PrivatePage /></AuthProvider>);
  expect(await screen.findByText("Private recipes for alice")).toBeInTheDocument();
  act(() => mocks.handlers.AccessTokenExpired());
  expect(screen.queryByText("Private recipes for alice")).not.toBeInTheDocument();
  expect(screen.getByText("Sign in required")).toBeInTheDocument();
});

it("keeps private content hidden if token revocation emits another user-loaded event", async () => {
  const alice = { profile: { sub: "alice" } };
  mocks.initializeAuth.mockResolvedValue(alice);
  let finishSignOut;
  mocks.signOut.mockImplementation(() => {
    mocks.handlers.UserLoaded(alice);
    return new Promise((resolve) => { finishSignOut = resolve; });
  });
  render(<AuthProvider><PrivatePage /></AuthProvider>);
  await screen.findByText("Private recipes for alice");
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  expect(screen.queryByText("Private recipes for alice")).not.toBeInTheDocument();
  await act(async () => finishSignOut());
  expect(screen.getByText("Sign in required")).toBeInTheDocument();
});
