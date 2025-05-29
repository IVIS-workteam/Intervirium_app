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
        self.background_color = (1, 1, 1, 1)
        self.color = (0.2, 0.2, 0.2, 1)
        self.font_size = dp(16)
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = (dp(15), 0)
        self.halign = 'left'
        self.valign = 'middle'
        self.text_size = (self.width - dp(30), None)
        self.bind(is_selected=self.update_visuals)
        self.bind(question_screen=self._bind_question_screen_properties)
        self.update_visuals() # Первичное обновление визуала

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
        self.canvas.before.clear() # Очищаем инструкции перед основным холстом
        with self.canvas.before:
            bg_color = (1, 1, 1, 1)
            border_color = (0.85, 0.85, 0.85, 1)

            q_screen = self.question_screen
            q_data = self.question_data

            if q_screen and q_data:
                if q_screen.show_explanation:
                    if self.text == q_data.get('correct_answer'):
                        bg_color = (0.8, 1, 0.8, 1)
                        border_color = (0.1, 0.6, 0.1, 1)
                    elif self.text == q_screen.selected_answer_option and not q_screen.is_correct:
                        bg_color = (1, 0.8, 0.8, 1)
                        border_color = (0.6, 0.1, 0.1, 1)
                elif self.is_selected:
                    bg_color = (1, 0.9, 0.8, 1)
                    border_color = (1, 0.5, 0.3, 1)

            Color(*bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(10)]
            )
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
        if self.topic_id:
            try:
                topic_ref = db.collection('topics').document(self.topic_id)
                topic_data = topic_ref.get()
                if topic_data.exists:
                    self.title = topic_data.to_dict().get('title', 'Вопросы')
            except Exception as e:
                print(f"Ошибка при загрузке названия темы: {str(e)}")
                self.title = 'Вопросы'
        Clock.schedule_once(lambda dt: self.load_questions())

    def load_questions(self):
        if not self.topic_id:
            self.question_text = "Нет доступных вопросов"
            return
        try:
            questions_ref = db.collection('topics').document(self.topic_id).collection('questions')
            questions = list(questions_ref.get())
            self.questions = []
            for doc in questions:
                question_data = doc.to_dict()
                if all(key in question_data for key in ['text', 'options', 'correct_answer', 'explanation']):
                    self.questions.append(question_data.copy())
            print(f"Загружено {len(self.questions)} вопросов, режим тренировки: {self.training_mode}")  # Debug
            if not self.training_mode and len(self.questions) > 3:
                import random
                self.questions = random.sample(self.questions, 3)
                print(f"Выбрано 3 случайных вопроса для теста")  # Debugар
            self.total_questions = len(self.questions)
            self.current_question = 0
            print(f"Всего вопросов для показа: {self.total_questions}")  # Debug
            if self.total_questions > 0:
                self.show_question()
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

    def select_answer(self, selected_btn, selected_option):
        print(f"Answer button pressed: {selected_option}") # Отладочный print
        for btn in self.answer_buttons:
            btn.is_selected = False # Сбрасываем выбор со всех кнопок
            # btn.disabled = False # Включаем кнопки перед выбором нового ответа (если были отключены)
        selected_btn.is_selected = True # Отмечаем только выбранную кнопку
        self.selected_answer_option = selected_option # Сохраняем выбранный ответ
        self.answer_selected = True # Устанавливаем статус, что ответ выбран
        # Теперь не вызываем check_answer здесь

    def process_answer(self):
        # Проверяем ответ, используя self.selected_answer_option
        if not self.answer_selected: # Проверяем статус выбора, а не None
             print("No answer selected") # Не должно происходить, если кнопка Далее отключена
             return

        question = self.questions[self.current_question]
        selected_option = self.selected_answer_option

        self.is_correct = selected_option == question['correct_answer']
        question['user_answer'] = selected_option

        if self.is_correct:
            self.correct_answers += 1
            # Визуальное выделение правильного ответа
            for btn in self.answer_buttons:
                if btn.text == question['correct_answer']:
                    btn.is_selected = True # Подсвечиваем правильный ответ
                    # Добавить изменение цвета фона на зеленый через KV при is_selected=True и правильном ответе
                # else:
                #     btn.disabled = True # Отключаем неправильные варианты
        else:
            wrong_answer = question.copy()
            self.wrong_answers.append(wrong_answer)
            # Визуальное выделение неправильного ответа и правильного
            for btn in self.answer_buttons:
                if btn.text == selected_option:
                    btn.is_selected = True # Подсвечиваем выбранный (неправильный) ответ
                    # Добавить изменение цвета фона на красный через KV при is_selected=True и неправильном ответе
                elif btn.text == question['correct_answer']:
                     btn.is_selected = True # Подсвечиваем правильный ответ
                     # Добавить изменение цвета фона на зеленый через KV при is_selected=True и правильном ответе
                # else:
                #     btn.disabled = True # Отключаем остальные варианты

        self.result_text = "Правильно!" if self.is_correct else f"Неправильно. Правильный ответ: {question['correct_answer']}"
        self.explanation = str(question.get('explanation', ''))
        self.show_explanation = True # Показываем объяснение
        self.button_state = 'next' # Меняем состояние кнопки на "Далее"
        print(f"Ответ: {selected_option}, Правильно: {self.is_correct}, Объяснение: {self.explanation}")  # Debug
        print(f"Debug: show_explanation={self.show_explanation}, result_text='{self.result_text}', explanation='{self.explanation}'") # Отладочный принт для объяснения

        # Отключаем все кнопки ответов после проверки

    def next_question(self):
        if self.button_state == 'next':
            self.current_question += 1
            if self.current_question < self.total_questions:
                # Clock.schedule_once(lambda dt: self.show_question(), 1) # Задержка 1 секунда перед показом нового вопроса
                self.show_question() # Переходим сразу к следующему вопросу
            else:
                if not self.training_mode:
                    wrong_topics = " * ".join(set(q.get('topic', '') for q in self.wrong_answers))
                    print(f"Результат: {self.correct_answers} правильных, {len(self.wrong_answers)} ошибок")  # Debug
                    results_screen = self.manager.get_screen('results')
                    results_screen.show_results(self.correct_answers, self.total_questions, len(self.wrong_answers), wrong_topics)
                    self.manager.current = 'results'
                else:
                    self.manager.current = 'topics'
        else:
             print("Кнопка 'Далее' нажата раньше времени (Не должно происходить)")

    def handle_bottom_button(self):
        if self.button_state == 'check':
            self.process_answer()
        elif self.button_state == 'next':
            self.next_question()

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
    def build(self):
        self.title = 'Intervirium'
        self.sm = ScreenManager(transition=NoTransition())
        Builder.load_file('main.kv') # Load the KV file here
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(TopicsScreen(name='topics'))
        self.sm.add_widget(QuestionsScreen(name='questions'))
        self.sm.add_widget(ResultsScreen(name='results'))
        self.sm.add_widget(SettingsScreen(name='settings'))
        return self.sm

if __name__ == '__main__':
    QuizApp().run()