import { poiName, hotelName, restName } from '../data/seeds';

export function labelFor(kind, id, showNames) {
  const sid = String(id ?? '');
  if (!showNames) return sid;

  const map =
    kind === 'poi' ? poiName :
    kind === 'hotel' ? hotelName :
    restName;

  const nm = map[sid];
  return nm ? `${nm} (${sid})` : sid;
}

