from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty, ListProperty
from functools import partial
from firebase_config import db, current_user
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.utils import platform

# Android permissions
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
    except ImportError:
        pass

class RoundedButton(Button):
    background_color = ListProperty([1, 1, 1, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = [0.95, 0.5, 0.3, 1]  # Orange color
        self.bind(size=self._update_canvas, pos=self._update_canvas)
        self._update_canvas()
        
    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[15])

# Загрузка KV языка для интерфейса
Builder.load_string('''
#:import utils kivy.utils

<RoundedButton>:
    background_color: 0,0,0,0
    color: 1,1,1,1
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#FF7F50')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]

<TopicCard>:
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#FFF5F5')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]

    BoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(10)
        
        Label:
            text: root.title
            font_size: dp(20)
            color: 0, 0, 0, 1
            size_hint_y: None
            height: dp(30)
            text_size: self.width, None
            halign: 'left'
            
        BoxLayout:
            size_hint_y: None
            height: dp(20)
            spacing: dp(5)
            
            Label:
                text: root.questions_count
                font_size: dp(14)
                color: utils.get_color_from_hex('#B0B0B0')
                size_hint_x: None
                width: self.texture_size[0]
                text_size: None, None
                halign: 'left'
                
            Label:
                text: ' вопросов'
                font_size: dp(14)
                color: utils.get_color_from_hex('#B0B0B0')
                size_hint_x: None
                width: self.texture_size[0]
                text_size: None, None
                halign: 'left'
                
            Label:
                text: ' • ' + root.progress + '% завершено' if root.progress != '0' else ''
                font_size: dp(14)
                color: utils.get_color_from_hex('#B0B0B0')
                size_hint_x: 1
                text_size: None, None
                halign: 'left'
                
        Widget:
            size_hint_y: None
            height: dp(4)
            canvas:
                Color:
                    rgba: utils.get_color_from_hex('#FFE5E5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [2]
                Color:
                    rgba: utils.get_color_from_hex('#FF7F50')
                RoundedRectangle:
                    pos: self.pos
                    size: self.width * float(root.progress or 0) / 100, self.height
                    radius: [2]
        
        Button:
            text: 'Разблокировать за 299 ₽' if root.locked else 'Начать'
            size_hint: 1, None
            height: dp(40)
            background_color: 0, 0, 0, 0
            color: 1, 1, 1, 1
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FF7F50')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]

<StatsCard>:
    orientation: 'vertical'
    padding: dp(15)
    canvas.before:
        Color:
            rgba: utils.get_color_from_hex('#FFF5F5')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]

<MainScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)
        
        Label:
            text: 'Intervirium'
            font_size: dp(32)
            bold: True
            size_hint_y: None
            height: dp(50)
            color: utils.get_color_from_hex('#FF7F50')
            
        BoxLayout:
            size_hint_y: None
            height: dp(100)
            spacing: dp(20)
            
            StatsCard:
                Label:
                    text: f'{root.questions_completed}/800'
                    font_size: dp(24)
                    color: utils.get_color_from_hex('#FF7F50')
                    bold: True
                    size_hint_y: None
                    height: dp(30)
                Label:
                    text: 'Вопросы'
                    font_size: dp(16)
                    color: utils.get_color_from_hex('#B0B0B0')
                    
            StatsCard:
                Label:
                    text: f'{root.topics_completed}/14'
                    font_size: dp(24)
                    color: utils.get_color_from_hex('#FF7F50')
                    bold: True
                    size_hint_y: None
                    height: dp(30)
                Label:
                    text: 'Темы'
                    font_size: dp(16)
                    color: utils.get_color_from_hex('#B0B0B0')
        
        Widget:
            size_hint_y: 0.3
            
        Button:
            text: 'Начать интервью'
            size_hint: 0.8, None
            pos_hint: {'center_x': 0.5}
            height: dp(50)
            background_color: 0, 0, 0, 0
            color: 1, 1, 1, 1
            font_size: dp(18)
            on_press: 
                root.manager.current = 'topics'
                root.manager.get_screen('topics').interview_mode = True
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FF7F50')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            
        Widget:
            size_hint_y: 0.1
        
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(15)
            size_hint_y: None
            height: dp(180)
            
        Button:
            text: 'Тренировка'
            size_hint_y: None
            height: dp(50)
            background_color: 0,0,0,0
            color: utils.get_color_from_hex('#000000')
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            on_press: root.manager.current = 'training'
            
        Button:
            text: 'Мои результаты'
            size_hint_y: None
            height: dp(50)
            background_color: 0,0,0,0
            color: utils.get_color_from_hex('#000000')
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            
        Button:
            text: 'Настройки'
            size_hint_y: None
            height: dp(50)
            background_color: 0,0,0,0
            color: utils.get_color_from_hex('#000000')
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]

<TopicsScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)
        
        Label:
            text: 'Список тем'
            font_size: dp(32)
            bold: True
            size_hint_y: None
            height: dp(50)
            color: utils.get_color_from_hex('#FF7F50')
            text_size: self.width, None
            halign: 'center'
            
        ScrollView:
            BoxLayout:
                id: topics_layout
                orientation: 'vertical'
                spacing: dp(15)
                size_hint_y: None
                height: self.minimum_height
                padding: dp(0), dp(0), dp(0), dp(20)
            
        Button:
            text: 'Назад'
            size_hint: 0.8, None
            pos_hint: {'center_x': 0.5}
            height: dp(50)
            background_color: 0,0,0,0
            color: utils.get_color_from_hex('#FF7F50')
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            on_press: root.manager.current = 'main'
            
<AnswerButton>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    size_hint: 1, None
    height: dp(60)
    font_size: dp(16)
    halign: 'center'
    valign: 'middle'
    text_size: self.width - dp(40), None
    padding: dp(20), dp(10)
    canvas.before:
        Color:
            rgba: self.background_rgba
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]

<TrainingScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)
        
        Label:
            text: 'Тренировка'
            font_size: dp(32)
            bold: True
            size_hint_y: None
            height: dp(50)
            color: utils.get_color_from_hex('#FF7F50')
            text_size: self.width, None
            halign: 'center'
            
        ScrollView:
            BoxLayout:
                id: topics_layout
                orientation: 'vertical'
                spacing: dp(15)
                size_hint_y: None
                height: self.minimum_height
                padding: dp(0), dp(0), dp(0), dp(20)
            
        Button:
            text: 'Назад'
            size_hint: 0.8, None
            pos_hint: {'center_x': 0.5}
            height: dp(50)
            background_color: 0,0,0,0
            color: utils.get_color_from_hex('#FF7F50')
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            on_press: root.manager.current = 'main'

<QuestionsScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)
        
        # Заголовок и прогресс
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: dp(80)
            spacing: dp(15)
        
        Label:
            text: 'Тренировка' if root.training_mode else 'Интервью'
            font_size: dp(16)
            color: utils.get_color_from_hex('#FF7F50')
            size_hint_y: None
            height: dp(20)
            
        Label:
            text: f'Вопрос {root.current_question + 1} из {root.total_questions}'
            font_size: dp(24)
            color: utils.get_color_from_hex('#FF7F50')
            size_hint_y: None
            height: dp(30)
            text_size: self.width, None
            halign: 'left'
            
            # Прогресс-бар
        BoxLayout:
            size_hint_y: None
            height: dp(8)
            padding: 0
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFE5E5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [4]
                Color:
                    rgba: utils.get_color_from_hex('#FF7F50')
                RoundedRectangle:
                    pos: self.pos
                    size: self.width * (root.current_question + 1) / root.total_questions if root.total_questions > 0 else 0, self.height
                    radius: [4]
        
        # Текст вопроса
        BoxLayout:
            size_hint_y: None
            height: question_label.height + dp(40)
            padding: dp(20)
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            
        Label:
            id: question_label
            text: root.question_text
            font_size: dp(18)
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
            color: 0, 0, 0, 1
            halign: 'left'
            valign: 'middle'
        
        # Варианты ответов
        BoxLayout:
            id: options_container
            orientation: 'vertical'
            spacing: dp(15)
            size_hint_y: None
            height: self.minimum_height
        
        Widget:
            size_hint_y: 1
        
        # Результат и объяснение
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height if root.show_explanation else 0
            opacity: 1 if root.show_explanation else 0
            spacing: dp(15)
            
        Label:
            text: root.result_text
            font_size: dp(20)
            bold: True
            size_hint_y: None
            height: dp(30) if root.show_explanation else 0
            color: utils.get_color_from_hex('#4CAF50') if root.is_correct else utils.get_color_from_hex('#F44336')
            
        BoxLayout:
            size_hint_y: None
            height: explanation_label.height + dp(40) if root.show_explanation else 0
            padding: dp(20)
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
                
            Label:
                id: explanation_label
                text: root.explanation
                font_size: dp(16)
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
                color: 0, 0, 0, 1
                halign: 'left'
                valign: 'middle'
            
        # Кнопка следующего вопроса
        Button:
            text: 'Следующий вопрос'
            size_hint: 0.8, None
            height: dp(50)
            pos_hint: {'center_x': 0.5}
            background_color: 0, 0, 0, 0
            color: 1, 1, 1, 1
            opacity: 1 if root.show_explanation else 0
            disabled: not root.show_explanation
            on_press: root.next_question()
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FF7F50')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
        
        # Кнопка "Назад"
        Button:
            text: 'Назад'
            size_hint: 0.8, None
            height: dp(50)
            pos_hint: {'center_x': 0.5}
            background_color: 0,0,0,0
            color: utils.get_color_from_hex('#FF7F50')
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
            on_press: root.manager.current = 'topics'
    
<ResultsScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(40)
        spacing: dp(20)
        
        Label:
            text: 'Успешно!' if root.passed else 'Тест не пройден'
            font_size: dp(32)
            bold: True
            color: utils.get_color_from_hex('#4CAF50') if root.passed else utils.get_color_from_hex('#F44336')
        
        Label:
            text: f'{root.correct_answers} из {root.total_questions} правильных ответов'
            font_size: dp(24)
        
        Label:
            text: 'Ошибки (' + str(root.total_questions - root.correct_answers) + ')' if (root.total_questions - root.correct_answers) > 0 else ''
            font_size: dp(20)
            color: utils.get_color_from_hex('#F44336')
            size_hint_y: None
            height: dp(30) if (root.total_questions - root.correct_answers) > 0 else 0
        
        Label:
            text: root.wrong_topics
            font_size: dp(16)
            text_size: self.width, None
            halign: 'center'
            size_hint_y: None
            height: self.texture_size[1]
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            
            Button:
                text: 'На главную'
                on_press: root.manager.current = 'main'
                background_color: 0,0,0,0
                color: utils.get_color_from_hex('#FF7F50')
                canvas.before:
                    Color:
                        rgba: utils.get_color_from_hex('#FFF5F5')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [15]
            
            Button:
                text: 'Разбор ошибок'
                on_press: root.manager.current = 'review'
                background_color: 0,0,0,0
                color: utils.get_color_from_hex('#FF7F50')
                canvas.before:
                    Color:
                        rgba: utils.get_color_from_hex('#FFF5F5')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [15]
        
        Button:
            text: 'Premium тесты'
            size_hint: 0.6, None
            height: dp(50)
            pos_hint: {'center_x': 0.5}
            background_color: 0,0,0,0
            color: utils.get_color_from_hex('#FF7F50')
            canvas.before:
                Color:
                    rgba: utils.get_color_from_hex('#FFF5F5')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]
''')

class TopicCard(BoxLayout):
    title = StringProperty('')
    questions_count = StringProperty('')
    progress = StringProperty('')
    locked = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(140)

class StatsCard(BoxLayout):
    pass

class Topic:
    def __init__(self, id, title, questions_count, progress=0, locked=False, price=None):
        self.id = id
        self.title = title
        self.questions_count = questions_count
        self.progress = progress
        self.locked = locked
        self.price = price

class MainScreen(Screen):
    questions_completed = NumericProperty(0)
    topics_completed = NumericProperty(0)
    
    def on_enter(self):
        # Загрузка статистики пользователя из Firebase
        if current_user:
            user_ref = db.collection('users').document(current_user['localId'])
            user_data = user_ref.get()
            if user_data.exists:
                data = user_data.to_dict()
                self.questions_completed = data.get('questions_completed', 0)
                self.topics_completed = data.get('topics_completed', 0)

class TopicsScreen(Screen):
    interview_mode = BooleanProperty(False)
    def on_enter(self):
        print("Entering TopicsScreen")  # Debug print
        self.load_topics()
        
    def load_topics(self):
        print("Loading topics...")  # Debug print
        # Очищаем существующие темы
        topics_layout = self.ids.topics_layout
        topics_layout.clear_widgets()
            
        topics_ref = db.collection('topics')
        topics = topics_ref.get()
        print(f"Found {len(list(topics))} topics")  # Debug print
        
        # Создаем список тем для сортировки
        topic_list = []
        for topic in topics:
            topic_data = topic.to_dict()
            topic_data['id'] = topic.id
            topic_list.append(topic_data)
            
        # Сортируем темы (можно добавить свою логику сортировки)
        # topic_list.sort(key=lambda x: x['title'])
            
        # Добавляем отсортированные темы
        for topic_data in topic_list:
            print(f"Processing topic: {topic_data}")  # Debug print
            self.add_topic_card(topic_data)
            
    def add_topic_card(self, topic_data):
        print(f"Creating card for topic: {topic_data['title']}")  # Debug print
        
        # Создаем карточку темы
        card = TopicCard()
        
        # Устанавливаем данные
        card.title = topic_data['title']
        card.questions_count = str(topic_data['questions_count'])
        card.progress = str(topic_data.get('progress', 0))
        card.locked = topic_data.get('locked', False)
        
        # Находим кнопку и привязываем обработчик
        def on_button_press(btn, topic_id=topic_data['id']):
            questions_screen = self.manager.get_screen('questions')
            if not topic_data['locked']:
                self.manager.get_screen('questions').topic_id = topic_id
                questions_screen.training_mode = not self.interview_mode
                self.manager.current = 'questions'
        
        # Ждем следующего кадра для поиска кнопки
        Clock.schedule_once(lambda dt: self.bind_button(card, on_button_press))
        
        self.ids.topics_layout.add_widget(card)
        
    def bind_button(self, card, callback):
        for child in card.walk():
            if isinstance(child, Button):
                child.bind(on_press=callback)
                break

class TrainingScreen(Screen):
    def on_enter(self):
        print("Entering TrainingScreen")
        self.load_topics()

    def load_topics(self):
        topics_layout = self.ids.topics_layout
        topics_layout.clear_widgets()

        topics_ref = db.collection('topics')
        topics = topics_ref.get()

        for topic in topics:
            topic_data = topic.to_dict()
            topic_data['id'] = topic.id
            if not topic_data.get('locked', False):
                self.add_topic_card(topic_data)
    
    def add_topic_card(self, topic_data):
        card = TopicCard()
        card.title = topic_data['title']
        card.questions_count = str(topic_data['questions_count'])
        card.progress = str(topic_data.get('progress', 0))
        card.locked = topic_data.get('locked', False)
        
        def on_button_press(btn, topic_id=topic_data['id']):
            questions_screen = self.manager.get_screen('questions')
            questions_screen.topic_id = topic_id
            questions_screen.training_mode = True
            self.manager.current = 'questions'
        
        Clock.schedule_once(lambda dt: self.bind_button(card, on_button_press))
        self.ids.topics_layout.add_widget(card)

    def bind_button(self, card, callback):
        for child in card.walk():
            if isinstance(child, Button):
                child.bind(on_press=callback)
                break

class AnswerButton(Button):
    background_rgba = ListProperty([0.95, 0.95, 0.95, 1])  # Светло-серый по умолчанию
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = [0, 0, 0, 1]  # Черный текст по умолчанию
        
    def set_correct(self):
        self.background_rgba = [0.2, 0.8, 0.2, 1]  # Зеленый фон
        self.color = [1, 1, 1, 1]  # Белый текст
        
    def set_incorrect(self):
        self.background_rgba = [0.8, 0.2, 0.2, 1]  # Красный фон
        self.color = [1, 1, 1, 1]  # Белый текст
        
    def reset_state(self):
        self.background_rgba = [0.95, 0.95, 0.95, 1]  # Серый фон
        self.color = [0, 0, 0, 1]  # Черный текст

class QuestionsScreen(Screen):
    topic_id = StringProperty('')
    current_question = NumericProperty(0)
    total_questions = NumericProperty(0)
    question_text = StringProperty('')
    explanation = StringProperty('')
    result_text = StringProperty('')
    is_correct = BooleanProperty(False)
    show_explanation = BooleanProperty(False)
    show_next_button = BooleanProperty(False)
    training_mode = BooleanProperty(False)
    wrong_answers = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []
        self.current_options = []
        self.answer_buttons = []
        
    def on_enter(self):
        print(f"Entering QuestionsScreen with topic_id: {self.topic_id}")
        self.show_explanation = False
        self.show_next_button = False
        self.load_questions()
        
    def load_questions(self):
        print(f"Loading questions for topic: {self.topic_id}")  # Debug print
        if not self.topic_id:
            print("No topic_id set!")  # Debug print
            return
            
        questions_ref = db.collection('topics').document(self.topic_id).collection('questions')
        print(f"Questions reference path: {questions_ref._path}")  # Debug print
        
        questions = list(questions_ref.get())
        print(f"Found {len(questions)} questions")  # Debug print
        
        self.questions = []
        for doc in questions:
            question_data = doc.to_dict()
            print(f"Question data: {question_data}")  # Debug print
            # Проверяем наличие всех необходимых полей
            if all(key in question_data for key in ['text', 'options', 'correct_answer', 'explanation']):
                self.questions.append(question_data)
            else:
                print(f"Skipping malformed question: {question_data}")
        if not self.training_mode and len(self.questions) > 20:
            import random
            self.questions = random.sample(self.questions, 20)
            
        self.total_questions = len(self.questions)
        self.current_question = 0
        if self.total_questions > 0:
            self.show_question()
        else:
            self.question_text = "Нет доступных вопросов для этой темы"
            self.current_options = []
            
    def show_question(self):
        self.show_explanation = False
        self.show_next_button = False
        self.explanation = ""
        self.result_text = ""
        if 0 <= self.current_question < self.total_questions:
            question = self.questions[self.current_question]
            
            # Очищаем контейнер с вариантами ответов
            options_container = self.ids.options_container
            options_container.clear_widgets()
            self.answer_buttons = []
            
            # Устанавливаем текст вопроса и варианты ответов
            self.question_text = question['text']
            self.current_options = question['options']
            
            # Создаем кнопки для каждого варианта ответа
            for option in self.current_options:
                btn = AnswerButton()
                btn.text = option
                btn.bind(on_press=lambda btn=btn, opt=option: self.check_answer(btn, opt))
                options_container.add_widget(btn)
                self.answer_buttons.append(btn)
        else:
            print(f"Invalid question index: {self.current_question}")  # Debug print
            
    def check_answer(self, button, selected_option):
        if not self.show_next_button:  # Предотвращаем повторное нажатие
            question = self.questions[self.current_question]
            self.is_correct = selected_option == question['correct_answer']
            
            # Подсвечиваем выбранную кнопку
            if self.is_correct:
                button.set_correct()
            else:
                button.set_incorrect()
                wrong_answer = question.copy()
                wrong_answer['user_answer'] = selected_option
                self.wrong_answers.append(wrong_answer)
                # Подсвечиваем правильный ответ зеленым
                for btn in self.answer_buttons:
                    if btn.text == question['correct_answer']:
                        btn.set_correct()
            
            # Показываем результат и объяснение
            self.result_text = "Правильно!" if self.is_correct else f"Неправильно. Правильный ответ: {question['correct_answer']}"
            self.explanation = question['explanation']
            self.show_explanation = True
            self.show_next_button = True
            
            # Отключаем все кнопки ответов кроме выбранной и правильной
            for btn in self.answer_buttons:
                if btn != button and btn.text != question['correct_answer']:
                    btn.disabled = True
                    btn.color = [0.7, 0.7, 0.7, 1]  # Серый текст для неактивных кнопок
    
    def next_question(self):
        self.current_question += 1
        if self.current_question < self.total_questions:
            self.show_question()
        else:
            # Все вопросы пройдены
            if not self.training_mode:
                correct = sum(1 for q in self.questions if q['correct_answer'] == q.get('user_answer', ''))
                wrong_topics = " * ".join(set(q.get('topic', '') for q in self.wrong_answers))

                results_screen = self.manager.get_screen('results')
                results_screen.show_results(correct, self.total_questions, wrong_topics)
                self.manager.current = 'results'
            else:
                self.manager.current = 'topics'

class ResultsScreen(Screen):
    correct_answers = NumericProperty(0)
    total_questions = NumericProperty(0)
    passed = BooleanProperty(False)
    wrong_topics = StringProperty('')
    
    def show_results(self, correct, total, wrong_topics):
        self.correct_answers = correct
        self.total_questions = total
        self.passed = (total - correct) < 3  # Меньше 3 ошибок
        self.wrong_topics = wrong_topics

class QuizApp(App):
    def build(self):
        self.title = 'Intervirium'
        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(TopicsScreen(name='topics'))
        self.sm.add_widget(TrainingScreen(name='training'))
        self.sm.add_widget(QuestionsScreen(name='questions'))
        self.sm.add_widget(ResultsScreen(name='results'))
        return self.sm
    
    def start_topic(self, topic_id):
        print(f"Starting topic: {topic_id}")  # Debug print
        # Проверяем, заблокирована ли тема
        topic_ref = db.collection('topics').document(topic_id)
        topic = topic_ref.get()
        
        if topic.exists:
            print(f"Topic exists: {topic.to_dict()}")  # Debug print
            topic_data = topic.to_dict()
            if topic_data.get('locked', False):
                print("Topic is locked")  # Debug print
                # TODO: Показать экран оплаты
                self.sm.current = 'premium'
            else:
                print("Topic is unlocked, loading questions")  # Debug print
                # Загружаем вопросы для темы
                questions_screen = self.sm.get_screen('questions')
                questions_screen.topic_id = topic_id
                self.sm.current = 'questions'
        else:
            print(f"Topic {topic_id} not found")  # Debug print

    def on_pause(self):
        # Сохраняем состояние приложения при паузе
        return True
    
    def on_resume(self):
        # Восстанавливаем состояние приложения при возобновлении
        pass
    
    def on_stop(self):
        # Очищаем ресурсы при остановке приложения
        pass

if __name__ == '__main__':
    QuizApp().run()
