import telebot
from telebot import types
from db import Database

API_TOKEN = 'INSERT YOUR TOKEN HERE'
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

def set_commands_for_user(user_id, role):
    if role == 'student':
        bot.set_my_commands(student_commands, scope=types.BotCommandScopeChat(user_id))
    elif role == 'teacher':
        bot.set_my_commands(teacher_commands, scope=types.BotCommandScopeChat(user_id))
    else:
        bot.set_my_commands([], scope=types.BotCommandScopeChat(user_id))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    telegram_id = message.from_user.id
    role, group_name, last_name, first_name, middle_name = db.get_student_info(telegram_id)

    if role:
        set_commands_for_user(telegram_id, role)
        if role == 'student' and group_name:
            bot.reply_to(message, f"Добро пожаловать! Ваша роль: студент. Ваша учебная группа: {group_name}.")
        else:
            bot.reply_to(message, f"Добро пожаловать! Ваша роль: преподаватель.")
    else:
        bot.reply_to(message, "Вашего ID нет в базе данных. Пожалуйста, обратитесь к администратору.")



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

    if role == 'teacher':
        msg = bot.reply_to(message, "Введите номера групп через пробел в формате xxx-xx:")
        bot.register_next_step_handler(msg, process_group_selection)
    else:
        bot.reply_to(message, "Эта команда доступна только преподавателям.")

def process_group_selection(message):
    group_names = message.text.split()
    msg = bot.reply_to(message, "Введите сообщение для отправки выбранным группам:")
    bot.register_next_step_handler(msg, lambda m: send_message_to_groups(m, group_names))

def send_message_to_groups(message, group_names):
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
            bot.send_message(
                student_id,
                f"Сообщение от {teacher_name} ({teacher_department}):\n\n{message.text}"
            )
        bot.reply_to(message, "Сообщение успешно отправлено всем студентам выбранных групп.")
    else:
        bot.reply_to(message, "Не удалось найти студентов для указанных групп или произошла ошибка при получении списка студентов.")


    if student_ids:
        for student_id in student_ids:
            bot.send_message(student_id, f"Сообщение от {teacher_name}:\n\n{message.text}")
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
            bot.register_next_step_handler(msg, lambda m: send_message_to_teacher(m, matching_teachers[0][0]))
        else:
            bot.reply_to(message, "Преподаватель с таким именем не найден. Проверьте правильность ввода или попробуйте снова.")

def send_message_to_teacher(message, teacher_id):
    student_id = message.from_user.id
    student_info = db.get_student_info_by_id(student_id)
    if student_info:
        student_name = f"{student_info['last_name']} {student_info['first_name']} {student_info['middle_name']}"
        student_group = student_info['group_name']
        bot.send_message(
            teacher_id,
            f"Сообщение от студента {student_name} ({student_group}):\n{message.text}"
        )
        bot.reply_to(message, "Сообщение отправлено преподавателю.")
    else:
        bot.reply_to(message, "Произошла ошибка при получении информации о студенте.")

@bot.message_handler(commands=['message_student'])
def initiate_teacher_message(message):
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
            bot.register_next_step_handler(msg, lambda m: send_message_to_student(m, matching_student[0][0]))
        else:
            bot.reply_to(message, "Студент с таким именем не найден. Проверьте правильность ввода или попробуйте снова.")

def send_message_to_student(message, student_id):
    teacher_id = message.from_user.id
    teacher_info = db.get_teacher_info_all(teacher_id)
    teacher_department = teacher_info[6]
    if teacher_info:
        teacher_name = f"{teacher_info[1]} {teacher_info[2]} {teacher_info[3]}"
        bot.send_message(
            student_id,
            f"Сообщение от преподавателя {teacher_name} Кафедра:{teacher_department}:\n{message.text}"
        )
        bot.reply_to(message, "Сообщение отправлено студенту.")
    else:
        bot.reply_to(message, "Произошла ошибка при получении информации о преподавателе.")


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


if __name__ == '__main__':
    print("Bot is polling...")
    bot.polling()
