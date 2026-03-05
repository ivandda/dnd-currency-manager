/* ==============================
   TypeScript types matching backend schemas
   ============================== */

export interface User {
    id: number;
    username: string;
    created_at: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface Party {
    id: number;
    name: string;
    code: string;
    dm_id: number;
    is_active: boolean;
    use_gold: boolean;
    use_electrum: boolean;
    use_platinum: boolean;
    created_at: string;
}

export interface CharacterInParty {
    id: number;
    name: string;
    character_class: string;
    balance_cp: number;
    balance_display: Record<string, number>;
    is_active: boolean;
    user_id: number;
    username: string;
}

export interface PartyDetail extends Party {
    dm_username: string;
    characters: CharacterInParty[];
}

export interface TransactionResponse {
    id: number;
    transaction_type: "transfer" | "dm_grant" | "dm_deduct" | "joint_payment" | "spend" | "self_add";
    amount_cp: number;
    amount_display: Record<string, number>;
    reason: string | null;
    timestamp: string;
    sender_id: number | null;
    sender_name: string | null;
    receiver_id: number | null;
    receiver_name: string | null;
}

export interface TransactionListResponse {
    transactions: TransactionResponse[];
    total: number;
    page: number;
    page_size: number;
}

export interface ParticipantResponse {
    character_id: number;
    character_name: string;
    share_cp: number;
    share_display: Record<string, number>;
    has_accepted: boolean;
}

export interface JointPaymentResponse {
    id: number;
    creator_character_id: number | null;
    creator_name: string | null;
    creator_is_dm: boolean;
    total_amount_cp: number;
    total_amount_display: Record<string, number>;
    reason: string | null;
    status: "pending" | "approved" | "rejected" | "cancelled";
    created_at: string;
    participants: ParticipantResponse[];
}

export type CoinType = "pp" | "gp" | "ep" | "sp" | "cp";

export const COIN_LABELS: Record<CoinType, string> = {
    pp: "Platinum",
    gp: "Gold",
    ep: "Electrum",
    sp: "Silver",
    cp: "Copper",
};

export const COIN_COLORS: Record<CoinType, string> = {
    pp: "text-platinum",
    gp: "text-gold",
    ep: "text-electrum",
    sp: "text-silver-coin",
    cp: "text-copper",
};
