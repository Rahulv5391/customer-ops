export type KBCategory = 'faq' | 'policy' | 'sop' | 'canned_response';

export interface KBDocumentResponse {
  id: string;
  title: string;
  category: KBCategory;
  version: string;
  source_updated_at: string;
  content_json: string;
  source_filename: string;
  content_hash: string;
  created_at: string;
}

export interface KBSearchHit {
  text: string;
  similarity: number;
  document_title: string;
  version: string;
  source_updated_at: string;
  section: string;
}
