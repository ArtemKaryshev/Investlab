from typing import Dict, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import User, LearningModule, InvestorCategory


# Learning curriculum data
LEARNING_MODULES = [
    {
        "order": 1,
        "title": "Основы инвестирования: что такое акция и биржа",
        "description": "Узнайте, что такое акция, как работает биржа и почему люди инвестируют.",
        "category": None,  # Available for all
        "content": {
            "sections": [
                {
                    "title": "Что такое акция?",
                    "text": "Акция — это доля в компании. Когда вы покупаете акцию, вы становитесь совладельцем бизнеса. Если компания растёт и зарабатывает больше — стоимость ваших акций растёт."
                },
                {
                    "title": "Как работает биржа?",
                    "text": "Биржа — это площадка, где встречаются продавцы и покупатели акций. Московская биржа (MOEX) — крупнейшая в России. Котировка — текущая цена, по которой можно купить или продать акцию."
                },
                {
                    "title": "Зачем инвестировать?",
                    "text": "Инвестирование позволяет сохранить деньги от инфляции и приумножить капитал. Это альтернатива банковским вкладам с потенциально большей доходностью, но и с рисками."
                }
            ]
        },
        "quiz": {
            "questions": [
                {
                    "question": "Что вы получаете, покупая акцию?",
                    "options": ["Долю в компании", "Кредит от компании", "Зарплату в компании"],
                    "correct": 0
                },
                {
                    "question": "Что такое котировка?",
                    "options": ["Текущая цена акции", "Количество акций", "Название компании"],
                    "correct": 0
                }
            ]
        },
        "practical_task": None,
        "xp_reward": 100
    },
    {
        "order": 2,
        "title": "Как читать котировку и биржевой стакан",
        "description": "Научитесь понимать цены, объёмы торгов и основные индикаторы.",
        "category": None,
        "content": {
            "sections": [
                {
                    "title": "Основные параметры котировки",
                    "text": "• Цена открытия (Open) — цена первой сделки дня\n• Максимум (High) и минимум (Low) — диапазон цен за день\n• Цена закрытия (Close) — последняя цена дня\n• Объём (Volume) — количество акций, проданных за день"
                },
                {
                    "title": "Изменение цены",
                    "text": "Изменение в % показывает, насколько выросла или упала акция относительно предыдущего дня. Зелёный цвет — рост, красный — падение."
                }
            ]
        },
        "quiz": {
            "questions": [
                {
                    "question": "Акция открылась по 100₽, максимум дня — 110₽, закрытие — 105₽. Какое изменение?",
                    "options": ["+5%", "+10%", "+15%"],
                    "correct": 0
                }
            ]
        },
        "practical_task": {
            "description": "Найдите в списке акцию с ростом более 2% и добавьте её в избранное.",
            "type": "add_to_watchlist",
            "criteria": {"min_change_pct": 2.0}
        },
        "xp_reward": 150
    },
    {
        "order": 3,
        "title": "Типы ордеров: рыночный, лимитный, стоп-лосс",
        "description": "Узнайте, как покупать и продавать акции с помощью разных типов заявок.",
        "category": None,
        "content": {
            "sections": [
                {
                    "title": "Рыночный ордер (Market)",
                    "text": "Исполняется мгновенно по текущей рыночной цене. Гарантирует исполнение, но не гарантирует точную цену."
                },
                {
                    "title": "Лимитный ордер (Limit)",
                    "text": "Исполняется только по указанной вами цене или лучше. Может не исполниться, если цена не дойдёт до вашего уровня."
                },
                {
                    "title": "Стоп-лосс (Stop Loss)",
                    "text": "Защищает от больших убытков. Автоматически продаёт акцию, если цена падает до указанного уровня."
                }
            ]
        },
        "quiz": {
            "questions": [
                {
                    "question": "Какой ордер гарантирует исполнение?",
                    "options": ["Рыночный", "Лимитный", "Стоп-лосс"],
                    "correct": 0
                },
                {
                    "question": "Какой ордер защищает от больших убытков?",
                    "options": ["Стоп-лосс", "Рыночный", "Лимитный"],
                    "correct": 0
                }
            ]
        },
        "practical_task": {
            "description": "Совершите первую покупку акции с помощью рыночного ордера.",
            "type": "execute_market_order",
            "criteria": {"side": "buy"}
        },
        "xp_reward": 200
    },
    {
        "order": 4,
        "title": "Риск-менеджмент: не теряйте деньги",
        "description": "Научитесь управлять рисками и защищать свой капитал.",
        "category": None,
        "content": {
            "sections": [
                {
                    "title": "Правило 1-2%",
                    "text": "Не рискуйте более 1-2% капитала в одной сделке. Это защитит вас от катастрофических потерь."
                },
                {
                    "title": "Всегда используйте стоп-лосс",
                    "text": "Стоп-лосс — ваша страховка. Устанавливайте его на уровне 5-10% ниже цены покупки для консервативной стратегии."
                },
                {
                    "title": "Не инвестируйте последние деньги",
                    "text": "Инвестируйте только свободные средства, которые вы можете позволить себе потерять без ущерба для жизни."
                }
            ]
        },
        "quiz": {
            "questions": [
                {
                    "question": "Сколько процентов капитала рекомендуется рисковать в одной сделке?",
                    "options": ["1-2%", "10-15%", "50%"],
                    "correct": 0
                }
            ]
        },
        "practical_task": None,
        "xp_reward": 150
    },
    {
        "order": 5,
        "title": "Диверсификация: не кладите яйца в одну корзину",
        "description": "Узнайте, как снизить риски через диверсификацию портфеля.",
        "category": None,
        "content": {
            "sections": [
                {
                    "title": "Что такое диверсификация?",
                    "text": "Диверсификация — распределение инвестиций между разными активами. Если одна акция упадёт, другие могут компенсировать потери."
                },
                {
                    "title": "Секторальная диверсификация",
                    "text": "Не покупайте только акции одного сектора (например, только нефтяные компании). Включите технологии, финансы, потребительский сектор."
                },
                {
                    "title": "Оптимальное количество акций",
                    "text": "Для начинающих: 5-10 разных акций. Больше — сложнее управлять, меньше — больше риск."
                }
            ]
        },
        "quiz": {
            "questions": [
                {
                    "question": "Что такое диверсификация?",
                    "options": ["Распределение инвестиций между разными активами", "Покупка одной акции", "Продажа всех акций"],
                    "correct": 0
                }
            ]
        },
        "practical_task": {
            "description": "Соберите портфель из минимум 3 акций разных секторов.",
            "type": "build_diversified_portfolio",
            "criteria": {"min_positions": 3}
        },
        "xp_reward": 250
    },
    {
        "order": 6,
        "title": "Сборка инвестиционного портфеля",
        "description": "Научитесь создавать сбалансированный портфель под свои цели.",
        "category": None,
        "content": {
            "sections": [
                {
                    "title": "Консервативный портфель (для категории Консервативный)",
                    "text": "70% — крупные стабильные компании (голубые фишки)\n20% — облигации или дивидендные акции\n10% — cash на случай коррекции"
                },
                {
                    "title": "Умеренный портфель (для категории Умеренный)",
                    "text": "50% — крупные компании\n30% — акции роста\n20% — спекулятивные позиции"
                },
                {
                    "title": "Агрессивный портфель (для категории Агрессивный)",
                    "text": "30% — голубые фишки\n40% — акции роста\n30% — высокорисковые активы"
                }
            ]
        },
        "quiz": {
            "questions": [
                {
                    "question": "Какая доля голубых фишек в консервативном портфеле?",
                    "options": ["70%", "30%", "50%"],
                    "correct": 0
                }
            ]
        },
        "practical_task": {
            "description": "Соберите портфель согласно рекомендациям для вашей категории инвестора.",
            "type": "build_category_portfolio",
            "criteria": {"match_category": True}
        },
        "xp_reward": 300
    },
    {
        "order": 7,
        "title": "Психология и ошибки новичка",
        "description": "Избегайте типичных эмоциональных ошибок начинающих инвесторов.",
        "category": None,
        "content": {
            "sections": [
                {
                    "title": "FOMO — страх упустить прибыль",
                    "text": "Не покупайте акцию только потому, что она растёт. Часто это приводит к покупке на пике и последующим убыткам."
                },
                {
                    "title": "Паническая продажа",
                    "text": "Не продавайте всё при первой просадке. Рынок волатилен — это нормально. Держитесь стратегии."
                },
                {
                    "title": "Усреднение убыточных позиций",
                    "text": "Докупать падающую акцию можно, только если у вас есть фундаментальные причины верить в её восстановление. Иначе вы просто увеличиваете убытки."
                }
            ]
        },
        "quiz": {
            "questions": [
                {
                    "question": "Что такое FOMO?",
                    "options": ["Страх упустить прибыль", "Страх потерять деньги", "Стратегия инвестирования"],
                    "correct": 0
                },
                {
                    "question": "Правильно ли продавать всё при первой просадке?",
                    "options": ["Нет, это паническая продажа", "Да, всегда", "Зависит от настроения"],
                    "correct": 0
                }
            ]
        },
        "practical_task": None,
        "xp_reward": 200
    }
]


