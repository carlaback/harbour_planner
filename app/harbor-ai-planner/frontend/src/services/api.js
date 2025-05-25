// src/services/api.js
import axios from 'axios';

// Behåll din befintliga api-objekt
const api = {
  // Båtar
  getBoats: (params = {}) => axios.get('/api/boats', { params }),
  getBoat: (id) => axios.get(`/api/boats/${id}`),
  createBoat: (data) => axios.post('/api/boats', data),
  updateBoat: (id, data) => axios.put(`/api/boats/${id}`, data),
  deleteBoat: (id) => axios.delete(`/api/boats/${id}`),
  
  // Platser
  getSlots: (params = {}) => axios.get('/api/slots', { params }),
  getSlot: (id) => axios.get(`/api/slots/${id}`),
  createSlot: (data) => axios.post('/api/slots', data),
  updateSlot: (id, data) => axios.put(`/api/slots/${id}`, data),
  deleteSlot: (id) => axios.delete(`/api/slots/${id}`),
  
  // Bryggor
  getDocks: (params = {}) => axios.get('/api/docks', { params }),
  
  // Strategier och optimering
  getStrategies: () => axios.get('/api/strategies'),
  runOptimization: (strategy_names, run_in_background = false) => 
    axios.post('/api/optimize', null, { params: { strategy_names, run_in_background } }),
  getOptimizationResult: (jobId) => axios.get(`/api/optimize/${jobId}`),
  
  // Testdata
  createTestData: (params = {}) => axios.post('/api/test-data', null, { params })
};

// Exportera dessa separata funktioner för att matcha dina imports i Visualization.jsx
// Dessa fungerar som alias till dina befintliga api-funktioner
export const fetchAllSlots = () => api.getSlots();
export const fetchAllDocks = () => api.getDocks();
export const updateSlotStatus = (id, status) => api.updateSlot(id, { status });

// Fortfarande exportera hela api-objektet som default
export default api;