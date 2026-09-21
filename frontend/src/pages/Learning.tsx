import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { BookOpen, Trophy, CheckCircle, Circle } from 'lucide-react'

const Learning = () => {
  const { data: modulesData, isLoading } = useQuery({
    queryKey: ['learning-modules'],
    queryFn: async () => {
      const res = await apiClient.getLearningModules()
      return res.data
    },
  })

  const { data: profile } = useQuery({
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

  const modules = modulesData?.modules || []
  const user = profile?.user

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 animate-slide-in">
      {/* Header */}
      <div className="bg-dark-surface rounded-lg p-6 border border-dark-border">
        <h1 className="text-2xl font-bold mb-4 text-gold">Обучение</h1>
        
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-400 mb-1">Прогресс</p>
            <p className="text-2xl font-bold">{user?.learning_progress || 0}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-1">Уровень</p>
            <p className="text-2xl font-bold">{user?.level || 1}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-1">XP</p>
            <p className="text-2xl font-bold">{user?.xp || 0}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-dark-elevated rounded-full h-2 overflow-hidden">
            <div
              className="bg-gold h-full transition-all duration-500"
              style={{ width: `${user?.learning_progress || 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* Modules */}
      <div className="space-y-3">
        {modules.map((module: any) => (
          <div
            key={module.id}
            className={`bg-dark-surface rounded-lg p-5 border transition-all ${
              module.completed
                ? 'border-success'
                : 'border-dark-border hover:border-gold'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-1">
                {module.completed ? (
                  <CheckCircle size={24} className="text-success" />
                ) : (
                  <Circle size={24} className="text-gray-400" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-bold text-lg">
                    {module.order}. {module.title}
                  </h3>
                  <span className="text-sm text-gold font-semibold flex-shrink-0 ml-2">
                    +{module.xp_reward} XP
                  </span>
                </div>
                
                <p className="text-sm text-gray-400 mb-3">{module.description}</p>
                
                <div className="flex items-center gap-2">
                  {module.quiz && (
                    <span className="text-xs bg-dark-elevated px-2 py-1 rounded">
                      📝 Квиз
                    </span>
                  )}
                  {module.practical_task && (
                    <span className="text-xs bg-dark-elevated px-2 py-1 rounded">
                      💼 Практика
                    </span>
                  )}
                  {module.completed && (
                    <span className="text-xs bg-success/20 text-success px-2 py-1 rounded">
                      ✓ Пройдено
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info Note */}
      <div className="bg-dark-elevated rounded-lg p-4 border border-dark-border">
        <p className="text-sm text-gray-400 text-center">
          💡 Открывайте модули в Telegram-боте для изучения материала и прохождения квизов
        </p>
      </div>
    </div>
  )
}

export default Learning
