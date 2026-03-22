/* ==============================
   API Client — handles fetch + JWT token management
   ============================== */

// Auto-detect backend URL from browser hostname for LAN support.
// When a LAN device opens http://192.168.1.10:3000, the API client
// will automatically target http://192.168.1.10:8000.
export function getApiBase(): string {
    const envBase = process.env.NEXT_PUBLIC_API_URL;
    if (typeof window !== "undefined") {
        if (envBase) {
            try {
                const envUrl = new URL(envBase);
                const envHost = envUrl.hostname;
                const currentHost = window.location.hostname;
                const envIsLocal = envHost === "localhost" || envHost === "127.0.0.1";
                const currentIsLocal = currentHost === "localhost" || currentHost === "127.0.0.1";

                // Keep explicit remote/tunnel API URLs, but do not force localhost
                // for LAN clients opening the app from another device.
                if (!envIsLocal || currentIsLocal) {
                    return envBase;
                }
            } catch {
                // If NEXT_PUBLIC_API_URL is malformed, ignore and fall back.
            }
        }

        return `${window.location.protocol}//${window.location.hostname}:8000`;
    }

    if (envBase) {
        return envBase;
    }
    // SSR fallback
    return "http://localhost:8000";
}


let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
    accessToken = token;
}

export function getAccessToken(): string | null {
    return accessToken;
}

class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
        this.name = "ApiError";
    }
}

async function request<T>(
    path: string,
    options: RequestInit = {},
    _isRetry = false,
): Promise<T> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };

    if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
    }

    let res: Response;
    try {
        res = await fetch(`${getApiBase()}${path}`, {
            ...options,
            headers,
            credentials: "include", // Send cookies (refresh token)
        });
    } catch {
        // Network-level failure (DNS, cold start, CORS preflight timeout).
        // Retry once after a short delay — this fixes the common "first
        // request after load fails" issue with Docker/LAN setups.
        const isSafeMethod = !options.method || options.method.toUpperCase() === 'GET' || options.method.toUpperCase() === 'HEAD';
        if (!_isRetry && isSafeMethod) {
            await new Promise((r) => setTimeout(r, 800));
            return request<T>(path, options, true);
        }
        throw new ApiError("Failed to connect to server", 0);
    }

    if (!res.ok) {
        // Try to refresh token on 401
        if (res.status === 401 && path !== "/api/auth/refresh" && path !== "/api/auth/login") {
            const refreshed = await tryRefreshToken();
            if (refreshed) {
                // Retry the request with new token
                headers["Authorization"] = `Bearer ${accessToken}`;
                const retryRes = await fetch(`${getApiBase()}${path}`, {
                    ...options,
                    headers,
                    credentials: "include",
                });
                if (retryRes.ok) {
                    return retryRes.json();
                }
            }
        }

        const body = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new ApiError(body.detail || "Request failed", res.status);
    }

    return res.json();
}

async function tryRefreshToken(): Promise<boolean> {
    try {
        const res = await fetch(`${getApiBase()}/api/auth/refresh`, {
            method: "POST",
            credentials: "include",
        });
        if (res.ok) {
            const data = await res.json();
            accessToken = data.access_token;
            return true;
        }
    } catch {
        // Refresh failed
    }
    return false;
}

// --- Auth API ---

export const authApi = {
    register: (username: string, password: string) =>
        request<{ access_token: string; token_type: string }>("/api/auth/register", {
            method: "POST",
            body: JSON.stringify({ username, password }),
        }),

    login: (username: string, password: string) =>
        request<{ access_token: string; token_type: string }>("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password }),
        }),

    refresh: () =>
        request<{ access_token: string; token_type: string }>("/api/auth/refresh", {
            method: "POST",
        }),

    logout: () =>
        request<{ message: string }>("/api/auth/logout", { method: "POST" }),
};

// --- User API ---

export const userApi = {
    getMe: () => request<import("./types").User>("/api/users/me"),
};

