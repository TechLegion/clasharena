export interface User {
  id: string
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  created_at: string
  updated_at: string
}

export interface Wallet {
  id: string
  user_id: string
  balance: number
  currency: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Transaction {
  id: string
  wallet_id: string
  amount: number
  transaction_type: 'deposit' | 'withdrawal' | 'match_bet' | 'match_win' | 'referral_bonus'
  status: 'pending' | 'completed' | 'failed'
  reference: string
  description?: string
  external_reference?: string
  created_at: string
  updated_at: string
}

export interface Match {
  id: string
  user_id: string
  game_type: string
  match_type: 'head_to_head' | 'tournament' | 'challenge'
  status: 'pending' | 'active' | 'completed' | 'cancelled'
  bet_amount: number
  potential_winnings: number
  opponent_id?: string
  match_data?: string
  result?: string
  created_at: string
  updated_at: string
}

export interface Referral {
  id: string
  referrer_id: string
  referred_id: string
  referral_code: string
  status: 'pending' | 'completed' | 'failed'
  reward_amount: number
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  full_name: string
  password: string
}
