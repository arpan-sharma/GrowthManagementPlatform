const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const AUTH = `${API_BASE}/api/v1/institutions/auth`;

export type AuthUser = {
  id: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  contact_number: string;
  role: string;
  institution_id: string;
  must_change_password: boolean;
};

export type AuthSession = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
};

export function userDisplayName(user: AuthUser) {
  return `${user.first_name} ${user.last_name}`.trim();
}

export function saveSession(session: AuthSession) {
  sessionStorage.setItem("access_token", session.access_token);
  sessionStorage.setItem("auth_user", JSON.stringify(session.user));
}

export function authHeaders(): HeadersInit {
  const token = sessionStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function postAuth(path: string, body: object): Promise<AuthSession> {
  const response = await fetch(`${AUTH}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.error?.message ?? "Sign in failed.");
  }
  saveSession(data);
  return data;
}

export function loginHeadTeacher(email: string, password: string) {
  return postAuth("/login", { email, password });
}

export function loginStudent(institutionCode: string, rollNumber: string, password: string) {
  return postAuth("/student/login", {
    institution_code: institutionCode,
    roll_number: rollNumber,
    password,
  });
}

export function fetchMe() {
  return fetch(`${AUTH}/me`, { headers: authHeaders() });
}
