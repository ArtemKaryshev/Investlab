import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { User, Award, TrendingUp, BookOpen, Clock } from 'lucide-react'

const Profile = () => {
  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const res = await apiClient.getProfile()
      return res.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-400">Загрузка...</div>
      </div>
    )
  }

  const user = profile?.user
  const portfolio = profile?.portfolio

  const categoryLabels: Record<string, string> = {
    conservative: 'Консервативный',
    moderate: 'Умеренный',
    aggressive: 'Агрессивный',
  }

  const categoryEmojis: Record<string, string> = {
    conservative: '🛡',
    moderate: '⚖️',
    aggressive: '🚀',
  }

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 animate-slide-in">
      {/* Profile Header */}
      <div className="bg-dark-surface rounded-lg p-6 border border-dark-border">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 bg-gold rounded-full flex items-center justify-center">
            <User size={32} className="text-dark-bg" />
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">{user?.first_name || 'Инвестор'}</h1>
            {user?.username && (
              <p className="text-gray-400">@{user.username}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-dark-border">
          <div>
            <p className="text-sm text-gray-400 mb-1">Категория</p>
            <p className="font-semibold flex items-center gap-2">
              <span>{categoryEmojis[user?.investor_category]}</span>
              {categoryLabels[user?.investor_category]}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-1">Уровень</p>
            <p className="text-2xl font-bold text-gold">{user?.level}</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={20} className="text-gold" />
            <p className="text-sm text-gray-400">Опыт (XP)</p>
          </div>
          <p className="text-2xl font-bold">{user?.xp}</p>
        </div>

        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen size={20} className="text-gold" />
            <p className="text-sm text-gray-400">Прогресс</p>
          </div>
          <p className="text-2xl font-bold">{user?.learning_progress}%</p>
        </div>

        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={20} className="text-gold" />
            <p className="text-sm text-gray-400">Стрик</p>
          </div>
          <p className="text-2xl font-bold">{user?.streak_days} дней</p>
        </div>

        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <div className="flex items-center gap-2 mb-2">
            <Award size={20} className="text-gold" />
            <p className="text-sm text-gray-400">Достижения</p>
          </div>
          <p className="text-2xl font-bold">{user?.achievements?.length || 0}</p>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="bg-dark-surface rounded-lg p-5 border border-dark-border">
        <h2 className="font-semibold mb-4">Сводка портфеля</h2>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Общая стоимость ₽</span>
            <span className="font-bold text-lg">
              ₽{portfolio?.total_value_rub?.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Общая стоимость $</span>
            <span className="font-bold text-lg">
              ${portfolio?.total_value_usd?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </span>
          </div>
          <div className="flex justify-between items-center pt-3 border-t border-dark-border">
            <span className="text-gray-400">Позиции ₽</span>
            <span className="font-semibold text-gold">
              ₽{portfolio?.positions_value_rub?.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Позиции $</span>
            <span className="font-semibold text-gold">
              ${portfolio?.positions_value_usd?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </span>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-dark-elevated rounded-lg p-4 border border-dark-border">
        <p className="text-xs text-gray-400 text-center leading-relaxed">
          ⚠️ <b>Дисклеймер:</b> InvestLab — виртуальный симулятор для обучения. 
          Все операции проводятся с виртуальными средствами. Данные не являются 
          инвестиционной рекомендацией.
        </p>
      </div>
    </div>
  )
}

export default Profile
