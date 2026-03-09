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
    balance_visible_to_viewer: boolean;
    is_balance_public: boolean;
    is_active: boolean;
    user_id: number;
    username: string;
}

export interface PartyDetail extends Party {
    dm_username: string;
    my_coin_settings: CoinSettings;
    characters: CharacterInParty[];
}

export interface CoinSettings {
    use_gold: boolean;
    use_electrum: boolean;
    use_platinum: boolean;
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

export type InventoryEventType =
    | "item_created"
    | "item_updated"
    | "item_amount_changed"
    | "item_visibility_changed"
    | "item_transferred"
    | "item_deleted"
    | "item_restored";

export interface InventoryItemResponse {
    id: number;
    party_id: number;
    name: string;
    description_md: string;
    amount: number;
    owner_character_id: number | null;
    owner_name: string | null;
    is_public: boolean;
    is_active: boolean;
    created_by_user_id: number;
    updated_by_user_id: number;
    created_at: string;
    updated_at: string;
    can_edit: boolean;
}

export interface InventoryHistoryEntryResponse {
    id: number;
    event_type: InventoryEventType;
    item_id: number;
    item_name: string | null;
    timestamp: string;
    actor_username: string | null;
    redacted: boolean;
    summary: string;
    old_owner_name: string | null;
    new_owner_name: string | null;
    old_amount: number | null;
    new_amount: number | null;
    old_is_public: boolean | null;
    new_is_public: boolean | null;
}

export interface InventoryHistoryListResponse {
    events: InventoryHistoryEntryResponse[];
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
    receiver_character_id: number | null;
    receiver_name: string | null;
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
