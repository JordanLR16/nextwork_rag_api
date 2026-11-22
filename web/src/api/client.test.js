import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clearAuthentication, getAccessToken } from "../auth/cognito";
import { getJson, postJson } from "./client";

vi.mock("../auth/cognito", () => ({ getAccessToken: vi.fn(), clearAuthentication: vi.fn() }));

beforeEach(() => {
  vi.resetAllMocks();
  getAccessToken.mockResolvedValue("access-token");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ count: 0 }) }));
});
afterEach(() => vi.unstubAllGlobals());

it("authenticates reads and writes using the current access token", async () => {
  await getJson("/recipes");
  await postJson("/pantry", { name: "Rice" });
  for (const [, options] of fetch.mock.calls) {
    expect(options.headers.Authorization).toBe("Bearer access-token");
    expect(options.headers["X-API-Key"]).toBeUndefined();
  }
  expect(fetch.mock.calls[1][1].body).toBe(JSON.stringify({ name: "Rice" }));
});

it("unloads private state when the API rejects the session", async () => {
  fetch.mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: "Session ended" }) });
  await expect(getJson("/recipes")).rejects.toThrow("Session ended");
  expect(clearAuthentication).toHaveBeenCalledOnce();
});

it("does not send anonymous requests when obtaining a token fails", async () => {
  getAccessToken.mockRejectedValue(new Error("Please sign in"));
  await expect(getJson("/recipes")).rejects.toThrow("Please sign in");
  expect(fetch).not.toHaveBeenCalled();
});
