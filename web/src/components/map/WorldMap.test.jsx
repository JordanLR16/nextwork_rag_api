import { render, screen, waitFor, cleanup, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import WorldMap from "./WorldMap";

function feature(properties, x = 0) {
  return { type: "Feature", properties, geometry: {
    type: "Polygon", coordinates: [[[x, 0], [x + 5, 0], [x + 5, 5], [x, 5], [x, 0]]],
  } };
}
const countries = { type: "FeatureCollection", features: [
  feature({ country_code: "AAA", name: "Alpha" }),
  feature({ country_code: "BBB", name: "Beta" }, 10),
  feature({ country_code: "AAA", name: "Alpha Island" }, 20),
] };
const regions = { type: "FeatureCollection", features: [
  feature({ country_code: "AAA", region_code: "AAA001", region_name: "North Alpha" }),
] };
const response = (data) => ({ ok: true, json: async () => data });

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("requests and displays regions only after selection, then clears them in world view", async () => {
  const fetch = vi.fn().mockResolvedValueOnce(response(countries)).mockResolvedValueOnce(response(regions));
  vi.stubGlobal("fetch", fetch);
  const user = userEvent.setup();
  render(<WorldMap />);
  const country = await screen.findByRole("button", { name: "Alpha" });
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(screen.getAllByRole("option")).toHaveLength(3);
  expect(screen.queryByLabelText("North Alpha")).not.toBeInTheDocument();
  await user.click(country);
  expect(await screen.findByLabelText("North Alpha")).toBeInTheDocument();
  expect(fetch.mock.calls[1][0]).toMatch(/\/api\/countries\/AAA\/regions$/);
  await user.click(screen.getByRole("button", { name: "Back to world" }));
  expect(screen.queryByLabelText("North Alpha")).not.toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(2);
});

it("discards a late response when switching countries and handles missing regions", async () => {
  let finishAlpha;
  const fetch = vi.fn().mockResolvedValueOnce(response(countries))
    .mockImplementationOnce(() => new Promise((resolve) => { finishAlpha = resolve; }))
    .mockResolvedValueOnce({ ok: false, status: 404 });
  vi.stubGlobal("fetch", fetch);
  const user = userEvent.setup();
  render(<WorldMap />);
  await user.click(await screen.findByRole("button", { name: "Alpha" }));
  const signal = fetch.mock.calls[1][1].signal;
  await user.selectOptions(screen.getByRole("combobox", { name: "Country" }), "BBB");
  expect(signal.aborted).toBe(true);
  expect(await screen.findByText("No region data available for this country.")).toBeInTheDocument();
  await act(async () => finishAlpha(response(regions)));
  expect(screen.queryByLabelText("North Alpha")).not.toBeInTheDocument();
  expect(screen.getByText("No region data available for this country.")).toBeInTheDocument();
});

it("supports keyboard selection and reports region errors without removing the map", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response(countries))
    .mockResolvedValueOnce({ ok: false, status: 503 }));
  const user = userEvent.setup();
  render(<WorldMap />);
  (await screen.findByRole("button", { name: "Alpha" })).focus();
  await user.keyboard("{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("Region request failed: 503");
  expect(screen.getByRole("button", { name: "Alpha" })).toHaveAttribute("aria-pressed", "true");
  await user.click(screen.getByRole("button", { name: "Back to world" }));
  await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
});
