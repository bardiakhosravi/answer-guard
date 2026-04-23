import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ProgressCard from "../ProgressCard";
import type { ImportJob } from "../../types";

function buildJob(overrides: Partial<ImportJob> = {}): ImportJob {
  return {
    runId: "a1b2c3d4-5678-9abc-def0-1234567890ab",
    status: "RUNNING",
    recordsProcessed: 0,
    recordsSkipped: 0,
    lastCheckpoint: null,
    startedAt: new Date().toISOString(),
    completedAt: null,
    errors: [],
    ...overrides,
  };
}

describe("ProgressCard", () => {
  it("renders the RUNNING status badge", () => {
    render(<ProgressCard job={buildJob({ status: "RUNNING" })} />);
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
  });

  it("renders the COMPLETED status badge", () => {
    render(<ProgressCard job={buildJob({ status: "COMPLETED" })} />);
    expect(screen.getByText("COMPLETED")).toBeInTheDocument();
  });

  it("renders the FAILED status badge", () => {
    render(<ProgressCard job={buildJob({ status: "FAILED" })} />);
    expect(screen.getByText("FAILED")).toBeInTheDocument();
  });

  it("renders the RESUMED status badge", () => {
    render(<ProgressCard job={buildJob({ status: "RESUMED" })} />);
    expect(screen.getByText("RESUMED")).toBeInTheDocument();
  });

  it("formats processed and skipped counts", () => {
    render(<ProgressCard job={buildJob({ recordsProcessed: 1234, recordsSkipped: 56 })} />);
    expect(screen.getByText("1,234")).toBeInTheDocument();
    expect(screen.getByText("56")).toBeInTheDocument();
  });

  it("shows last checkpoint when set", () => {
    render(<ProgressCard job={buildJob({ lastCheckpoint: 4200 })} />);
    expect(screen.getByText("4,200")).toBeInTheDocument();
    expect(screen.getByText(/Last checkpoint/)).toBeInTheDocument();
  });

  it("does not show the checkpoint line when not set", () => {
    render(<ProgressCard job={buildJob({ lastCheckpoint: null })} />);
    expect(screen.queryByText(/Last checkpoint/)).not.toBeInTheDocument();
  });

  it("truncates the run ID for readability", () => {
    render(<ProgressCard job={buildJob({ runId: "a1b2c3d4-5678-9abc-def0-1234567890ab" })} />);
    expect(screen.getByText(/a1b2c3d4/)).toBeInTheDocument();
    expect(screen.queryByText(/1234567890ab/)).not.toBeInTheDocument();
  });
});
