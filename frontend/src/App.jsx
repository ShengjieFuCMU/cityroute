// frontend/src/App.jsx
import { useState } from 'react';
import { generateItinerary, autoPickMeals, getDay, exportItinerary } from './api';
import TripSettings from './TripSettings';
import { labelFor } from './utils/display';
import { defaultUi } from './state/uiPrefs';

// Safe defaults for A) POI selection controls
const defaultPrefs = {
  only_must_go: false,
  max_pois_total: 40,
};

export default function App() {
  // Basic trip inputs
  const [city, setCity] = useState('Pittsburgh');
  const [days, setDays] = useState(3);
  const [detour, setDetour] = useState(15);
  const [diet, setDiet] = useState('');   // e.g., vegetarian|vegan
  const [price, setPrice] = useState(''); // $, $$, $$$

  // Itinerary/result state
  const [itId, setItId] = useState('');
  const [dayIds, setDayIds] = useState([]);
  const [hotel, setHotel] = useState('');
  const [daysData, setDaysData] = useState({}); // { dayId: { visit_ids:[], lunch_id, dinner_id, total_time_minutes } }

  // UX state
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  // A) TripSettings prefs (only_must_go, max_pois_total)
  const [prefs, setPrefs] = useState(defaultPrefs);

  // B) UI pref: show names next to IDs
  const [ui, setUi] = useState(defaultUi); // { showNames: true }

  // Build backend prefs
  const buildPrefs = () => {
    const p = {
      days: Number(days),
      travel_mode: 'drive',
      detour_limit_minutes: Number(detour),
      ...prefs, // merge only_must_go, max_pois_total
    };
    if (diet.trim()) {
      p.diet_tags = diet.split('|').map(s => s.trim()).filter(Boolean);
    }
    if (price) p.price_range = price;
    return p;
    // NOTE: We keep API payload IDs-only; names are shown via labelFor(...) purely in UI.
  };

  async function onGenerate() {
    setBusy(true);
    setMsg('');
    try {
      const payload = {
        city,
        prefs: buildPrefs(),
        // (future) pois, hotels, restaurants, locks ...
      };
      const res = await generateItinerary(payload);
      setItId(res.itinerary_id);
      setDayIds(res.day_ids || []);
      setHotel(res.hotel_id || '');
      setDaysData({});
      setMsg('Generated.');
    } catch (e) {
      const errMsg = e?.response?.data?.detail || e.message;
      setMsg('Generate failed: ' + errMsg);
    } finally {
      setBusy(false);
    }
  }

  async function onAutoPick() {
    if (!itId) return setMsg('Generate first.');
    setBusy(true);
    setMsg('');
    try {
      const r = await autoPickMeals(itId, { detour_limit_min: Number(detour) });
      const next = { ...daysData };
      for (const d of (r.days || [])) {
        next[d.id] = await getDay(d.id);
      }
      setDaysData(next);
      setMsg('Auto-picked meals.');
    } catch (e) {
      const errMsg = e?.response?.data?.detail || e.message;
      setMsg('Auto-Pick failed: ' + errMsg);
    } finally {
      setBusy(false);
    }
  }

  async function onExport(format) {
    if (!itId) return setMsg('Generate first.');
    setBusy(true);
    setMsg('');
    try {
      const data = await exportItinerary(itId, format);
      const blob = new Blob(
        [format === 'csv' ? (data.csv_text || '') : JSON.stringify(data, null, 2)],
        { type: format === 'csv' ? 'text/csv' : 'application/json' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = format === 'csv' ? (data.filename || `${itId}_days.csv`) : `${itId}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setMsg(`Exported ${format.toUpperCase()}.`);
    } catch (e) {
      const errMsg = e?.response?.data?.detail || e.message;
      setMsg('Export failed: ' + errMsg);
    } finally {
      setBusy(false);
    }
  }

  const isErrorMsg =
    msg.startsWith('Generate failed') ||
    msg.startsWith('Auto-Pick failed') ||
    msg.startsWith('Export failed');

  return (
    <div style={{ fontFamily: 'system-ui', padding: 16, maxWidth: 900, margin: '0 auto' }}>
      <h1>CityRoute (Thin Demo)</h1>

      {/* Basic trip inputs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, minmax(120px,1fr))', gap: 12 }}>
        <label>City
          <input value={city} onChange={e => setCity(e.target.value)} />
        </label>
        <label>Days
          <input type="number" min={1} max={14} value={days} onChange={e => setDays(e.target.value)} />
        </label>
        <label>Detour (min)
          <input type="number" value={detour} onChange={e => setDetour(e.target.value)} />
        </label>
        <label>Diet tags
          <input placeholder="vegetarian|vegan" value={diet} onChange={e => setDiet(e.target.value)} />
        </label>
        <label>Price
          <select value={price} onChange={e => setPrice(e.target.value)}>
            <option value="">(any)</option>
            <option>$</option>
            <option>$$</option>
            <option>$$$</option>
          </select>
        </label>

        {/* B) Show names toggle */}
        <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <input
            type="checkbox"
            checked={ui.showNames}
            onChange={e => setUi(u => ({ ...u, showNames: e.target.checked }))}
          />
          Show names
        </label>
      </div>

      {/* A) POI selection controls */}
      <div style={{ marginTop: 12 }}>
        <TripSettings prefs={prefs} setPrefs={setPrefs} />
      </div>

      {/* Actions */}
      <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button disabled={busy} onClick={onGenerate}>Generate</button>
        <button disabled={busy || !itId} onClick={onAutoPick}>Auto-Pick Meals</button>
        <button disabled={busy || !itId} onClick={() => onExport('json')}>Export JSON</button>
        <button disabled={busy || !itId} onClick={() => onExport('csv')}>Export CSV</button>
      </div>

      {/* Status */}
      <div style={{ marginTop: 8, color: isErrorMsg ? '#a00' : '#0a0' }}>{msg}</div>

      <hr />

      {/* Summary header */}
      <div>
        <b>Itinerary:</b> {itId || '—'}
        &nbsp; <b>Hotel:</b> {hotel ? labelFor('hotel', hotel, ui.showNames) : '—'}
      </div>

      <div style={{ marginTop: 8 }}><b>Days:</b> {dayIds.length ? dayIds.join(', ') : '—'}</div>

      {/* Day cards */}
      <div style={{ marginTop: 12 }}>
        {dayIds.map(id => (
          <div key={id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 10, marginBottom: 8 }}>
            <b>{id}</b>
            <div style={{ marginTop: 6 }}>
              {Array.isArray(daysData[id]?.visit_ids)
                ? daysData[id].visit_ids
                    .map(pid => labelFor('poi', pid, ui.showNames))
                    .join(' → ')
                : '(no details yet — run Auto-Pick then revisit)'}
            </div>
            <div style={{ marginTop: 6 }}>
              Lunch: {daysData[id]?.lunch_id ? labelFor('restaurant', daysData[id].lunch_id, ui.showNames) : '—'}
              &nbsp; Dinner: {daysData[id]?.dinner_id ? labelFor('restaurant', daysData[id].dinner_id, ui.showNames) : '—'}
            </div>
            <div style={{ marginTop: 6 }}>
              Total: {daysData[id]?.total_time_minutes ?? '—'} min
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

