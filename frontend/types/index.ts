export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface Patent {
  id: string;
  patent_number: string;
  title: string;
  abstract: string;
  description: string;
  inventors: string;
  assignee: string;
  publication_date: string;
  domain: string;
  source_url?: string;
}

export interface FeatureComparisonItem {
  target_feature: string;
  prior_art_feature: string;
  match_level: 'Strong' | 'Partial' | 'Weak' | 'Not Found';
  explanation: string;
}

export interface SearchResultItem {
  patent: Patent;
  semantic_score: number;
  keyword_score: number;
  domain_score: number;
  final_score: number;
  matched_concepts: string[];
  rank: number;
  semantic_similarity_label?: string;
  relevance_explanation?: string;
  feature_comparison?: FeatureComparisonItem[];
  patent_specific_insights?: string[];
}

export interface SearchSummary {
  total_results: number;
  high_similarity: number;
  moderate_similarity: number;
  low_similarity: number;
  very_high_similarity: number;
}

export interface PriorArtSearchResponse {
  search_id: string;
  invention_title: string;
  domain: string;
  created_at: string;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY HIGH';
  risk_label: string;
  highest_similarity: number;
  summary: SearchSummary;
  results: SearchResultItem[];
  is_demo_dataset: boolean;
  disclaimer: string;
}

export interface SearchHistoryItem {
  id: string;
  invention_title: string;
  domain: string;
  created_at: string;
  highest_similarity: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY HIGH';
  total_results: number;
}

export interface SavedPatent {
  id: string;
  patent_id: string;
  notes?: string;
  created_at: string;
  patent: Patent;
}

export interface Report {
  id: string;
  search_id: string;
  report_path: string;
  created_at: string;
}

export interface SearchFormData {
  title: string;
  domain: string;
  problem_statement: string;
  description: string;
  keywords: string[];
}
