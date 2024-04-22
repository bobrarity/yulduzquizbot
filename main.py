from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from quiz import quiz, telegram_key
import yaml
import random


class Form(StatesGroup):
    lang = State()
    topic = State()
    q_type = State()
    difficulty = State()
    answering = State()
    finished = State()


messages = {
    'start': {
        'english': "Welcome to the quiz! Now, please enter a topic:",
        'russian': "Добро пожаловать в викторину! Теперь, пожалуйста, введите тему:",
        'uzbek': "Viktorinaga xush kelibsiz! Endi, iltimos, mavzuni yozing:"
    },
    'q_type': {
        'english': "Please choose the type of the question format:",
        'russian': "Выберите формат вопроса:",
        'uzbek': "Savol turlaridan birini tanlang:"
    },
    'wait': {
        'english': "Generating your quiz...",
        'russian': "Создание вашей викторины...",
        'uzbek': "Sizning viktorinangiz yaratilmoqda..."
    }
}

bot = Bot(token=telegram_key)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🇬🇧 English", callback_data='english'),
                 InlineKeyboardButton("🇷🇺 Русский", callback_data='russian'),
                 InlineKeyboardButton("🇺🇿 O'zbek", callback_data='uzbek'))
    await message.answer('Please choose your language.', reply_markup=keyboard)
    await Form.lang.set()


@dp.callback_query_handler(lambda c: c.data in ['english', 'russian', 'uzbek'], state=Form.lang)
async def get_lang(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    language = callback_query.data
    await state.update_data(lang=language)
    await callback_query.message.edit_text(messages['start'][language])
    await Form.topic.set()


@dp.message_handler(state=Form.topic)
async def get_topic(message: types.Message, state: FSMContext):
    topic = message.text
    await state.update_data(topic=topic)
    user_data = await state.get_data()
    language = user_data['lang']
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Multiple Choice", callback_data='multiple'),
                 InlineKeyboardButton(text="True/False", callback_data='true_false'))
    await message.answer(messages['q_type'][language], reply_markup=keyboard)
    await Form.q_type.set()


@dp.callback_query_handler(lambda c: c.data in ['multiple', 'true_false'], state=Form.q_type)
async def get_q_type(callback_query: types.CallbackQuery, state: FSMContext):
    q_type = callback_query.data
    await state.update_data(q_type=q_type)
    user_data = await state.get_data()
    lang = user_data['lang']
    topic = user_data['topic']
    await callback_query.message.edit_text(messages['wait'][lang])

    quiz(topic, lang, q_type)

    with open('questions.yaml', 'r') as file:
        questions = yaml.safe_load(file)['questions']

    await dp.storage.set_data(chat=callback_query.message.chat.id,
                              data={'questions': questions, 'current_question_index': 0, 'score': 0})

    await ask_question(callback_query.message)


async def ask_question(message: types.Message):
    user_data = await dp.storage.get_data(chat=message.chat.id)
    questions = user_data['questions']
    current_index = user_data['current_question_index']

    if current_index < len(questions):
        question = questions[current_index]
        keyboard = InlineKeyboardMarkup(row_width=1)

        options = [opt if isinstance(opt, str) else opt['correct'] for opt in question['a']]

        random.shuffle(options)

        for option in options:
            keyboard.add(InlineKeyboardButton(option, callback_data=option))

        await message.answer(question['q'], reply_markup=keyboard)
        await Form.answering.set()
    else:
        await message.answer(f"Quiz finished! Your score: {user_data['score']}/{len(questions)}")
        await Form.finished.set()


@dp.callback_query_handler(state=Form.answering)
async def check_answer(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    user_data = await dp.storage.get_data(chat=callback_query.message.chat.id)
    questions = user_data['questions']
    current_index = user_data['current_question_index']
    correct_answer = [item for item in questions[current_index]['a'] if isinstance(item, dict)][0]['correct']

    if callback_query.data == correct_answer:
        score = user_data['score'] + 1
        response = "Correct!"
    else:
        score = user_data['score']
        response = f"Incorrect. The correct answer was: {correct_answer}"

    await dp.storage.update_data(chat=callback_query.message.chat.id,
                                 data={'score': score, 'current_question_index': current_index + 1})
    await bot.send_message(chat_id=chat_id, text=response)
    await ask_question(callback_query.message)


if __name__ == '__main__':
    executor.start_polling(dp)
