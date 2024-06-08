import telebot
from telebot import types
from pyzbar.pyzbar import decode
from PIL import Image
import io
from db import Database

API_TOKEN = 'YOUR_API_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

db = Database('your_database.db')

student_commands = [
    types.BotCommand('start', 'Начать'),
    types.BotCommand('schedule', 'Посмотреть расписание'),
    types.BotCommand('message_teacher', 'Написать преподавателю'),
    types.BotCommand('subject_info', 'Информация о предмете')
]

teacher_commands = [
    types.BotCommand('start', 'Начать'),
    types.BotCommand('broadcast', 'Отправить сообщение группам'),
    types.BotCommand('message_student', 'Написать студенту')
]

depot_commands = [
    types.BotCommand('start', 'Начать'),
    types.BotCommand('message_student', 'Написать студенту'),
    types.BotCommand('message_teacher', 'Написать преподавателю'),
    types.BotCommand('broadcast', 'Отправить сообщение группам'),
    types.BotCommand('delete', 'Удалить пользователя')
]

db.update_user_activity_status()

def set_commands_for_user(user_id, role):
    if role == 'student':
        bot.set_my_commands(student_commands, scope=types.BotCommandScopeChat(user_id))
    elif role == 'teacher':
        bot.set_my_commands(teacher_commands, scope=types.BotCommandScopeChat(user_id))
    elif role == 'depot':
        bot.set_my_commands(depot_commands, scope=types.BotCommandScopeChat(user_id))
    else:
        bot.set_my_commands([], scope=types.BotCommandScopeChat(user_id))


@bot.message_handler(commands=['register'])
def register_user(message):
    msg = bot.reply_to(message, "Пожалуйста, отправьте фото QR-кода для регистрации.")
    bot.register_next_step_handler(msg, process_qr_code)


def process_qr_code(message):
    if message.photo:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image = Image.open(io.BytesIO(downloaded_file))
        decoded_objects = decode(image)

        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")
            register_user_from_qr_data(message.chat.id, qr_data)
        else:
            bot.reply_to(message, "Не удалось распознать QR-код. Пожалуйста, попробуйте снова.")
    else:
        bot.reply_to(message, "Пожалуйста, отправьте фото QR-кода.")


def register_user_from_qr_data(chat_id, qr_data):
    user_data = qr_data.split(',')
    last_name, first_name, middle_name, roles, group_id, department, start_date, end_date = user_data
    telegram_id = message.from_user.id

    existing_user = db.get_user_by_name_and_group(last_name, first_name, middle_name, group_id)
    if existing_user:
        bot.send_message(chat_id, "Пользователь с такими данными уже зарегистрирован.")
    else:
        db.add_user(telegram_id, last_name, first_name, middle_name, roles, group_id, department, start_date, end_date)
        bot.send_message(chat_id, f"Пользователь {last_name} {first_name} успешно зарегистрирован.")
@bot.message_handler(commands=['start'])
def send_welcome(message):
    telegram_id = message.from_user.id
    role, group_name, last_name, first_name, middle_name, is_active = db.get_student_info(telegram_id)

    if set_active:
        if role:
            set_commands_for_user(telegram_id, role)
            if role == 'student' and group_name:
                bot.reply_to(message, f"Добро пожаловать! Ваша роль: студент. Ваша учебная группа: {group_name}.")
            elif role == 'teacher':
                bot.reply_to(message, f"Добро пожаловать! Ваша роль: преподаватель.")
            elif role == 'depot':
                bot.reply_to(message, f"Добро пожаловать! Ваша роль: учебная часть.")
        else:
            bot.reply_to(message, "Вашего ID нет в базе данных. Пожалуйста, обратитесь к администратору.")
    else:
        bot.reply_to(message, "Ваш аккаунт неактивен. Обратитесь к администратору для поддержки.")

@bot.message_handler(commands=['schedule'])
def show_schedule(message):
    telegram_id = message.from_user.id
    role, group_name, last_name, first_name, middle_name = db.get_student_info(telegram_id)
    if role:
        if role == 'student' and group_name:
            group_id = db.get_group_id_by_student_id(telegram_id)
            if group_id:
                schedule = db.view_group_schedule(group_id)
                if schedule:
                    with open("schedule.jpg", "wb") as file:
                        file.write(schedule)
                    with open("schedule.jpg", "rb") as file:
                        bot.send_photo(message.chat.id, file)
                else:
                    bot.reply_to(message, f"У вашей группы ({group_name}) нет расписания.")
            else:
                bot.reply_to(message, f"Не удалось найти вашу группу.")
        else:
            bot.reply_to(message, "Эта команда доступна только студентам.")
    else:
        bot.reply_to(message, "Вашего ID нет в базе данных. Пожалуйста, обратитесь к администратору.")

@bot.message_handler(commands=['broadcast'])
def send_broadcast(message):
    telegram_id = message.from_user.id
    role = db.get_user_role(telegram_id)

    if role == 'teacher' or role == 'depot':
        msg = bot.reply_to(message, "Введите номера групп через пробел в формате xxx-xx:")
        bot.register_next_step_handler(msg, process_group_selection)
    else:
        bot.reply_to(message, "Эта команда доступна только преподавателям.")