class LearningService:
    """Service for managing learning progress and gamification."""
    
    async def initialize_modules(self, db: AsyncSession):
        """Initialize learning modules in database."""
        
        # Check if modules already exist
        result = await db.execute(select(LearningModule))
        existing = result.scalars().all()
        
        if existing:
            return  # Already initialized
        
        # Create modules
        for module_data in LEARNING_MODULES:
            module = LearningModule(**module_data)
            db.add(module)
        
        await db.commit()
    
    async def get_modules_for_user(
        self,
        db: AsyncSession,
        user: User
    ) -> List[Dict[str, Any]]:
        """Get learning modules available for user's category."""
        
        stmt = select(LearningModule).where(
            (LearningModule.category == user.investor_category) |
            (LearningModule.category.is_(None))
        ).order_by(LearningModule.order)
        
        result = await db.execute(stmt)
        modules = result.scalars().all()
        
        completed_lessons = user.completed_lessons or []
        
        return [
            {
                "id": m.id,
                "order": m.order,
                "title": m.title,
                "description": m.description,
                "content": m.content,
                "quiz": m.quiz,
                "practical_task": m.practical_task,
                "xp_reward": m.xp_reward,
                "completed": m.id in completed_lessons,
                "quiz_score": user.quiz_scores.get(str(m.id)) if user.quiz_scores else None,
            }
            for m in modules
        ]
    
    async def complete_lesson(
        self,
        db: AsyncSession,
        user: User,
        module_id: int
    ) -> Dict[str, Any]:
        """Mark lesson as completed and award XP."""
        
        # Get module
        result = await db.execute(
            select(LearningModule).where(LearningModule.id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module:
            return {"success": False, "error": "Модуль не найден"}
        
        # Check if already completed
        completed_lessons = user.completed_lessons or []
        if module_id in completed_lessons:
            return {"success": False, "error": "Урок уже пройден"}
        
        # Add to completed
        completed_lessons.append(module_id)
        user.completed_lessons = completed_lessons
        
        # Award XP
        user.xp += module.xp_reward
        
        # Check for level up
        new_level = self._calculate_level(user.xp)
        leveled_up = new_level > user.level
        user.level = new_level
        
        # Update progress
        user.learning_progress = self._calculate_progress(user)
        
        await db.commit()
        
        return {
            "success": True,
            "xp_earned": module.xp_reward,
            "total_xp": user.xp,
            "level": user.level,
            "leveled_up": leveled_up,
            "progress": user.learning_progress,
        }
    
    async def submit_quiz(
        self,
        db: AsyncSession,
        user: User,
        module_id: int,
        answers: List[int]
    ) -> Dict[str, Any]:
        """Submit quiz answers and calculate score."""
        
        # Get module
        result = await db.execute(
            select(LearningModule).where(LearningModule.id == module_id)
        )
        module = result.scalar_one_or_none()
        
        if not module or not module.quiz:
            return {"success": False, "error": "Квиз не найден"}
        
        # Calculate score
        questions = module.quiz.get("questions", [])
        if len(answers) != len(questions):
            return {"success": False, "error": "Неверное количество ответов"}
        
        correct = sum(
            1 for i, q in enumerate(questions)
            if answers[i] == q["correct"]
        )
        score = int((correct / len(questions)) * 100)
        
        # Save score
        quiz_scores = user.quiz_scores or {}
        quiz_scores[str(module_id)] = score
        user.quiz_scores = quiz_scores
        
        # Update progress
        user.learning_progress = self._calculate_progress(user)
        
        await db.commit()
        
        return {
            "success": True,
            "score": score,
            "correct": correct,
            "total": len(questions),
            "passed": score >= 70,
        }
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level from XP (100 XP per level)."""
        return max(1, xp // 100)
    
    def _calculate_progress(self, user: User) -> int:
        """
        Calculate overall learning progress (0-100%).
        Formula: 60% lessons + 30% quizzes + 10% practical tasks
        """
        # Count total modules (simplified - assumes 7 modules)
        total_modules = 7
        
        completed_lessons = len(user.completed_lessons or [])
        lesson_progress = (completed_lessons / total_modules) * 60
        
        quiz_scores = user.quiz_scores or {}
        if quiz_scores:
            avg_quiz_score = sum(quiz_scores.values()) / len(quiz_scores)
            quiz_progress = (avg_quiz_score / 100) * 30
        else:
            quiz_progress = 0
        
        practical_tasks = len(user.practical_tasks or [])
        task_progress = min((practical_tasks / 3) * 10, 10)  # Max 3 practical tasks
        
        return min(int(lesson_progress + quiz_progress + task_progress), 100)
    
    async def award_achievement(
        self,
        db: AsyncSession,
        user: User,
        achievement_id: str
    ):
        """Award an achievement to user."""
        achievements = user.achievements or []
        if achievement_id not in achievements:
            achievements.append(achievement_id)
            user.achievements = achievements
            await db.commit()


# Global learning service instance
learning_service = LearningService()
