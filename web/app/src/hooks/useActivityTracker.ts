import { useEffect, useRef, useCallback } from 'react';

const IDLE_TIMEOUT_MS = 30 * 60 * 1000;  // 30 min
const CHECK_INTERVAL_MS = 60 * 1000;      // 1 min
const REFRESH_THRESHOLD_MS = 5 * 60 * 1000; // refresh when < 5 min left
const ACTIVITY_GRACE_MS = 2 * 60 * 1000;   // consider "active" if activity in last 2 min

export function useActivityTracker(
  isActive: boolean,
  onIdle: () => void,
  onRefresh: () => Promise<boolean>,
) {
  const lastActivityRef = useRef<number>(Date.now());
  const checkIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const updateActivity = useCallback(() => {
    if (isActive) lastActivityRef.current = Date.now();
  }, [isActive]);

  useEffect(() => {
    if (!isActive) return;

    const events = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    const throttled = (() => {
      let last = 0;
      return () => {
        const now = Date.now();
        if (now - last > 1000) {
          last = now;
          updateActivity();
        }
      };
    })();

    events.forEach((e) => window.addEventListener(e, throttled));
    return () => events.forEach((e) => window.removeEventListener(e, throttled));
  }, [isActive, updateActivity]);

  useEffect(() => {
    if (!isActive) return;

    checkIntervalRef.current = setInterval(async () => {
      const now = Date.now();
      const idle = now - lastActivityRef.current;
      const token = localStorage.getItem('holkos_token');
      if (!token) return;

      let tokenExp = 0;
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        tokenExp = payload?.exp ? payload.exp * 1000 : 0;
      } catch {
        onIdle();
        return;
      }

      const msUntilExpiry = tokenExp - now;
      const wasActiveRecently = idle < ACTIVITY_GRACE_MS;

      if (idle > IDLE_TIMEOUT_MS || msUntilExpiry < 0) {
        onIdle();
        return;
      }

      if (wasActiveRecently && msUntilExpiry < REFRESH_THRESHOLD_MS) {
        const ok = await onRefresh();
        if (!ok) onIdle();
      }
    }, CHECK_INTERVAL_MS);

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
    };
  }, [isActive, onIdle, onRefresh]);
}
