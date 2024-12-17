from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from crud_functions import add_users, initiate_db,  get_all_products, is_included
import re
api = '---'
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

initiate_db()

start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
button3 = KeyboardButton(text='Рассчитать')
button4 = KeyboardButton(text='Информация')
button5 = KeyboardButton(text='Купить')
button10 = KeyboardButton(text='Регистрация')
start_kb.add(button3, button4)
start_kb.row(button5, button10)

kb_calories = InlineKeyboardMarkup()
button = InlineKeyboardButton(text= 'Рассчитать норму калорий', callback_data = 'calories')
button2 = InlineKeyboardButton(text= 'Формулы расчета', callback_data= 'formuls')
kb_calories.add(button, button2)

kb_buy = InlineKeyboardMarkup()
button6 = InlineKeyboardButton(text='Logitech G102', callback_data = 'mouse')
button7 = InlineKeyboardButton(text='Logitech G304', callback_data= 'mouse2')
button8 = InlineKeyboardButton(text='Logitech G PRO', callback_data= 'mouse3')
button9 = InlineKeyboardButton(text='ARDOR GAMING Fury', callback_data= 'mouse4')
kb_buy.add(button6, button7, button8, button9)


class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = State()

def lat_let(username):
    return bool(re.match('^[a-zA-Z]+$', username))


@dp.message_handler(text='Регистрация')
async def reg(message):
    await message.answer('Введите имя пользователя (только латинский алфавит):')
    await RegistrationState.username.set()

@dp.message_handler(state=RegistrationState.username)
async def set_username(message, state: FSMContext):
    if not lat_let(message.text):
        await message.answer(
            "Ошибка: Имя пользователя должно содержать только латинские буквы. Попробуйте снова."
        )
        return

    if is_included(message.text):
        await message.answer('Этот пользователь уже зарегистрирован.')
        return

    await state.update_data(username=message.text)
    await message.answer('Введите ваш email:')
    await RegistrationState.email.set()


@dp.message_handler(state=RegistrationState.email)
async def set_email(message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer('Введите свой возраст')
    await RegistrationState.age.set()

@dp.message_handler(state=RegistrationState.age)
async def set_agee(message, state: FSMContext):
    try:
        age=int(message.text)
    except ValueError:
        await message.answer('Пожалуйста, введите правильный возраст (целое число).')

    await state.update_data(age=age)

    user_data = await state.get_data()
    add_users(user_data['username'], user_data['email'], user_data['age'])

    await message.answer('Регистрация прошла успешно')
    await state.finish()


@dp.message_handler(text= 'Купить')
async def buy(message):
    products = get_all_products()

    for idx, product in enumerate(products, start=1):
        title, description, price = product
        image_path = f'files/{idx}.webp'

        with open(image_path, 'rb') as img:
            await message.answer_photo(img, caption=f'Название: {title} | Описание: {description} | Цена: {price}',reply_markup=start_kb)

    await message.answer('Выберите продукт для покупки:', reply_markup=kb_buy)


@dp.callback_query_handler(text = ['mouse'])
async def buy_mouse(call):
    await call.message.answer('Вы успешно приобрели продукт!')
    await call.answer()

@dp.message_handler(text = 'Рассчитать')
async def main_menu(message):
    await message.answer('Выерите опцию:', reply_markup = kb_calories)

@dp.callback_query_handler(text = 'formuls')
async  def get_formuls(call):
    await call.message.answer('для женщин: 10 x вес (кг) + 6,25 x рост (см) – 5 x возраст (г) – 161')
    await call.answer()

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

@dp.message_handler(commands=['start'])
async def start(message):
    await message.answer('Привет! Я бот помогающий твоему здоровью.', reply_markup= start_kb)


@dp.callback_query_handler(text = ['calories'])
async def set_age(call):
    await call.message.answer('Введите свой возраст:')
    await UserState.age.set()
    await call.answer()


@dp.message_handler(state = UserState.age)
async def set_growth(message, state):
    await state.update_data(age = int(message.text))
    await message.answer('Введите свой рост:')
    await UserState.growth.set()


@dp.message_handler(state = UserState.growth)
async def set_weight(message, state):
    await state.update_data(growth = int(message.text))
    await message.answer('Введите свой вес:')
    await UserState.weight.set()


@dp.message_handler(state = UserState.weight)
async def send_calories(message, state):
    await state.update_data(weight = int(message.text))

    data = await state.get_data()
    age = data['age']
    growth = data['growth']
    weight = data['weight']

    colories = 10 * weight + 6.25 * growth - 5 * age - 161

    await message.answer(f'Ваша норма калорий: {colories:.0f}, ккал в день')
    await state.finish()



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
