import { useCallback } from 'react';

/**
 * Props:
 *  - prefs: { only_must_go?: boolean, max_pois_total?: number }
 *  - setPrefs: fn(updater)
 */
export default function TripSettings({ prefs, setPrefs }) {
  // clamp to [1, 40], and coerce to int
  const clampTotal = useCallback((n) => {
    const x = Number.isFinite(n) ? Math.floor(n) : 40;
    return Math.max(1, Math.min(40, x));
  }, []);

  return (
    <div className="trip-settings" style={{display:'grid', gap:'8px', padding:'8px', border:'1px solid #ddd', borderRadius:8}}>
      <h3 style={{margin:'0 0 4px'}}>Trip settings</h3>

      <label style={{display:'flex', gap:8, alignItems:'center'}}>
        <input
          type="checkbox"
          checked={!!(prefs.only_must_go)}
          onChange={(e) => setPrefs(p => ({ ...p, only_must_go: e.target.checked }))}
        />
        <span>Only must-go POIs</span>
      </label>

      <label style={{display:'flex', gap:8, alignItems:'center'}}>
        <span>Max POIs total</span>
        <input
          type="number"
          min={1}
          max={40}
          value={prefs.max_pois_total ?? 40}
          onChange={(e) => {
            const raw = Number(e.target.value);
            setPrefs(p => ({ ...p, max_pois_total: clampTotal(raw) }));
          }}
          onBlur={(e) => {
            // normalize on blur too
            const raw = Number(e.target.value);
            const clamped = clampTotal(raw);
            if (String(raw) !== String(clamped)) e.target.value = String(clamped);
          }}
          style={{width:90}}
        />
      </label>

      <small style={{color:'#555'}}>
        Validation: 1–40. Backend may still trim; you’ll see a warning below if that happens.
      </small>
    </div>
  );
}