// --- Party API ---

export const partyApi = {
    create: (name: string, use_gold = true, use_electrum = false, use_platinum = false) =>
        request<import("./types").Party>("/api/parties", {
            method: "POST",
            body: JSON.stringify({ name, use_gold, use_electrum, use_platinum }),
        }),

    list: () => request<import("./types").Party[]>("/api/parties"),

    getDetail: (code: string) =>
        request<import("./types").PartyDetail>(`/api/parties/${code}`),

    join: (code: string, character_name: string, character_class: string) =>
        request<import("./types").CharacterInParty>(`/api/parties/${code}/join`, {
            method: "POST",
            body: JSON.stringify({ character_name, character_class }),
        }),

    leave: (code: string) =>
        request<{ message: string }>(`/api/parties/${code}/leave`, {
            method: "POST",
        }),

    kick: (code: string, character_id: number) =>
        request<{ message: string }>(`/api/parties/${code}/kick`, {
            method: "POST",
            body: JSON.stringify({ character_id }),
        }),

    archive: (code: string) =>
        request<import("./types").Party>(`/api/parties/${code}/archive`, {
            method: "PATCH",
        }),

    updateMyCoins: (code: string, config: { use_gold?: boolean; use_electrum?: boolean; use_platinum?: boolean }) =>
        request<import("./types").CoinSettings>(`/api/parties/${code}/my-coins`, {
            method: "PATCH",
            body: JSON.stringify(config),
        }),

    updateMyCharacterSettings: (code: string, settings: { is_balance_public?: boolean }) =>
        request<{ is_balance_public: boolean }>(`/api/parties/${code}/my-character-settings`, {
            method: "PATCH",
            body: JSON.stringify(settings),
        }),
};

// --- Transfer API ---

export const transferApi = {
    p2p: (code: string, receiver_id: number, amount: Record<string, number>, reason?: string) =>
        request<import("./types").TransactionResponse>(`/api/parties/${code}/transfers/p2p`, {
            method: "POST",
            body: JSON.stringify({ receiver_id, amount, reason }),
        }),

    distribute: (code: string, character_ids: number[], include_npc: boolean, amount: Record<string, number>, reason?: string) =>
        request<import("./types").TransactionResponse[]>(`/api/parties/${code}/transfers/distribute`, {
            method: "POST",
            body: JSON.stringify({ character_ids, include_npc, amount, reason }),
        }),

    loot: (code: string, character_ids: number[], amount: Record<string, number>, reason?: string, is_deduction = false) =>
        request<import("./types").TransactionResponse[]>(`/api/parties/${code}/transfers/loot`, {
            method: "POST",
            body: JSON.stringify({ character_ids, amount, reason, is_deduction }),
        }),

    godMode: (code: string, character_id: number, amount: Record<string, number>, is_deduction: boolean, reason?: string) =>
        request<import("./types").TransactionResponse>(`/api/parties/${code}/transfers/god-mode`, {
            method: "POST",
            body: JSON.stringify({ character_id, amount, is_deduction, reason }),
        }),

    spend: (code: string, amount: Record<string, number>, reason: string) =>
        request<import("./types").TransactionResponse>(`/api/parties/${code}/transfers/spend`, {
            method: "POST",
            body: JSON.stringify({ amount, reason }),
        }),

    selfAdd: (code: string, amount: Record<string, number>, reason?: string) =>
        request<import("./types").TransactionResponse>(`/api/parties/${code}/transfers/self-add`, {
            method: "POST",
            body: JSON.stringify({ amount, reason }),
        }),
};

// --- Transaction API ---

export const transactionApi = {
    getHistory: (code: string, page = 1, page_size = 20) =>
        request<import("./types").TransactionListResponse>(
            `/api/parties/${code}/transactions?page=${page}&page_size=${page_size}`
        ),
};

// --- Heroic Inspiration API ---

