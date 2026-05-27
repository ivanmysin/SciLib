// API Types for SciLib Frontend

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'user' | 'admin';
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface Item {
  id: string;
  title: string;
  authors: Author[];
  year?: number;
  journal?: string;
  doi?: string;
  abstract?: string;
  item_type: 'article' | 'book' | 'thesis' | 'report' | 'other';
  created_at: string;
  updated_at: string;
  attachments: Attachment[];
  tags: Tag[];
  collections: Collection[];
}

export interface Author {
  given_name: string;
  family_name: string;
  affiliation?: string;
}

export interface Attachment {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  is_primary: boolean;
  processing_status: 'pending' | 'processing' | 'success' | 'failed';
  created_at: string;
}

export interface Collection {
  id: string;
  name: string;
  parent_id?: string;
  children?: Collection[];
  item_count: number;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: string;
  name: string;
  color?: string;
  item_count: number;
}

export interface Group {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  members: GroupMember[];
  created_at: string;
  updated_at: string;
}

export interface GroupMember {
  user_id: string;
  user: User;
  role: 'member' | 'admin';
  joined_at: string;
}

export interface Job {
  id: string;
  job_type: 'pdf_process' | 'crossref_enrich' | 'citation_resolve' | 'embedding';
  status: 'pending' | 'running' | 'success' | 'failed';
  item_id?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface SearchQuery {
  query: string;
  mode: 'simple' | 'advanced' | 'semantic';
  filters?: {
    authors?: string[];
    year_from?: number;
    year_to?: number;
    journals?: string[];
    item_types?: string[];
    tags?: string[];
    collection_id?: string;
  };
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  items: Item[];
  total: number;
  has_more: boolean;
}

export interface WebDAVConfig {
  url: string;
  username: string;
  password_set: boolean;
}

export interface MCPToken {
  token: string;
  expires_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  webdav_config?: WebDAVConfig;
  zotero_connected: boolean;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface CreateItemRequest {
  title: string;
  authors: Author[];
  year?: number;
  journal?: string;
  doi?: string;
  abstract?: string;
  item_type: 'article' | 'book' | 'thesis' | 'report' | 'other';
  collection_ids?: string[];
  tag_ids?: string[];
}

export interface UpdateItemRequest {
  title?: string;
  authors?: Author[];
  year?: number;
  journal?: string;
  doi?: string;
  abstract?: string;
  item_type?: 'article' | 'book' | 'thesis' | 'report' | 'other';
}

export interface CreateCollectionRequest {
  name: string;
  parent_id?: string;
}

export interface CreateGroupRequest {
  name: string;
  description?: string;
  member_ids?: string[];
}

export interface AddGroupMemberRequest {
  user_id: string;
  role: 'member' | 'admin';
}

export interface APIError {
  detail: string;
  status_code: number;
}
