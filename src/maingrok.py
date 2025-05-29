from kivy.config import Config
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.set('graphics', 'resizable', '0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, Ellipse
from kivy.utils import platform
from kivy.lang import Builder
from kivy.clock import Clock
from firebase_config import db, current_user

# Запрос разрешений для Android
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
    except ImportError:
        pass

class AnswerButton(Button):
    is_selected = BooleanProperty(False)
    question_screen = ObjectProperty(None)
    question_data = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (1, 1, 1, 1) # Этот цвет используется Kivy, но мы рисуем сами
        self.color = (0.2, 0.2, 0.2, 1) # Цвет текста
        self.font_size = dp(16)
        self.size_hint_y = None # Высота будет определяться содержимым
        # Устанавливаем padding. Вертикальный padding поможет тексту не прижиматься к краям.
        self.padding = (dp(15), dp(10)) # Настройте вертикальный padding по необходимости
        self.halign = 'left'
        self.valign = 'top' # Выравнивание текста сверху кнопки
        
        # Привязываем обновление text_size к изменению ширины
        self.bind(width=self._update_text_size)
        # Привязываем высоту кнопки к размеру текста + padding
        self.bind(texture_size=self._update_height)

        # Планируем первый вызов update_visuals на следующий кадр
        Clock.schedule_once(lambda dt: self.update_visuals(), 0)

    # Метод для обновления text_size при изменении ширины кнопки
    def _update_text_size(self, instance, width):
        if width > 0:
            self.text_size = (width - self.padding[0]*2, None)

    # Метод для обновления высоты кнопки на основе размера текста
    def _update_height(self, instance, texture_size):
        self.height = texture_size[1] + self.padding[1]*2

    def _bind_question_screen_properties(self, instance, value):
        if hasattr(self, '_old_question_screen') and self._old_question_screen:
            self._old_question_screen.unbind(show_explanation=self.update_visuals,
                                             selected_answer_option=self.update_visuals,
                                             is_correct=self.update_visuals)
        if value:
            value.bind(show_explanation=self.update_visuals,
                       selected_answer_option=self.update_visuals,
                       is_correct=self.update_visuals)
            self._old_question_screen = value
            self.update_visuals() # Обновляем визуал после привязки

    def update_visuals(self, *args):
        # print(f"update_visuals called for '{self.text}'. is_selected: {self.is_selected}, show_explanation: {self.question_screen.show_explanation if self.question_screen else 'N/A'}") # Detailed Debug
        self.canvas.before.clear() # Очищаем инструкции перед основным холстом
        with self.canvas.before:
            # Временно меняем цвет фона по умолчанию на синий для диагностики
            bg_color = (0, 0, 1, 1) # Синий цвет по умолчанию (для теста)
            # bg_color = (1, 1, 1, 1) # Цвет по умолчанию (белый) - оригинальный

            border_color = (0.85, 0.85, 0.85, 1) # Цвет рамки по умолчанию (серый)

            q_screen = self.question_screen
            q_data = self.question_data

            if q_screen and q_data: # Проверяем, доступны ли данные экрана вопросов
                if q_screen.show_explanation: # Если показывается объяснение (после проверки ответа)
                    if self.text == q_data.get('correct_answer'):
                        # Правильный ответ
                        bg_color = (0.8, 1, 0.8, 1) # Зеленый фон
                        border_color = (0.1, 0.6, 0.1, 1) # Зеленая рамка
                    elif self.text == q_screen.selected_answer_option and not q_screen.is_correct:
                        # Выбранный пользователем НЕправильный ответ
                        bg_color = (1, 0.8, 0.8, 1) # Красный фон
                        border_color = (0.6, 0.1, 0.1, 1) # Красная рамка
                elif self.is_selected: # Если кнопка просто выбрана пользователем (до проверки)
                    # Выбранный ответ до проверки
                    bg_color = (1, 0.9, 0.8, 1) # Оранжевый фон
                    border_color = (1, 0.5, 0.3, 1) # Оранжевая рамка
            
            # Сначала рисуем фон
            Color(*bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(10)]
            )

            # Затем рисуем рамку поверх фона
            Color(*border_color)
            Line(
                width=dp(1.5),
                rounded_rectangle=(*self.pos, *self.size, dp(10))
            )

class TopicCard(BoxLayout):
    title = StringProperty('')
    questions_count = StringProperty('')
    progress = StringProperty('')
    locked = BooleanProperty(False)
    topic_id = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(160)
    
    def on_button_press(self, instance):
        print(f"Кнопка нажата: {instance.text}")  # Debug
        if not self.locked:
            print(f"Переход к теме: {self.title}")  # Debug
            app = App.get_running_app()
            questions_screen = app.sm.get_screen('questions')
            topics_screen = app.sm.get_screen('topics')
            
            questions_screen.topic_id = self.topic_id
            questions_screen.training_mode = not topics_screen.interview_mode
            questions_screen.title = self.title
            app.sm.current = 'questions'
            print(f"Переключение на экран вопросов, training_mode: {questions_screen.training_mode}")  # Debug