def process_group_selection(message):
    group_names = message.text.split()
    msg = bot.reply_to(message, "Введите сообщение для отправки выбранным группам:")
    bot.register_next_step_handler(msg, lambda m: process_broadcast_message(m, group_names))

def process_broadcast_message(message, group_names):
    if message.content_type == 'text':
        send_message_to_groups(message, group_names, message.text)
    elif message.content_type == 'photo':
        send_message_to_groups(message, group_names, message.photo[-1].file_id, content_type='photo')
    elif message.content_type == 'document':
        send_message_to_groups(message, group_names, message.document.file_id, content_type='document')

def send_message_to_groups(message, group_names, content, content_type='text'):
    student_ids = []
    teacher_id = message.from_user.id
    teacher_info = db.get_teacher_info_all(teacher_id)
    teacher_name = f"{teacher_info[1]} {teacher_info[2]} {teacher_info[3]}"
    teacher_department = teacher_info[6]

    for group_name in group_names:
        group_id = db.get_group_id_by_name(group_name)
        if group_id:
            students = db.get_students_by_group_id(group_id)
            student_ids.extend([student[0] for student in students])

    student_ids = list(set(student_ids) - {teacher_id})

    if student_ids:
        for student_id in student_ids:
            if content_type == 'text':
                bot.send_message(student_id, f"Сообщение от {teacher_name} ({teacher_department}):\n\n{content}")
            elif content_type == 'photo':
                bot.send_photo(student_id, content, caption=f"Сообщение от {teacher_name} ({teacher_department}):")
            elif content_type == 'document':
                bot.send_document(student_id, content, caption=f"Сообщение от {teacher_name} ({teacher_department}):")
        bot.reply_to(message, "Сообщение успешно отправлено всем студентам выбранных групп.")
    else:
        bot.reply_to(message, "Не удалось найти студентов для указанных групп или произошла ошибка при получении списка студентов.")

@bot.message_handler(commands=['message_teacher'])
def initiate_teacher_message(message):
    msg = bot.reply_to(message, "Введите полное ФИО преподавателя (Фамилия Имя Отчество):")
    bot.register_next_step_handler(msg, process_teacher_name)

def process_teacher_name(message):
    teacher_name = message.text.strip()
    if len(teacher_name.split()) < 3:
        last_name = teacher_name.split()[0]
        matching_teachers = db.find_teachers_by_last_name(last_name)
        if matching_teachers:
            response = "Найдено несколько преподавателей с такой фамилией. Введите полное ФИО:\n"
            for teacher in matching_teachers:
                response += f"{teacher[1]} {teacher[2]} {teacher[3]}\n"
            msg = bot.reply_to(message, response)
            bot.register_next_step_handler(msg, process_teacher_name)
        else:
            bot.reply_to(message, "Преподаватель с такой фамилией не найден. Проверьте правильность ввода или попробуйте снова.")
    else:
        matching_teachers = db.find_teachers_by_name(teacher_name)
        if len(matching_teachers) == 1:
            msg = bot.reply_to(message, "Введите сообщение для отправки преподавателю:")
            bot.register_next_step_handler(msg, lambda m: process_teacher_message(m, matching_teachers[0][0]))
        else:
            bot.reply_to(message, "Преподаватель с таким именем не найден. Проверьте правильность ввода или попробуйте снова.")

def process_teacher_message(message, teacher_id):
    if message.content_type == 'text':
        send_message_to_teacher(message, teacher_id, message.text)
    elif message.content_type == 'photo':
        send_message_to_teacher(message, teacher_id, message.photo[-1].file_id, content_type='photo')
    elif message.content_type == 'document':
        send_message_to_teacher(message, teacher_id, message.document.file_id, content_type='document')

def send_message_to_teacher(message, teacher_id, content, content_type='text'):
    student_id = message.from_user.id
    student_info = db.get_student_info_by_id(student_id)
    student_name = f"{student_info['last_name']} {student_info['first_name']} {student_info['middle_name']}"
    student_group = student_info['group_name']
    if content_type == 'text':
        bot.send_message(teacher_id, f"Сообщение от студента {student_name} ({student_group}):\n{content}")
    elif content_type == 'photo':
        bot.send_photo(teacher_id, content, caption=f"Сообщение от студента {student_name} ({student_group}):")
    elif content_type == 'document':
        bot.send_document(teacher_id, content, caption=f"Сообщение от студента {student_name} ({student_group}):")
    bot.reply_to(message, "Сообщение отправлено преподавателю.")

@bot.message_handler(commands=['message_student'])
def initiate_student_message(message):
    msg = bot.reply_to(message, "Введите полное ФИО студента (Фамилия Имя Отчество):")
    bot.register_next_step_handler(msg, process_student_name)

