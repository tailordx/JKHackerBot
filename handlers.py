from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import SYMBOLS
import db
from lexicon import LEXICON, LEXICON_DATA

router = Router()


class InputForm(StatesGroup):
    data = State()
    confirm = State()


@router.message(Command('start'), StateFilter(default_state))
async def start_handler(message: Message):
    await message.answer(text=LEXICON['start'])


@router.message(Command('help'), StateFilter(default_state))
async def start_handler(message: Message):
    await message.answer(text=LEXICON['help'])


@router.message(Command('submit'), StateFilter(default_state))
async def submit_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if (r := db.get(user_id)) is not None:
        _, readings = r
    else:
        readings = [None] * len(SYMBOLS)
    await state.set_state(InputForm.data)
    await state.set_data({'index': 0, 'readings': readings})
    reply = (
        f"{LEXICON_DATA[SYMBOLS[0]]}\n"
        f"{LEXICON['current_value']}: {readings[0]}\n"
        f"{LEXICON['new_value']}:"
    )
    await message.answer(text=reply)


@router.message(~StateFilter(default_state), Command('cancel') or F.text == LEXICON['cancel'])
async def cancel_handler(message: Message, state: FSMContext):
    await message.answer(text=LEXICON['submission_cancel'], reply_markup=ReplyKeyboardRemove())
    await state.clear()


@router.message(StateFilter(InputForm.data))
async def input_data_handler(message: Message, state: FSMContext):
    value = message.text
    data = await state.get_data()
    index = data['index']
    readings = data['readings']
    if value != '-':
        if value.isdigit():
            old_value = readings[index]
            new_value = int(value)
            if old_value is None or new_value >= old_value:
                readings[index] = new_value
            else:
                await message.answer(text=LEXICON['input_is_less'])
                return
        else:
            await message.answer(text=LEXICON['wrong_input'])
            return
    index += 1
    if index < len(SYMBOLS):
        reply = (
            f"{LEXICON_DATA[SYMBOLS[index]]}\n"
            f"{LEXICON['current_value']}: {readings[index]}\n"
            f"{LEXICON['new_value']}:"
        )
        await message.answer(text=reply)
    else:
        reply = f"{LEXICON['check_prompt']}:\n\n"
        for i, symbol in enumerate(SYMBOLS):
            reply += f"{LEXICON_DATA[symbol]}: {readings[i]}\n"
        keyboard = [[
            KeyboardButton(text=LEXICON['confirm']),
            KeyboardButton(text=LEXICON['cancel']),
        ]]
        reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        await message.answer(text=reply, reply_markup=reply_markup)
        await state.set_state(InputForm.confirm)
    await state.update_data(index=index, readings=readings)


@router.message(StateFilter(InputForm.confirm), F.text.in_({'confirm', LEXICON['confirm']}))
async def input_confirm_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    readings = data['readings']
    if db.submit(user_id, readings) == 0:
        reply = LEXICON['submission_success']
    else:
        reply = LEXICON['submission_error']
    await message.answer(text=reply, reply_markup=ReplyKeyboardRemove())
    await state.clear()


@router.message(StateFilter(InputForm.confirm))
async def input_confirm_handler(message: Message):
    await message.answer(text=LEXICON['confirm_prompt'])


@router.message(StateFilter(default_state), Command('get'))
async def get_handler(message: Message):
    r = db.get(message.from_user.id)
    if r is not None:
        timestamp, readings = r
        reply = f"{LEXICON['get_success']}:\n\n"
        for i, symbol in enumerate(SYMBOLS):
            reply += f"{LEXICON_DATA[symbol]}: {readings[i]}\n"
        reply += f"\n{LEXICON['timestamp']}: {timestamp}"
        await message.answer(text=reply)
    else:
        await message.answer(text=LEXICON['get_fail'])


@router.message(StateFilter(default_state))
async def get_handler(message: Message):
    await message.answer(text=LEXICON['help'])