class MainScreen(Screen):
    questions_completed = NumericProperty(0)
    topics_completed = NumericProperty(0)
    total_topics = NumericProperty(0)
    total_questions = NumericProperty(0)
    
    def on_enter(self):
        if current_user:
            user_ref = db.collection('users').document(current_user['localId'])
            user_data = user_ref.get()
            if user_data.exists:
                data = user_data.to_dict()
                self.questions_completed = data.get('questions_completed', 0)
                self.topics_completed = data.get('topics_completed', 0)
            else:
                print("No user data found in Firebase")
        else:
            print("No current user available")

class TopicsScreen(Screen):
    interview_mode = BooleanProperty(False)
    
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_topics(), 0) # Schedule on next frame

    def load_topics(self):
        topics_layout = self.ids.topics_layout
        topics_layout.clear_widgets()
        try:
            topics_ref = db.collection('topics')
            topics = topics_ref.stream()
            topic_found = False
            for topic in topics:
                topic_found = True
                topic_data = topic.to_dict()
                if not topic_data:
                    print(f"Пустые данные для темы {topic.id}")
                    continue
                topic_data['id'] = topic.id
                print(f"Загружена тема: {topic_data}")
                self.add_topic_card(topic_data)
            
            # Update total counts in MainScreen
            app = App.get_running_app()
            main_screen = app.sm.get_screen('main')
            main_screen.total_topics = len(self.ids.topics_layout.children) # Count added topic cards
            main_screen.total_questions = sum(int(card.questions_count) for card in self.ids.topics_layout.children if hasattr(card, 'questions_count')) # Sum questions from loaded topics

            if not topic_found:
                print("Коллекция 'topics' пуста или не найдена")
                topics_layout.add_widget(Label(
                    text="Нет доступных тем. Проверьте Firebase.",
                    font_size=dp(16),
                    color=(1, 0, 0, 1),
                    size_hint_y=None,
                    height=dp(50)
                ))
        except Exception as e:
            print(f"Ошибка при загрузке тем: {str(e)}")
            topics_layout.add_widget(Label(
                text=f"Ошибка: {str(e)}",
                font_size=dp(16),
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=dp(50)
            ))
    
    def add_topic_card(self, topic_data):
        print(f"Creating topic card with data: {topic_data}")  # Debug
        if not topic_data.get('title') or not topic_data.get('questions_count'):
            print(f"Skipping topic card due to missing title or questions_count: {topic_data}")
            return
            
        card = TopicCard()
        card.title = topic_data.get('title', 'Без названия')
        card.questions_count = str(topic_data.get('questions_count', 0))
        card.progress = str(topic_data.get('progress', 0))
        card.locked = topic_data.get('locked', False)
        card.topic_id = topic_data['id']  # Сохраняем ID темы в карточке
        
        self.ids.topics_layout.add_widget(card)

