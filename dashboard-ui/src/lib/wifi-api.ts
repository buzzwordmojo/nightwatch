/**
 * WiFi API client for communicating with the Nightwatch portal and dashboard.
 * Works with both the captive portal (192.168.4.1) and dashboard (nightwatch.local:9530).
 */

export interface Network {
  ssid: string;
  signal: number;
  security?: string;
}

export interface WifiScanResponse {
  networks: Network[];
}

export interface WifiConfigResponse {
  success: boolean;
  message: string;
  ssid?: string;
  redirect_url?: string;
  hotspot_shutdown_delay?: number;
}

export interface HealthResponse {
  status: string;
  service?: string;
  running?: boolean;
  connections?: number;
}

/**
 * Check if a service is reachable via health endpoint.
 */
export async function checkHealth(
  baseUrl: string,
  timeoutMs: number = 2000
): Promise<HealthResponse | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${baseUrl}/health`, {
      mode: "cors",
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      return await response.json();
    }
    return null;
  } catch {
    clearTimeout(timeoutId);
    return null;
  }
}

/**
 * Scan for available WiFi networks.
 */
export async function scanNetworks(baseUrl: string): Promise<Network[]> {
  try {
    const response = await fetch(`${baseUrl}/api/setup/wifi/scan`, {
      mode: "cors",
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Scan failed: ${response.status}`);
    }

    const data: WifiScanResponse = await response.json();
    return data.networks || [];
  } catch (error) {
    console.error("WiFi scan error:", error);
    throw error;
  }
}

/**
 * Submit WiFi credentials to configure the device.
 */
export async function submitCredentials(
  baseUrl: string,
  ssid: string,
  password: string
): Promise<WifiConfigResponse> {
  try {
    const response = await fetch(`${baseUrl}/api/setup/wifi`, {
      method: "POST",
      mode: "cors",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ssid, password }),
    });

    const data: WifiConfigResponse = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.message || "Failed to configure WiFi");
    }

    return data;
  } catch (error) {
    console.error("WiFi config error:", error);
    throw error;
  }
}