export const heroicInspirationApi = {
    grant: (code: string, characterId: number) =>
        request<import("./types").HeroicInspirationUpdate>(`/api/parties/${code}/heroic-inspiration/${characterId}/grant`, {
            method: "POST",
        }),

    revoke: (code: string, characterId: number) =>
        request<import("./types").HeroicInspirationUpdate>(`/api/parties/${code}/heroic-inspiration/${characterId}/revoke`, {
            method: "POST",
        }),

    use: (code: string) =>
        request<import("./types").HeroicInspirationUpdate>(`/api/parties/${code}/heroic-inspiration/use`, {
            method: "POST",
        }),
};

// --- Joint Payment API ---

export const jointPaymentApi = {
    create: (code: string, character_ids: number[], amount: Record<string, number>, reason?: string, receiver_character_id?: number) =>
        request<import("./types").JointPaymentResponse>(`/api/parties/${code}/joint-payments`, {
            method: "POST",
            body: JSON.stringify({ character_ids, amount, reason, receiver_character_id }),
        }),

    createDM: (code: string, character_ids: number[], amount: Record<string, number>, reason?: string, receiver_character_id?: number) =>
        request<import("./types").JointPaymentResponse>(`/api/parties/${code}/joint-payments/dm`, {
            method: "POST",
            body: JSON.stringify({ character_ids, amount, reason, receiver_character_id }),
        }),

    list: (code: string) =>
        request<import("./types").JointPaymentResponse[]>(`/api/parties/${code}/joint-payments`),

    accept: (code: string, paymentId: number) =>
        request<import("./types").JointPaymentResponse>(`/api/parties/${code}/joint-payments/${paymentId}/accept`, {
            method: "POST",
        }),

    reject: (code: string, paymentId: number) =>
        request<import("./types").JointPaymentResponse>(`/api/parties/${code}/joint-payments/${paymentId}/reject`, {
            method: "POST",
        }),

    cancel: (code: string, paymentId: number) =>
        request<import("./types").JointPaymentResponse>(`/api/parties/${code}/joint-payments/${paymentId}/cancel`, {
            method: "POST",
        }),
};

// --- Inventory API ---

export const inventoryApi = {
    list: (code: string, include_archived = false) =>
        request<import("./types").InventoryItemResponse[]>(
            `/api/parties/${code}/inventory?include_archived=${include_archived}`
        ),

    getHistory: (code: string, limit = 200) =>
        request<import("./types").InventoryHistoryListResponse>(
            `/api/parties/${code}/inventory/history?limit=${limit}`
        ),

    create: (
        code: string,
        body: {
            name: string;
            description_md: string;
            amount: number;
            owner_character_id?: number | null;
            is_public: boolean;
        }
    ) =>
        request<import("./types").InventoryItemResponse>(`/api/parties/${code}/inventory`, {
            method: "POST",
            body: JSON.stringify(body),
        }),

    update: (
        code: string,
        itemId: number,
        body: {
            name?: string;
            description_md?: string;
            amount?: number;
            is_public?: boolean;
        }
    ) =>
        request<import("./types").InventoryItemResponse>(`/api/parties/${code}/inventory/${itemId}`, {
            method: "PATCH",
            body: JSON.stringify(body),
        }),

    transfer: (code: string, itemId: number, owner_character_id: number | null) =>
        request<import("./types").InventoryItemResponse>(`/api/parties/${code}/inventory/${itemId}/transfer`, {
            method: "POST",
            body: JSON.stringify({ owner_character_id }),
        }),

    archive: (code: string, itemId: number) =>
        request<import("./types").InventoryItemResponse>(`/api/parties/${code}/inventory/${itemId}/archive`, {
            method: "POST",
        }),

    restore: (code: string, itemId: number) =>
        request<import("./types").InventoryItemResponse>(`/api/parties/${code}/inventory/${itemId}/restore`, {
            method: "POST",
        }),
};
