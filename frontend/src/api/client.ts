import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add Telegram auth to all requests
api.interceptors.request.use((config) => {
  if (window.Telegram?.WebApp?.initData) {
    config.headers.Authorization = `tma ${window.Telegram.WebApp.initData}`
  }
  return config
})

// API methods
export const apiClient = {
  // User & Portfolio
  getProfile: () => api.get('/api/user/profile'),
  getPositions: () => api.get('/api/portfolio/positions'),
  
  // Market
  getStocks: (limit = 50) => api.get(`/api/market/stocks?limit=${limit}`),
  getStockDetail: (ticker: string) => api.get(`/api/market/stock/${ticker}`),
  getStockHistory: (ticker: string, days = 365) => 
    api.get(`/api/market/stock/${ticker}/history?days=${days}`),
  
  // Trading
  executeTrade: (data: { ticker: string; side: string; shares: number; currency: string }) =>
    api.post('/api/trade/execute', data),
  getOrders: (limit = 50) => api.get(`/api/trading/orders?limit=${limit}`),
  getTransactions: (limit = 50) => api.get(`/api/trading/transactions?limit=${limit}`),
  
  // Watchlist
  getWatchlist: () => api.get('/api/watchlist'),
  addToWatchlist: (ticker: string) => api.post('/api/watchlist/add', { ticker }),
  removeFromWatchlist: (ticker: string) => api.delete(`/api/watchlist/remove/${ticker}`),
  
  // Learning
  getLearningModules: () => api.get('/api/learning/modules'),
  submitQuiz: (moduleId: number, answers: number[]) =>
    api.post('/api/learning/quiz/submit', { module_id: moduleId, answers }),
  
  // Leaderboard & Duels
  getGlobalLeaderboard: (limit = 50) => api.get(`/api/leaderboard/global?limit=${limit}`),
  getActiveDuels: () => api.get('/api/duels/active'),
  getDuelLeaderboard: (duelId: number) => api.get(`/api/duels/${duelId}/leaderboard`),
  joinDuel: (duelId: number) => api.post(`/api/duels/${duelId}/join`),
}

export default api
