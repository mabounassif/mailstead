import { errorFromResponse, ApiError } from "./apiError";
import { loadSavedInstanceUrl } from "./instanceUrl";
import { clearToken, loadToken } from "./session";

let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
};

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const origin = await loadSavedInstanceUrl();
  if (!origin) {
    throw new ApiError(0, "no_instance", "Connect a Mailstead instance first.");
  }
  const headers: Record<string, string> = { Accept: "application/json" };
  const auth = options.auth !== false;
  if (auth) {
    const token = await loadToken();
    if (!token) {
      onUnauthorized?.();
      throw new ApiError(401, "unauthorized", "Sign in again.");
    }
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  let response: Response;
  try {
    response = await fetch(`${origin}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network", "Could not reach your Mailstead instance.");
  }
  if (response.status === 401 && auth) {
    await clearToken();
    onUnauthorized?.();
  }
  if (!response.ok) {
    throw await errorFromResponse(response);
  }
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export type MailboxState = {
  address: string;
  state: string;
};

export type Me = {
  username: string;
  mailbox: MailboxState | null;
  unread_count: number;
};

export type ChatRow = {
  key?: string;
  id?: number;
  title?: string;
  label?: string;
  preview?: string;
  unread?: boolean;
  count?: number;
  names?: string[];
  sort_at?: string | null;
};

export type Chats = {
  unread_count: number;
  dms: ChatRow[];
  channels: ChatRow[];
  projects: { id: number; name: string; count: number }[];
  people: { address: string; label: string }[];
};

export type ChatMessage = {
  kind: "message" | "event";
  copy_id?: number;
  who?: string;
  title?: string;
  preview?: string;
  body?: string;
  outgoing?: boolean;
  unread?: boolean;
  sort_at?: string | null;
};

export type Participant = {
  address: string;
  display_name: string;
  kind: string;
};

export type Conversation = {
  mode: string;
  conversation_id: number | null;
  label: string;
  project_id: number | null;
  dm_key: string;
  contact: string;
  subject: string;
  can_compose: boolean;
  participants: Participant[];
  known_addresses: string[];
  messages: ChatMessage[];
};

export type SendResult = {
  ok: boolean;
  conversation_id: number | null;
  dm_key: string;
  outbound_id: string;
};

export type CopySummary = {
  copy_id: number;
  folder: string;
  subject: string;
  from: string;
  to: string;
  snippet: string;
  unread: boolean;
  sort_at: string | null;
};

export type Page<T> = {
  page: number;
  pages: number;
  count: number;
  results: T[];
  q?: string;
};

export type Attachment = {
  id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  downloadable: boolean;
};

export type ThreadItem = {
  kind: "message" | "event";
  copy_id?: number;
  subject?: string;
  from?: string;
  outgoing?: boolean;
  text?: string;
  html?: string;
  is_anchor?: boolean;
  bcc?: string;
  body?: string;
  attachments?: Attachment[];
};

export type MessageDetail = {
  copy_id: number;
  folder: string;
  can_reply: boolean;
  reply_to: string;
  reply_all_to: string;
  reply_all_cc: string;
  reply_subject: string;
  thread: ThreadItem[];
};

export type DriveFile = {
  name: string;
  size: string;
  size_bytes: number;
  subject: string;
  local: boolean;
  copy_id: number;
  attachment_id: number;
};

export type ContactRow = {
  address: string;
  label: string;
  title: string;
  preview: string;
  unread: boolean;
  count: number;
  sort_at?: string | null;
};

export type Card = {
  id: number;
  title: string;
  body: string;
  updated_at: string;
};

export type VaultEntry = {
  id: number;
  label: string;
  username: string;
};

export type NotificationPrefs = {
  enabled: boolean;
  new_mail: boolean;
  preview_mode: string;
  preview_modes: string[];
  push_configured: boolean;
  expo_push_configured: boolean;
};

export type DeviceRow = {
  id: number;
  kind: "web" | "expo";
  label: string;
  created_at: string;
};
