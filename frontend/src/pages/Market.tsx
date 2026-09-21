import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import { Search, TrendingUp, TrendingDown, Star } from 'lucide-react'

const Market = () => {
  const [searchQuery, setSearchQuery] = useState('')

  const { data: stocksData, isLoading } = useQuery({
    queryKey: ['stocks'],
    queryFn: async () => {
      const res = await apiClient.getStocks(50)
      return res.data
    },
  })

  const stocks = stocksData?.stocks || []
  const filteredStocks = stocks.filter((stock: any) =>
    stock.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
    stock.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-400">Загрузка рынка...</div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 animate-slide-in">
      {/* Header */}
      <div className="bg-dark-surface rounded-lg p-6 border border-dark-border">
        <h1 className="text-2xl font-bold mb-4 text-gold">Рынок MOEX</h1>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Поиск акций..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-dark-elevated border border-dark-border rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-gold transition-colors"
          />
        </div>
      </div>

      {/* Stocks List */}
      <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
        <div className="p-4 border-b border-dark-border">
          <h2 className="font-semibold">Популярные акции</h2>
        </div>
        
        <div className="divide-y divide-dark-border">
          {filteredStocks.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              <p>Акции не найдены</p>
            </div>
          ) : (
            filteredStocks.map((stock: any) => (
              <Link
                key={stock.ticker}
                to={`/stock/${stock.ticker}`}
                className="block p-4 hover:bg-dark-elevated transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-10 h-10 bg-dark-elevated rounded-lg flex items-center justify-center">
                      <span className="font-bold text-gold text-sm">{stock.ticker.slice(0, 2)}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold">{stock.ticker}</h3>
                      <p className="text-sm text-gray-400 truncate">{stock.name}</p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className="font-semibold">{stock.price.toFixed(2)} {stock.currency}</p>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default Market
