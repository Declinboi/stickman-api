import { Logger } from '@nestjs/common';
export interface RetryOptions {
  attempts: number;       // total number of attempts (including the first try)
  delay: number;          // initial delay in ms
  backoff?: 'fixed' | 'exponential'; // default: 'exponential'
  onRetry?: (error: unknown, attempt: number) => void;
}
/**
 * Executes `fn` and retries up to `options.attempts - 1` times on failure.
 *
 * @example
 * const result = await retryWithBackoff(() => someAsyncOperation(), {
 *   attempts: 3,
 *   delay: 1000,
 *   backoff: 'exponential',
 * });
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions,
  logger?: Logger,
  context?: string,
): Promise<T> {
  const { attempts, delay, backoff = 'exponential', onRetry } = options;
  let lastError: unknown;
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      const isLastAttempt = attempt === attempts;
      if (isLastAttempt) {
        logger?.error(
          `[${context ?? 'retryWithBackoff'}] All ${attempts} attempt(s) exhausted.`,
          error,
        );
        break;
      }
      const waitMs =
        backoff === 'exponential'
          ? delay * Math.pow(2, attempt - 1)  // 1s → 2s → 4s …
          : delay;
      logger?.warn(
        `[${context ?? 'retryWithBackoff'}] Attempt ${attempt}/${attempts} failed. ` +
          `Retrying in ${waitMs}ms…`,
      );
      onRetry?.(error, attempt);
      await sleep(waitMs);
    }
  }
  throw lastError;
}
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
