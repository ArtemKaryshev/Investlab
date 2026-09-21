import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { ArrowLeft, TrendingUp, TrendingDown, ShoppingCart, DollarSign } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const StockDetail = () => {
  const { ticker } = useParams<{ ticker: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [tradeMode, setTradeMode] = useState<'buy' | 'sell'>('buy')
  const [shares, setShares] = useState<string>('1')
  const [currency, setCurrency] = useState<'RUB' | 'USD'>('RUB')

  const { data: stockData, isLoading: stockLoading } = useQuery({
    queryKey: ['stock', ticker],
    queryFn: async () => {
      const res = await apiClient.getStockDetail(ticker!)
      return res.data
    },
  })

  const { data: historyData } = useQuery({
    queryKey: ['stock-history', ticker],
    queryFn: async () => {
      const res = await apiClient.getStockHistory(ticker!, 30)
      return res.data
    },
  })

  const tradeMutation = useMutation({
    mutationFn: (data: any) => apiClient.executeTrade(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      alert('Сделка успешно выполнена!')
      setShares('1')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Ошибка выполнения сделки')
    },
  })

  if (stockLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-400">Загрузка...</div>
      </div>
    )
  }

  const stock = stockData?.stock
  if (!stock) {
    return <div className="p-4">Акция не найдена</div>
  }

  const handleTrade = () => {
    const sharesNum = parseFloat(shares)
    if (isNaN(sharesNum) || sharesNum <= 0) {
      alert('Введите корректное количество акций')
      return
    }

    tradeMutation.mutate({
      ticker: ticker!,
      side: tradeMode,
      shares: sharesNum,
      currency: currency,
    })
  }

  const history = historyData?.history || []
  const chartData = history.map((item: any) => ({
    date: item.date,
    price: item.close,
  }))

  const isPositive = stock.change_pct >= 0

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 animate-slide-in">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-dark-surface rounded-lg transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-2xl font-bold text-gold">{ticker}</h1>
      </div>

      {/* Price Card */}
      <div className="bg-dark-surface rounded-lg p-6 border border-dark-border">
        <p className="text-sm text-gray-400 mb-2">{stock.name}</p>
        <div className="flex items-end gap-3 mb-4">
          <p className="text-4xl font-bold">{stock.price.toFixed(2)}</p>
          <p className="text-xl text-gray-400">{stock.currency}</p>
        </div>
        
        <div className={`flex items-center gap-2 ${isPositive ? 'text-success' : 'text-danger'}`}>
          {isPositive ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
          <span className="text-lg font-semibold">
            {stock.change_pct > 0 ? '+' : ''}{stock.change_pct.toFixed(2)}%
          </span>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-dark-border text-sm">
          <div>
            <p className="text-gray-400">Открытие</p>
            <p className="font-semibold">{stock.open.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-gray-400">Максимум</p>
            <p className="font-semibold">{stock.high.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-gray-400">Минимум</p>
            <p className="font-semibold">{stock.low.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-gray-400">Объём</p>
            <p className="font-semibold">{(stock.volume / 1000).toFixed(0)}K</p>
          </div>
        </div>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h2 className="font-semibold mb-4">График (30 дней)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" hide />
              <YAxis domain={['auto', 'auto']} hide />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1E222E',
                  border: '1px solid #2A2E3A',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#9CA3AF' }}
              />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#FBBF24"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Trading Panel */}
      <div className="bg-dark-surface rounded-lg p-6 border border-dark-border">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <ShoppingCart size={20} className="text-gold" />
          Торговля
        </h2>

        {/* Buy/Sell Toggle */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setTradeMode('buy')}
            className={`flex-1 py-3 rounded-lg font-semibold transition-colors ${
              tradeMode === 'buy'
                ? 'bg-success text-white'
                : 'bg-dark-elevated text-gray-400'
            }`}
          >
            Купить
          </button>
          <button
            onClick={() => setTradeMode('sell')}
            className={`flex-1 py-3 rounded-lg font-semibold transition-colors ${
              tradeMode === 'sell'
                ? 'bg-danger text-white'
                : 'bg-dark-elevated text-gray-400'
            }`}
          >
            Продать
          </button>
        </div>

        {/* Shares Input */}
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">Количество акций</label>
          <input
            type="number"
            min="1"
            step="1"
            value={shares}
            onChange={(e) => setShares(e.target.value)}
            className="w-full bg-dark-elevated border border-dark-border rounded-lg px-4 py-3 text-white focus:outline-none focus:border-gold transition-colors"
          />
        </div>

        {/* Currency Toggle */}
        <div className="mb-4">
          <label className="block text-sm text-gray-400 mb-2">Валюта</label>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrency('RUB')}
              className={`flex-1 py-2 rounded-lg font-semibold transition-colors ${
                currency === 'RUB'
                  ? 'bg-gold text-dark-bg'
                  : 'bg-dark-elevated text-gray-400'
              }`}
            >
              ₽ RUB
            </button>
            <button
              onClick={() => setCurrency('USD')}
              className={`flex-1 py-2 rounded-lg font-semibold transition-colors ${
                currency === 'USD'
                  ? 'bg-gold text-dark-bg'
                  : 'bg-dark-elevated text-gray-400'
              }`}
            >
              $ USD
            </button>
          </div>
        </div>

        {/* Total */}
        <div className="bg-dark-elevated rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Итого:</span>
            <span className="text-xl font-bold">
              {(stock.price * parseFloat(shares || '0')).toFixed(2)} {currency}
            </span>
          </div>
        </div>

        {/* Execute Button */}
        <button
          onClick={handleTrade}
          disabled={tradeMutation.isPending}
          className={`w-full py-4 rounded-lg font-bold transition-colors ${
            tradeMode === 'buy'
              ? 'bg-success hover:bg-green-600'
              : 'bg-danger hover:bg-red-600'
          } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {tradeMutation.isPending ? 'Выполнение...' : tradeMode === 'buy' ? 'Купить' : 'Продать'}
        </button>
      </div>
    </div>
  )
}

export default StockDetail
