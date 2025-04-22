from firebase_config import db

def upload_topics():
    # Создаем тестовую тему с вопросами
    python_topic = {
        'title': 'Python Junior',
        'questions_count': 3,
        'locked': False
    }
    
    # Создаем документ для темы с правильным ID
    topic_ref = db.collection('topics').document('python-junior')
    topic_ref.set(python_topic)
    print(f"Created topic document at: {topic_ref._path}")  # Debug print
    
    # Создаем вопросы для темы
    questions = [
        {
            'text': 'Что такое Python?',
            'options': [
                'Язык программирования',
                'Вид змеи',
                'Операционная система',
                'База данных'
            ],
            'correct_answer': 'Язык программирования',
            'explanation': 'Python - это высокоуровневый язык программирования общего назначения.'
        },
        {
            'text': 'Какой оператор используется для определения блока кода в Python?',
            'options': [
                'Фигурные скобки {}',
                'Двоеточие :',
                'Точка с запятой ;',
                'Круглые скобки ()'
            ],
            'correct_answer': 'Двоеточие :',
            'explanation': 'В Python блоки кода определяются с помощью отступов после двоеточия.'
        },
        {
            'text': 'Какой тип данных используется для хранения последовательности элементов в Python?',
            'options': [
                'int',
                'str',
                'list',
                'bool'
            ],
            'correct_answer': 'list',
            'explanation': 'List (список) - это упорядоченная последовательность элементов в Python.'
        }
    ]
    
    # Добавляем вопросы в подколлекцию
    questions_ref = topic_ref.collection('questions')
    for i, question in enumerate(questions):
        question_doc = questions_ref.document(f'question_{i+1}')
        question_doc.set(question)
        print(f"Added question {i+1} at: {question_doc._path}")  # Debug print
    
    print("Тема и вопросы успешно загружены!")

if __name__ == '__main__':
    upload_topics() 