class QuestionsScreen(Screen):
    topic_id = StringProperty('')
    current_question = NumericProperty(0)
    total_questions = NumericProperty(0)
    question_text = StringProperty('')
    explanation = StringProperty('')
    result_text = StringProperty('')
    is_correct = BooleanProperty(False)
    show_explanation = BooleanProperty(False)
    training_mode = BooleanProperty(False)
    wrong_answers = ListProperty([])
    correct_answers = NumericProperty(0)
    title = StringProperty('Вопросы')
    selected_answer_option = ObjectProperty('', allow_none=True)
    answer_selected = BooleanProperty(False)
    button_state = StringProperty('check') # check, next

    time_left = NumericProperty(1800) # 30 minutes in seconds
    timer_event = ObjectProperty(None, allow_none=True) # To hold the scheduled timer event
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []
        self.current_options = []
        self.answer_buttons = []
        
    def on_enter(self):
        self.show_explanation = False
        self.correct_answers = 0
        self.wrong_answers = []
        self.selected_answer_option = '' # Сбрасываем выбранный ответ при входе
        self.answer_selected = False # Сбрасываем статус выбора при входе
        self.button_state = 'check' # Устанавливаем начальное состояние кнопки
        self.time_left = 1800 # Reset timer
        if self.timer_event: # Cancel any existing timer
            self.timer_event.cancel()
            # self.timer_event = None # Закомментировано для избежания ValueError

        if self.topic_id:
            try:
                topic_ref = db.collection('topics').document(self.topic_id)
                topic_data = topic_ref.get()
                if topic_data.exists:
                    self.title = topic_data.to_dict().get('title', 'Вопросы')
            except Exception as e:
                print(f"Ошибка при загрузке названия темы: {str(e)}")
                self.title = 'Вопросы'
        # Schedule load_questions to allow KV to build widgets and make ids available
        Clock.schedule_once(lambda dt: self.load_questions(), 0)

    
    def load_questions(self):
        if not self.topic_id:
            self.question_text = "Нет доступных вопросов"
            return
        try:
            questions_ref = db.collection('topics').document(self.topic_id).collection('questions')
            # Получаем все вопросы из темы
            all_questions = list(questions_ref.get())
            self.questions = []
            for doc in all_questions:
                question_data = doc.to_dict()
                if all(key in question_data for key in ['text', 'options', 'correct_answer', 'explanation']):
                    self.questions.append(question_data.copy())
            print(f"Загружено {len(self.questions)} вопросов из Firebase, режим тренировки: {self.training_mode}")  # Debug

            # Перемешиваем вопросы только в режиме интервью (когда training_mode = False)
            if not self.training_mode:
                import random
                random.shuffle(self.questions)
                print(f"Вопросы перемешаны для режима интервью") # Debug
                
                # В режиме интервью оставляем только первые 20 вопросов, если их больше
                if len(self.questions) > 20:
                    self.questions = self.questions[:20]
                    print(f"Оставлено 20 случайных вопросов для режима интервью") # Debug
            else:
                print(f"Вопросы оставлены в исходном порядке для режима тренировки") # Debug

            self.total_questions = len(self.questions) # Обновляем общее количество вопросов после ограничения
            self.current_question = 0
            print(f"Всего вопросов для показа: {self.total_questions}")  # Debug
            if self.total_questions > 0:
                self.show_question()
                # Запускаем таймер только в режиме интервью (когда training_mode = False)
                if not self.training_mode:
                    self.timer_event = Clock.schedule_interval(self.update_timer, 1)
                    print(f"Таймер запущен для режима интервью") # Debug
                else:
                    print(f"Таймер не запущен для режима тренировки") # Debug
            else:
                self.question_text = "Нет доступных вопросов для этой темы"
                print(f"No quizzes found for topic {self.topic_id}")
        except Exception as e:
            print(f"Ошибка загрузки вопросов: {str(e)}")
            self.question_text = f"Ошибка: {str(e)}"
            
    def show_question(self):
        self.show_explanation = False
        self.explanation = ""
        self.result_text = ""
        self.selected_answer_option = '' # Сбрасываем выбранный ответ для нового вопроса
        self.answer_selected = False # Сбрасываем статус выбора для нового вопроса
        self.button_state = 'check' # Устанавливаем кнопку в состояние "Проверить"
        if 0 <= self.current_question < self.total_questions:
            question = self.questions[self.current_question]
            options_container = self.ids.options_container
            options_container.clear_widgets()
            self.answer_buttons = []
            self.question_text = question['text']
            self.current_options = question['options']
            print(f"Showing question {self.current_question + 1}: {self.question_text}")  # Debug
            Clock.schedule_once(lambda dt: self._add_answer_buttons(question), 0.01) # Добавляем задержку

    def _add_answer_buttons(self, question):
        options_container = self.ids.options_container
        for option in self.current_options:
            btn = AnswerButton()
            btn.text = option
            btn.is_selected = False
            btn.state = 'normal' # Явно устанавливаем состояние кнопки
            btn.question_screen = self # Передаем ссылку на QuestionScreen
            btn.question_data = question # Передаем данные вопроса
            btn.bind(on_press=lambda btn=btn, opt=option: self.select_answer(btn, opt))
            options_container.add_widget(btn)
            self.answer_buttons.append(btn)
            # Принудительно обновляем размер текста и высоту после добавления текста (привязка в AnswerButton должна справиться)
            # btn._update_text_size(btn, btn.width) # Удалено

    def select_answer(self, selected_btn, selected_option):
        print(f"Нажата кнопка ответа: {selected_option}") # Отладочный print
        
        for btn in self.answer_buttons:
            if btn == selected_btn: # Если это выбранная кнопка
                 btn.is_selected = True
            else: # Если это другая кнопка
                 btn.is_selected = False
            
            # Вызываем обновление визуала для каждой кнопки сразу после установки is_selected
            btn.update_visuals()

        self.selected_answer_option = selected_option # Сохраняем выбранный ответ
        self.answer_selected = True # Устанавливаем статус, что ответ выбран

    def process_answer(self):
        if not self.answer_selected:
             print("No answer selected")
             return

        question = self.questions[self.current_question]
        selected_option = self.selected_answer_option

        self.is_correct = selected_option == question['correct_answer']
        question['user_answer'] = selected_option

        if self.is_correct:
            self.correct_answers += 1
        else:
            wrong_answer = question.copy()
            self.wrong_answers.append(wrong_answer)

        self.result_text = "Правильно!" if self.is_correct else f"Неправильно. Правильный ответ: {question['correct_answer']}"
        self.explanation = str(question.get('explanation', ''))
        self.show_explanation = True
        self.button_state = 'next'
        print(f"Ответ: {selected_option}, Правильно: {self.is_correct}, Объяснение: {self.explanation}")

        # Отключаем все кнопки ответов после проверки (опционально, если нужно предотвратить дальнейший выбор)
        # for btn in self.answer_buttons:
        #     btn.disabled = True
    
    def next_question(self):
        if self.button_state == 'next':
            self.current_question += 1
            if self.current_question < self.total_questions:
                self.show_question()
            else:
                # Timer stops automatically when quiz ends
                if self.timer_event:
                     self.timer_event.cancel()
                     # self.timer_event = None # Commenting out this line
                # If in interview mode, go to results screen, otherwise back to topics
                if not self.training_mode:
                    wrong_topics = " * ".join(set(q.get('topic', '') for q in self.wrong_answers)) # Use wrong_answers collected so far
                    print(f"Результат по таймеру: {self.correct_answers} правильных, {len(self.wrong_answers)} ошибок") # Debug
                    results_screen = self.manager.get_screen('results')
                    results_screen.show_results(self.correct_answers, self.current_question + 1, len(self.wrong_answers), wrong_topics) # Pass results up to current question
                    self.manager.current = 'results'
                else:
                    self.manager.current = 'topics'

    def handle_bottom_button(self):
        if self.button_state == 'check':
            self.process_answer()
        elif self.button_state == 'next':
            self.next_question()

    def update_timer(self, dt):
        self.time_left -= 1
        if self.time_left <= 0:
            self.time_left = 0
            if self.timer_event:
                self.timer_event.cancel()
                # self.timer_event = None # Commenting out this line
            self.quiz_complete()

    def quiz_complete(self):
        print("Тест завершен по таймеру!") # Debug
        # Here you can add logic to show results or handle timeout
        # For now, let's just switch to the results screen
        if not self.training_mode:
            wrong_topics = " * ".join(set(q.get('topic', '') for q in self.wrong_answers)) # Use wrong_answers collected so far
            print(f"Результат по таймеру: {self.correct_answers} правильных, {len(self.wrong_answers)} ошибок") # Debug
            results_screen = self.manager.get_screen('results')
            results_screen.show_results(self.correct_answers, self.current_question + 1, len(self.wrong_answers), wrong_topics) # Pass results up to current question
        self.manager.current = 'results'

    def on_leave(self):
        # Ensure timer is stopped if screen is left
        if self.timer_event:
            self.timer_event.cancel()
            # self.timer_event = None # Commenting out this line
        print("Leaving QuestionsScreen, timer stopped.") # Debug

    def format_timer(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

class ResultsScreen(Screen):
    correct_answers = NumericProperty(0)
    total_questions = NumericProperty(0)
    wrong_answers = NumericProperty(0)
    passed = BooleanProperty(False)
    wrong_topics = StringProperty('')
    
    def show_results(self, correct, total, wrong, wrong_topics):
        self.correct_answers = correct
        self.total_questions = total
        self.wrong_answers = wrong
        self.passed = (total - correct) < 3
        self.wrong_topics = wrong_topics
        print(f"Showing results: Correct={correct}, Total={total}, Wrong={wrong}, Topics={wrong_topics}")  # Debug

class QuizCard(BoxLayout):
    pass

class SettingsScreen(Screen):
    # Класс для экрана настроек
    pass

class QuizApp(App):
    def load_app_data(self):
        try:
            # Загружаем темы и подсчитываем общее количество вопросов
            topics_ref = db.collection('topics')
            topics = topics_ref.stream()
            total_questions = 0
            total_topics = 0
            
            for topic in topics:
                total_topics += 1
                topic_data = topic.to_dict()
                if topic_data:
                    total_questions += int(topic_data.get('questions_count', 0))
            
            # Обновляем счетчики на главном экране
            main_screen = self.sm.get_screen('main')
            main_screen.total_topics = total_topics
            main_screen.total_questions = total_questions
            
            print(f"Загружено тем: {total_topics}, всего вопросов: {total_questions}")
            
        except Exception as e:
            print(f"Ошибка при загрузке данных: {str(e)}")

    def build(self):
        self.title = 'Intervirium'
        self.sm = ScreenManager(transition=NoTransition())
        Builder.load_file('main.kv') # Load the KV file here
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(TopicsScreen(name='topics'))
        self.sm.add_widget(QuestionsScreen(name='questions'))
        self.sm.add_widget(ResultsScreen(name='results'))
        self.sm.add_widget(SettingsScreen(name='settings'))
        
        # Загружаем данные при запуске приложения
        Clock.schedule_once(lambda dt: self.load_app_data(), 0)
        
        return self.sm

if __name__ == '__main__':
    QuizApp().run()