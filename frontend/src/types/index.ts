export type DietType = 'veg' | 'vegan' | 'eggetarian' | 'non_veg';

export type MarkerStatus = 'low' | 'borderline' | 'normal' | 'high';

export type Activity = 'none' | 'walking' | 'cycling' | 'running';

export interface UserProfile {
  age: number;
  gender: string;
  diet_type: DietType;
  allergens: string[];
  name?: string;
  height_cm?: number | null;
  weight_kg?: number | null;
  activity?: Activity;
  region?: string;
  meats?: string[];
  custom_allergies?: string[];
  existing_diet?: string;
}

/* ------------------------------------------------------------------ diet plans */

export type MealSlot = 'breakfast' | 'lunch' | 'snack' | 'dinner';
export type PlanStyle = 'familiar' | 'nutritious' | 'regional';

export interface PlanItem {
  dish_id: string;
  name: string;
  names?: { hi?: string; te?: string };
  servings: number;
  serving: string;
  role: string;
  energy_kcal: number;
}

export interface PlanTargets {
  energy_kcal: number;
  protein_g: number;
  rda: Record<string, number>;
  low: string[];
  sodium_mg: number;
  bmi: number;
}

export interface PlanDay {
  meals: Record<MealSlot, PlanItem[]>;
  totals: Record<string, number>;
  targets: PlanTargets;
  rda_met: Record<string, boolean>;
  salt_g: number;
  style?: PlanStyle;
  title?: string;
}

export interface ShoppingItem {
  name: string;
  names?: { hi: string; te: string };
  aisle?: string;
  edible_g: number;
  buy_g: number;
}

export interface ReferenceRange {
  low: number | null;
  high: number | null;
}

export interface DetectedBiomarker {
  biomarker_key: string;
  display_name: string;
  detected_value: number;
  detected_unit: string;
  canonical_value: number | null;
  canonical_unit: string;
  report_reference_range: ReferenceRange | null;
  extraction_method: string;
  confidence: number | null;
  verification_status?: string;
  qualifier?: string | null;
  source_page?: number | null;
  source_text?: string | null;
  warnings?: string[];
}

export interface ExtractionResponse {
  session_id: string;
  sanitized_preview: string;
  extracted_biomarkers: DetectedBiomarker[];
  unmatched_text_lines: string[];
  warnings?: string[];
}

export interface MarkerInput {
  biomarker_key: string;
  value: number;
  unit: string;
  reference_low?: number | null;
  reference_high?: number | null;
}

export interface MarkerAnalysisResult {
  biomarker_key: string;
  display_name: string;
  value: number;
  unit: string;
  status: MarkerStatus;
  range_low: number;
  range_high: number;
  percentage_of_optimal: number;
  clinical_warning?: string | null;
  target_nutrient_key: string;
}

export interface FoodRecommendation {
  id: string;
  name: string;
  hindi_name?: string | null;
  category: string;
  serving_size: string;
  key_nutrient_yield: string;
  synergies: string[];
  preparation_tip?: string | null;
}

export interface NutrientRecommendationPlan {
  target_biomarker: string;
  biomarker_display_name: string;
  status: MarkerStatus;
  recommended_foods: FoodRecommendation[];
  absorption_dos: string[];
  absorption_donts: string[];
  purpose?: 'improve' | 'maintain';
}

export interface FullAnalysisResponse {
  analysis_id: string;
  timestamp: string;
  user_profile: UserProfile;
  status_summary: {
    low: number;
    borderline: number;
    normal: number;
    high: number;
  };
  marker_analyses: MarkerAnalysisResult[];
  recommendations: NutrientRecommendationPlan[];
  grounded_explanation: string;
  requires_physician_consult: boolean;
  consult_reasons: string[];
  saved_to_history?: boolean;
  diet_plan?: { style: PlanStyle; days: PlanDay[]; shopping_list: ShoppingItem[]; saved_at?: string } | null;
}

/* ------------------------------------------------------------------ accounts */

export type Role = 'user' | 'admin' | 'owner';
export type AccountStatus = 'active' | 'disabled';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  status: AccountStatus;
  created_at: string;
  last_login_at?: string | null;
}

export interface LinkInfo {
  kind: 'invite' | 'reset';
  email: string;
  role?: Role | null;
  expires_at: string;
  invited_by?: string | null;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/* ------------------------------------------------------------------ history */

export interface HistoryMarker {
  biomarker_key: string;
  display_name: string;
  status: MarkerStatus;
  value: number;
  unit: string;
}

export interface HistoryItem {
  id: string;
  created_at: string;
  status_summary: Record<string, number>;
  marker_count: number;
  requires_consult: boolean;
  markers: HistoryMarker[];
}

/* ------------------------------------------------------------------ admin */

export interface AdminUser extends User {
  report_count: number;
  locked: boolean;
  can_manage: boolean;
}

export interface Invite {
  id: string;
  email: string;
  role: Role | null;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  created_at: string;
  expires_at: string;
  created_by?: string | null;
}

export interface InviteCreated {
  invite: Invite;
  path: string;
}

export interface LinkCreated {
  path: string;
  expires_at: string;
}

export interface AddAdminResult {
  action: 'promoted' | 'invited';
  user?: AdminUser | null;
  invite?: Invite | null;
  path?: string | null;
}

export interface AdminStats {
  users_total: number;
  users_by_role: Record<Role, number>;
  users_disabled: number;
  reports_total: number;
  reports_last_7_days: number;
  signups_last_7_days: number;
  daily: { date: string; analyses: number; signups: number }[];
}

export interface AuditEntry {
  id: number;
  created_at: string;
  actor_email: string | null;
  action: string;
  target_type: string | null;
  target_email: string | null;
  ip: string | null;
  details: Record<string, unknown> | null;
}
