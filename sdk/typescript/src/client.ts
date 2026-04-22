export interface AnswerGuardConfig {
  endpoint: string;
  sourceSystemId: string;
  timeoutMs?: number;
}

export interface CaptureOptions {
  metadata?: Record<string, string>;
}

interface CaptureResponseBody {
  qa_pair_id: string;
  captured_at: string;
}

export class AnswerGuard {
  private readonly endpoint: string;
  private readonly sourceSystemId: string;
  private readonly timeoutMs: number;

  constructor(config: AnswerGuardConfig) {
    this.endpoint = config.endpoint.replace(/\/$/, "");
    this.sourceSystemId = config.sourceSystemId;
    this.timeoutMs = config.timeoutMs ?? 2000;
  }

  /** Fire-and-forget. Never throws. Returns immediately. */
  capture(question: string, answer: string, options?: CaptureOptions): void {
    const payload = {
      question,
      answer,
      source_system_id: this.sourceSystemId,
      metadata: options?.metadata ?? {},
    };

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    fetch(`${this.endpoint}/v1/capture`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
      .then(() => clearTimeout(timer))
      .catch((err) => {
        clearTimeout(timer);
        console.error("[AnswerGuard] Capture failed:", err);
      });
  }

  /** Awaitable capture. Throws on failure. */
  async captureAsync(
    question: string,
    answer: string,
    options?: CaptureOptions
  ): Promise<{ qa_pair_id: string; captured_at: string }> {
    const payload = {
      question,
      answer,
      source_system_id: this.sourceSystemId,
      metadata: options?.metadata ?? {},
    };

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.endpoint}/v1/capture`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`AnswerGuard capture failed: ${response.status} ${response.statusText}`);
      }

      return (await response.json()) as CaptureResponseBody;
    } finally {
      clearTimeout(timer);
    }
  }
}
