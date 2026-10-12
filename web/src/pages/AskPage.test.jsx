import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { askKnowledgeBase } from "../api/recipes";
import AskPage from "./AskPage";

vi.mock("../api/recipes", () => ({
  askKnowledgeBase: vi.fn(),
}));

describe("AskPage", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("submits a question and displays the returned answer", async () => {
    const user = userEvent.setup();
    askKnowledgeBase.mockResolvedValueOnce({
      answer: "You can make spinach fried rice.",
    });

    render(<AskPage />);

    const question = "What can I make with spinach and rice?";
    await user.type(screen.getByLabelText(/question/i), question);
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(askKnowledgeBase).toHaveBeenCalledOnce();
    expect(askKnowledgeBase).toHaveBeenCalledWith(question);
    expect(
      await screen.findByText("You can make spinach fried rice."),
    ).toBeInTheDocument();
  });
});
