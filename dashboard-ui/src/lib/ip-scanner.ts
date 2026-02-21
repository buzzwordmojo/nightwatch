/**
 * IP Scanner for discovering Nightwatch devices on the local network.
 *
 * This is needed because mDNS (nightwatch.local) doesn't work on Android.
 * We scan common IP ranges to find the device by checking its health endpoint.
 */

import { checkHealth } from "./wifi-api";

const DASHBOARD_PORT = 9530;

// Common home network IP ranges
const COMMON_RANGES = [
  "192.168.86", // Google WiFi / Nest
  "192.168.1",  // Most common routers
  "192.168.0",  // Common routers
  "10.0.0",     // Some networks
  "10.0.1",     // Apple routers
];

/**
 * Generate list of possible device IPs to scan.
 */
function generatePossibleIPs(): string[] {
  const ips: string[] = [];

  for (const range of COMMON_RANGES) {
    // Scan common DHCP range (2-100)
    for (let host = 2; host <= 100; host++) {
      ips.push(`http://${range}.${host}:${DASHBOARD_PORT}`);
    }
  }

  return ips;
}

/**
 * Try to reach a single IP and return it if successful.
 */
async function tryIP(url: string, timeoutMs: number = 1000): Promise<string | null> {
  const health = await checkHealth(url, timeoutMs);
  return health ? url : null;
}

/**
 * Scan a batch of IPs in parallel.
 */
async function scanBatch(urls: string[], timeoutMs: number = 1000): Promise<string | null> {
  const results = await Promise.all(urls.map((url) => tryIP(url, timeoutMs)));
  return results.find((result) => result !== null) || null;
}

export interface ScanOptions {
  /** Timeout per IP in milliseconds */
  timeoutMs?: number;
  /** Number of IPs to scan in parallel */
  batchSize?: number;
  /** Callback for progress updates */
  onProgress?: (scanned: number, total: number) => void;
  /** Signal to abort scanning */
  signal?: AbortSignal;
}

export interface ScanResult {
  found: boolean;
  url: string | null;
  scanned: number;
}

/**
 * Discover Nightwatch device IP on the local network.
 *
 * First tries mDNS (nightwatch.local), then falls back to IP scanning.
 */
export async function discoverDevice(options: ScanOptions = {}): Promise<ScanResult> {
  const {
    timeoutMs = 1000,
    batchSize = 20,
    onProgress,
    signal,
  } = options;

  // First, try mDNS
  const mdnsUrl = `http://nightwatch.local:${DASHBOARD_PORT}`;
  const mdnsResult = await checkHealth(mdnsUrl, 2000);

  if (mdnsResult) {
    return { found: true, url: mdnsUrl, scanned: 0 };
  }

  // Fall back to IP scanning
  const possibleIPs = generatePossibleIPs();
  let scanned = 0;

  for (let i = 0; i < possibleIPs.length; i += batchSize) {
    // Check if aborted
    if (signal?.aborted) {
      return { found: false, url: null, scanned };
    }

    const batch = possibleIPs.slice(i, i + batchSize);
    const found = await scanBatch(batch, timeoutMs);

    scanned += batch.length;
    onProgress?.(scanned, possibleIPs.length);

    if (found) {
      return { found: true, url: found, scanned };
    }
  }

  return { found: false, url: null, scanned };
}

/**
 * Poll for device with retries.
 *
 * Used after WiFi configuration to wait for the device to come online.
 */
export async function pollForDevice(options: {
  maxAttempts?: number;
  intervalMs?: number;
  onAttempt?: (attempt: number, maxAttempts: number) => void;
  signal?: AbortSignal;
} = {}): Promise<ScanResult> {
  const {
    maxAttempts = 30,
    intervalMs = 2000,
    onAttempt,
    signal,
  } = options;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    if (signal?.aborted) {
      return { found: false, url: null, scanned: attempt };
    }

    onAttempt?.(attempt, maxAttempts);

    const result = await discoverDevice({
      timeoutMs: 1500,
      batchSize: 20,
      signal,
    });

    if (result.found) {
      return result;
    }

    // Wait before next attempt
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  return { found: false, url: null, scanned: maxAttempts };
}
