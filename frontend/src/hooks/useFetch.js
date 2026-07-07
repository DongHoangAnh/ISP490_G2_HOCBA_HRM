/* Hook fetch dùng chung cho các panel Nghỉ phép (và về sau: toàn SPA).
   Stale-while-revalidate: có cache theo cacheKey → hiện data cũ ngay và fetch
   ngầm cập nhật; chưa có cache → loading=true (skeleton). Thay cho pattern
   data/err/tick lặp ở từng panel. Owner: Nhật Anh.
   Spec: docs/superpowers/specs/2026-07-07-timeoff-frontend-cleanup-design.md */
import { useState, useEffect, useRef, useCallback } from 'react';

/* Cache cấp module: sống trong phiên SPA, mất khi F5 (chấp nhận). */
const cache = new Map();

/* fetcher: () => Promise<payload>.
   deps: mảng dependency — đổi là fetch lại (truyền thẳng cho useEffect).
   cacheKey: chuỗi định danh cache (vd `timeoff:dashboard:2026:5`); null = không cache. */
export default function useFetch(fetcher, deps, cacheKey) {
  const [state, setState] = useState(() => {
    const hit = cacheKey != null && cache.has(cacheKey);
    return { data: hit ? cache.get(cacheKey) : null, err: null, loading: !hit };
  });
  const runId = useRef(0);           // chống race: chỉ nhận response của lần gọi mới nhất
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const keyRef = useRef(cacheKey);
  keyRef.current = cacheKey;

  const load = useCallback(() => {
    const id = ++runId.current;
    const key = keyRef.current;
    const hit = key != null && cache.has(key);
    // Có cache → hiện ngay (stale) rồi revalidate ngầm; chưa có → loading.
    setState({ data: hit ? cache.get(key) : null, err: null, loading: !hit });
    fetcherRef.current()
      .then((payload) => {
        if (id !== runId.current) return; // deps đã đổi — bỏ response cũ
        if (key != null) cache.set(key, payload);
        setState({ data: payload, err: null, loading: false });
      })
      .catch((e) => {
        if (id !== runId.current) return;
        if (hit) {
          // Đang hiện data cũ → không đè màn hình lỗi, chỉ ghi log.
          console.warn('useFetch revalidate failed:', e);
          setState((s) => ({ ...s, loading: false }));
        } else {
          setState({ data: null, err: e.message, loading: false });
        }
      });
  }, []);

  useEffect(load, deps);

  /* Action (duyệt/hủy/điều chỉnh…) ghi thẳng payload server trả về. */
  const setData = useCallback((payload) => {
    if (keyRef.current != null) cache.set(keyRef.current, payload);
    setState({ data: payload, err: null, loading: false });
  }, []);

  return { data: state.data, err: state.err, loading: state.loading, reload: load, setData };
}
