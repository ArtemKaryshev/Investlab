import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { Trophy, Medal, Award } from 'lucide-react'

const Leaderboard = () => {
  const { data: leaderboardData, isLoading } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: async () => {
      const res = await apiClient.getGlobalLeaderboard(50)
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

  const leaderboard = leaderboardData?.leaderboard || []

  const getMedalIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Medal size={24} className="text-gold" />
      case 2:
        return <Medal size={24} className="text-gray-400" />
      case 3:
        return <Medal size={24} className="text-amber-700" />
      default:
        return <span className="text-gray-400 font-semibold">{rank}</span>
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 animate-slide-in">
      {/* Header */}
      <div className="bg-dark-surface rounded-lg p-6 border border-dark-border">
        <h1 className="text-2xl font-bold mb-2 text-gold flex items-center gap-2">
          <Trophy size={28} />
          Лидерборд
        </h1>
        <p className="text-sm text-gray-400">
          Топ инвесторов по общей стоимости портфеля
        </p>
      </div>

      {/* Top 3 Podium */}
      {leaderboard.length >= 3 && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          {/* Second Place */}
          <div className="bg-dark-surface rounded-lg p-4 border border-gray-400 flex flex-col items-center justify-end">
            <Medal size={32} className="text-gray-400 mb-2" />
            <p className="font-bold truncate w-full text-center text-sm">
              {leaderboard[1].username}
            </p>
            <p className="text-xs text-gray-400">Уровень {leaderboard[1].level}</p>
            <p className="text-sm font-semibold mt-1">
              ₽{(leaderboard[1].total_value_rub / 1000000).toFixed(1)}M
            </p>
            <div className="mt-2 text-2xl font-bold text-gray-400">2</div>
          </div>

          {/* First Place */}
          <div className="bg-dark-surface rounded-lg p-4 border-2 border-gold flex flex-col items-center">
            <Trophy size={40} className="text-gold mb-2" />
            <p className="font-bold truncate w-full text-center">
              {leaderboard[0].username}
            </p>
            <p className="text-xs text-gray-400">Уровень {leaderboard[0].level}</p>
            <p className="font-semibold mt-1 text-gold">
              ₽{(leaderboard[0].total_value_rub / 1000000).toFixed(1)}M
            </p>
            <div className="mt-2 text-3xl font-bold text-gold">1</div>
          </div>

          {/* Third Place */}
          <div className="bg-dark-surface rounded-lg p-4 border border-amber-700 flex flex-col items-center justify-end">
            <Medal size={32} className="text-amber-700 mb-2" />
            <p className="font-bold truncate w-full text-center text-sm">
              {leaderboard[2].username}
            </p>
            <p className="text-xs text-gray-400">Уровень {leaderboard[2].level}</p>
            <p className="text-sm font-semibold mt-1">
              ₽{(leaderboard[2].total_value_rub / 1000000).toFixed(1)}M
            </p>
            <div className="mt-2 text-2xl font-bold text-amber-700">3</div>
          </div>
        </div>
      )}

      {/* Full Leaderboard */}
      <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
        <div className="divide-y divide-dark-border">
          {leaderboard.map((entry: any) => (
            <div
              key={entry.user_id}
              className={`p-4 flex items-center gap-4 ${
                entry.rank <= 3 ? 'bg-dark-elevated' : 'hover:bg-dark-elevated'
              } transition-colors`}
            >
              <div className="w-10 flex items-center justify-center">
                {getMedalIcon(entry.rank)}
              </div>
              
              <div className="flex-1 min-w-0">
                <h3 className="font-bold truncate">{entry.username}</h3>
                <div className="flex items-center gap-3 text-sm text-gray-400">
                  <span>Уровень {entry.level}</span>
                  <span>•</span>
                  <span>{entry.xp} XP</span>
                  <span>•</span>
                  <span>{entry.learning_progress}% обучения</span>
                </div>
              </div>
              
              <div className="text-right">
                <p className="font-bold">
                  ₽{entry.total_value_rub.toLocaleString('ru-RU', { maximumFractionDigits: 0 })}
                </p>
                <p className="text-sm text-gray-400">
                  ${entry.total_value_usd.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Leaderboard