def process_student_name(message):
    student_name = message.text.strip()
    if len(student_name.split()) < 3:
        last_name = student_name.split()[0]
        matching_students = db.find_students_by_last_name(last_name)
        if matching_students:
            response = "Найдено несколько студентов с такой фамилией. Введите полное ФИО:\n"
            for student in matching_students:
                response += f"{student[1]} {student[2]} {student[3]} ({student[4]})\n"
            msg = bot.reply_to(message, response)
            bot.register_next_step_handler(msg, process_student_name)
        else:
            bot.reply_to(message, "Студент с такой фамилией не найден. Проверьте правильность ввода или попробуйте снова.")
    else:
        matching_student = db.find_students_by_name(student_name)
        if len(matching_student) == 1:
            msg = bot.reply_to(message, "Введите сообщение для отправки студенту:")
            bot.register_next_step_handler(msg, lambda m: process_student_message(m, matching_student[0][0]))
        else:
            bot.reply_to(message, "Студент с таким именем не найден. Проверьте правильность ввода или попробуйте снова.")

def process_student_message(message, student_id):
    if message.content_type == 'text':
        send_message_to_student(message, student_id, message.text)
    elif message.content_type == 'photo':
        send_message_to_student(message, student_id, message.photo[-1].file_id, content_type='photo')
    elif message.content_type == 'document':
        send_message_to_student(message, student_id, message.document.file_id, content_type='document')

def send_message_to_student(message, student_id, content, content_type='text'):
    teacher_id = message.from_user.id
    teacher_info = db.get_teacher_info_all(teacher_id)
    teacher_name = f"{teacher_info[1]} {teacher_info[2]} {teacher_info[3]}"
    teacher_department = teacher_info[6]
    if content_type == 'text':
        bot.send_message(student_id, f"Сообщение от преподавателя {teacher_name} Кафедра: {teacher_department}:\n{content}")
    elif content_type == 'photo':
        bot.send_photo(student_id, content, caption=f"Сообщение от преподавателя {teacher_name} Кафедра: {teacher_department}:")
    elif content_type == 'document':
        bot.send_document(student_id, content, caption=f"Сообщение от преподавателя {teacher_name} Кафедра: {teacher_department}:")
    bot.reply_to(message, "Сообщение отправлено студенту.")

@bot.message_handler(commands=['subject_info'])
def request_subject_info(message):
    msg = bot.reply_to(message, "Введите название предмета или его короткое название:")
    bot.register_next_step_handler(msg, process_subject_name)

def process_subject_name(message):
    subject_name = message.text.strip()
    subject_info = db.get_subject_info(subject_name)

    if subject_info:
        subject_details = (
            f"Название предмета: {subject_info['name']}\n"
            f"Информация: {subject_info['info']}\n"
            f"Короткое название: {subject_info['short_name']}\n"
            f"Тип занятия: {subject_info['class_type']}"
        )
        bot.reply_to(message, subject_details)
    else:
        bot.reply_to(message, "Предмет не найден. Проверьте правильность ввода или попробуйте снова.")

@bot.message_handler(commands=['delete'])
def delete_user_command(message):
    telegram_id = message.from_user.id
    role = db.get_user_role(telegram_id)

    if role == 'depot':
        msg = bot.reply_to(message, "Введите роль пользователя для удаления (student/teacher):")
        bot.register_next_step_handler(msg, process_role_for_deletion)
    else:
        bot.reply_to(message, "Эта команда доступна только для учебной части.")

def process_role_for_deletion(message):
    role_to_delete = message.text.strip().lower()
    if role_to_delete == 'student':
        msg = bot.reply_to(message, "Введите название учебной группы:")
        bot.register_next_step_handler(msg, process_group_for_student_deletion)
    elif role_to_delete == 'teacher':
        msg = bot.reply_to(message, "Введите название кафедры:")
        bot.register_next_step_handler(msg, process_department_for_teacher_deletion)
    else:
        bot.reply_to(message, "Некорректная роль. Пожалуйста, введите student или teacher.")

def process_group_for_student_deletion(message):
    group_name = message.text.strip()
    msg = bot.reply_to(message, "Введите полное ФИО студента (Фамилия Имя Отчество):")
    bot.register_next_step_handler(msg, lambda m: process_student_name_for_deletion(m, group_name))

def process_student_name_for_deletion(message, group_name):
    student_name = message.text.strip()
    student = db.find_students_by_name_and_group(student_name, group_name)
    if student:
        db.delete_user(student['id'])
        bot.reply_to(message, f"Студент {student_name} из группы {group_name} успешно удален.")
    else:
        bot.reply_to(message, "Студент не найден. Проверьте данные и попробуйте снова.")

def process_department_for_teacher_deletion(message):
    department = message.text.strip()
    msg = bot.reply_to(message, "Введите полное ФИО преподавателя (Фамилия Имя Отчество):")
    bot.register_next_step_handler(msg, lambda m: process_teacher_name_for_deletion(m, department))

def process_teacher_name_for_deletion(message, department):
    teacher_name = message.text.strip()
    teacher = db.find_teachers_by_name_and_department(teacher_name, department)
    if teacher:
        db.delete_user(teacher['id'])
        bot.reply_to(message, f"Преподаватель {teacher_name} из кафедры {department} успешно удален.")
    else:
        bot.reply_to(message, "Преподаватель не найден. Проверьте данные и попробуйте снова.")

if __name__ == '__main__':
    print("Bot is polling...")
    bot.polling()
