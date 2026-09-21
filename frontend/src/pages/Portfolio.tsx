import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { TrendingUp, TrendingDown, DollarSign, Wallet } from 'lucide-react'

const Portfolio = () => {
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const res = await apiClient.getProfile()
      return res.data
    },
  })

  const { data: positionsData, isLoading: positionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const res = await apiClient.getPositions()
      return res.data
    },
  })

  if (profileLoading || positionsLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-400">Загрузка...</div>
      </div>
    )
  }

  const positions = positionsData?.positions || []
  const portfolio = profile?.portfolio || {}
  const balances = profile?.balances || {}

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 animate-slide-in">
      {/* Header */}
      <div className="bg-dark-surface rounded-lg p-6 border border-dark-border">
        <h1 className="text-2xl font-bold mb-4 text-gold">Ваш портфель</h1>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400 mb-1">Общая стоимость ₽</p>
            <p className="text-2xl font-bold">
              ₽{portfolio.total_value_rub?.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-1">Общая стоимость $</p>
            <p className="text-2xl font-bold">
              ${portfolio.total_value_usd?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
        </div>
      </div>

      {/* Cash Balance */}
      <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
        <div className="flex items-center gap-2 mb-3">
          <Wallet size={20} className="text-gold" />
          <h2 className="font-semibold">Наличные</h2>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2">
            <DollarSign size={16} className="text-gray-400" />
            <span className="text-lg">${balances.usd?.toLocaleString('en-US')}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">₽</span>
            <span className="text-lg">₽{balances.rub?.toLocaleString('ru-RU')}</span>
          </div>
        </div>
      </div>

      {/* Positions */}
      <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
        <div className="p-4 border-b border-dark-border">
          <h2 className="font-semibold">Позиции</h2>
        </div>
        
        {positions.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <p>У вас пока нет позиций</p>
            <p className="text-sm mt-2">Начните торговать на вкладке "Рынок"</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {positions.map((position: any) => {
              const isProfit = position.profit > 0
              return (
                <div key={position.ticker} className="p-4 hover:bg-dark-elevated transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-bold text-lg">{position.ticker}</h3>
                      <p className="text-sm text-gray-400">{position.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">
                        {position.current_price.toFixed(2)} {position.currency}
                      </p>
                      <p className={`text-sm flex items-center gap-1 ${isProfit ? 'text-success' : 'text-danger'}`}>
                        {isProfit ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {position.change_pct > 0 ? '+' : ''}{position.change_pct.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-gray-400">Акций</p>
                      <p className="font-semibold">{position.shares}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Стоимость</p>
                      <p className="font-semibold">
                        {position.position_value.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">P&L</p>
                      <p className={`font-semibold ${isProfit ? 'text-success' : 'text-danger'}`}>
                        {position.profit > 0 ? '+' : ''}{position.profit.toFixed(0)} ({position.profit_pct > 0 ? '+' : ''}{position.profit_pct.toFixed(1)}%)
                      </p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default Portfolio
