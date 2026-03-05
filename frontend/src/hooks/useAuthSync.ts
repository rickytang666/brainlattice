import { useEffect } from "react";
import { useSafeAuth } from "./useSafeAuth";
import { API_BASE, SESSION_ID_KEY, apiFetch } from "../config";

export function useAuthSync() {
  const { userId, isLoaded } = useSafeAuth();

  useEffect(() => {
    if (!isLoaded || !userId) return;

    const oldSessionId = localStorage.getItem(SESSION_ID_KEY);
    // if we have an anonymous session and it's different from the clerk user id
    if (oldSessionId && oldSessionId !== userId) {
      console.log(`[useAuthSync] migrating anonymous projects from ${oldSessionId} to ${userId}`);
      
      apiFetch(`${API_BASE}/project/transfer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_id: oldSessionId, target_id: userId })
      }, userId)
      .then(res => {
        if (res.ok) {
          console.log("[useAuthSync] migration complete, clearing anonymous session map.");
          localStorage.removeItem(SESSION_ID_KEY);
        } else {
          console.error("[useAuthSync] migration request returned non-ok status.");
        }
      })
      .catch(err => console.error("[useAuthSync] migration failed:", err));
    }
  }, [isLoaded, userId]);
}
