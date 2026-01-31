export interface User {
    user_id: string;
    name: string;
    risk_score: number;
    account_age_days?: number;
    status?: string;
    balance?: number;
    typology?: string;
    is_suspicious?: number;
    created_at?: string;
    transaction_count?: number;
    monthly_spending?: number;
    total_transactions?: number;
}

export interface Transaction {
    amount: number;
    timestamp: string;
    currency: string;
    transaction_type: string;
}

export interface FraudDetectionResponse {
    risk_probability: number;
    subgraph: {
        nodes: User[];
        edges: Transaction[];
    };
}