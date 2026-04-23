import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ImprovementFormModal from "../ImprovementFormModal";

function renderCreate(overrides: Partial<Parameters<typeof ImprovementFormModal>[0]> = {}) {
  const onSave = vi.fn(async () => {});
  const onClose = vi.fn();
  render(
    <ImprovementFormModal
      open
      mode="create"
      excerpt="the agent said this"
      onClose={onClose}
      onSave={onSave}
      {...overrides}
    />,
  );
  return { onSave, onClose };
}

describe("ImprovementFormModal", () => {
  it("does not render when closed", () => {
    render(
      <ImprovementFormModal
        open={false}
        mode="create"
        excerpt="x"
        onClose={() => {}}
        onSave={async () => {}}
      />,
    );
    expect(screen.queryByText("Improve this response")).not.toBeInTheDocument();
  });

  it("renders create-mode title and button", () => {
    renderCreate();
    expect(screen.getByText("Improve this response")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save guideline" })).toBeInTheDocument();
  });

  it("renders edit-mode title and button", () => {
    render(
      <ImprovementFormModal
        open
        mode="edit"
        excerpt="x"
        onClose={() => {}}
        onSave={async () => {}}
      />,
    );
    expect(screen.getByText("Edit guideline")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
  });

  it("disables Save until both fields have 3+ non-whitespace characters", () => {
    renderCreate();
    const save = screen.getByRole("button", { name: "Save guideline" });
    const [problem, desired] = screen.getAllByRole("textbox");
    expect(save).toBeDisabled();

    fireEvent.change(problem, { target: { value: "ab" } });
    fireEvent.change(desired, { target: { value: "abc" } });
    expect(save).toBeDisabled(); // problem still too short

    fireEvent.change(problem, { target: { value: "abc" } });
    expect(save).toBeEnabled();

    fireEvent.change(problem, { target: { value: "   " } });
    expect(save).toBeDisabled(); // whitespace doesn't count
  });

  it("calls onSave with trimmed values", async () => {
    const { onSave } = renderCreate();
    const [problem, desired] = screen.getAllByRole("textbox");
    fireEvent.change(problem, { target: { value: "  too verbose  " } });
    fireEvent.change(desired, { target: { value: "  be concise  " } });
    fireEvent.click(screen.getByRole("button", { name: "Save guideline" }));
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith("too verbose", "be concise");
    });
  });

  it("shows an error banner when onSave rejects", async () => {
    const onSave = vi.fn(async () => {
      throw new Error("network down");
    });
    render(
      <ImprovementFormModal
        open
        mode="create"
        excerpt="x"
        onClose={() => {}}
        onSave={onSave}
      />,
    );
    const [problem, desired] = screen.getAllByRole("textbox");
    fireEvent.change(problem, { target: { value: "abc" } });
    fireEvent.change(desired, { target: { value: "def" } });
    fireEvent.click(screen.getByRole("button", { name: "Save guideline" }));
    await waitFor(() => {
      expect(screen.getByText(/Could not save: network down/)).toBeInTheDocument();
    });
  });
});
