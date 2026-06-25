"use client";

import { Region } from "./types";

const KEY = "gtt_session";

export interface Session {
  username: string;
  region: Region;
  id: string;
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function setSession(session: Session) {
  window.localStorage.setItem(KEY, JSON.stringify(session));
}

export function clearSession() {
  window.localStorage.removeItem(KEY);
}

export function createSession(username: string, region: Region): Session {
  const session: Session = { username, region, id: `u-${Date.now()}` };
  setSession(session);
  return session;
}
