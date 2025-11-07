/**
 * Deterministic Random Number Generator
 *
 * Provides reproducible random sampling for bootstrap operations.
 * Uses a seeded PRNG to ensure identical results across runs.
 */

/**
 * Simple seeded PRNG (LCG algorithm)
 * Good enough for bootstrap sampling, not cryptographically secure
 */
export class DeterministicRNG {
  private seed: number;
  private current: number;

  // LCG parameters (same as glibc)
  private readonly a = 1103515245;
  private readonly c = 12345;
  private readonly m = 2 ** 31;

  constructor(seed: number = 42) {
    this.seed = seed;
    this.current = seed;
  }

  /**
   * Generate next random number [0, 1)
   */
  private next(): number {
    this.current = (this.a * this.current + this.c) % this.m;
    return this.current / this.m;
  }

  /**
   * Generate random integer in range [min, max)
   */
  randInt(min: number, max: number): number {
    return Math.floor(this.next() * (max - min)) + min;
  }

  /**
   * Generate random float in range [min, max)
   */
  randFloat(min: number = 0, max: number = 1): number {
    return this.next() * (max - min) + min;
  }

  /**
   * Generate array of random indices for bootstrap resampling
   */
  resampleIndices(n: number, size: number): number[] {
    const indices: number[] = [];
    for (let i = 0; i < size; i++) {
      indices.push(this.randInt(0, n));
    }
    return indices;
  }

  /**
   * Generate block bootstrap indices
   */
  resampleBlocks(n: number, blockSize: number): number[] {
    const numBlocks = Math.ceil(n / blockSize);
    const indices: number[] = [];

    for (let i = 0; i < numBlocks; i++) {
      const blockStart = this.randInt(0, Math.max(1, n - blockSize + 1));
      for (let j = 0; j < blockSize; j++) {
        if (blockStart + j < n) {
          indices.push(blockStart + j);
        }
      }
    }

    return indices.slice(0, n); // Ensure exact sample size
  }

  /**
   * Shuffle array in place (Fisher-Yates)
   */
  shuffle<T>(array: T[]): T[] {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = this.randInt(0, i + 1);
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  /**
   * Reset RNG to initial seed
   */
  reset(): void {
    this.current = this.seed;
  }

  /**
   * Get current seed
   */
  getSeed(): number {
    return this.seed;
  }
}

/**
 * Global deterministic RNG instance
 * All bootstrap operations should use this to ensure reproducibility
 */
let globalRNG: DeterministicRNG | null = null;

export function initializeGlobalRNG(seed: number = 42): void {
  globalRNG = new DeterministicRNG(seed);
}

export function getGlobalRNG(): DeterministicRNG {
  if (!globalRNG) {
    initializeGlobalRNG();
  }
  return globalRNG!;
}

export function resetGlobalRNG(): void {
  if (globalRNG) {
    globalRNG.reset();
  }
}
