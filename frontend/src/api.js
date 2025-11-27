import axios from 'axios';
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' }
});
export const generateItinerary = (p)=>API.post('/itinerary/generate', p).then(r=>r.data);
export const autoPickMeals = (id,opts={})=>API.post('/restaurants/auto_pick',{itinerary_id:id,...opts}).then(r=>r.data);
export const getDay = (id)=>API.get(`/days/${id}`).then(r=>r.data);
export const exportItinerary = (id,format='json')=>API.post('/export',{itinerary_id:id,format}).then(r=>r.data);

