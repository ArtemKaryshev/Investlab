import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutGrid, TrendingUp, BookOpen, Trophy, User } from 'lucide-react'

const Navigation = () => {
  const location = useLocation()
  
  const navItems = [
    { path: '/portfolio', icon: LayoutGrid, label: 'Портфель' },
    { path: '/market', icon: TrendingUp, label: 'Рынок' },
    { path: '/learning', icon: BookOpen, label: 'Обучение' },
    { path: '/leaderboard', icon: Trophy, label: 'Рейтинг' },
    { path: '/profile', icon: User, label: 'Профиль' },
  ]
  
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-dark-surface border-t border-dark-border z-50">
      <div className="flex justify-around items-center h-16 max-w-2xl mx-auto">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname === path
          return (
            <Link
              key={path}
              to={path}
              className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                isActive ? 'text-gold' : 'text-gray-400'
              }`}
            >
              <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-xs mt-1">{label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}

const Layout = () => {
  return (
    <div className="min-h-screen bg-dark-bg pb-16">
      <Outlet />
      <Navigation />
    </div>
  )
}

export default Layout
