# bot.py
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
)
from database import Database

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states
(
    START, NAME, USER_ID, GROUP, PHONE, PASSWORD, MAIN_MENU, ORDERS, CREATE_ORDER, ORDER_STATUS,
    CALENDAR, SETTINGS, CHOOSE_DATE, CHOOSE_COUNT, CHOOSE_TYPE, REVIEW_ORDER, DELETE_USER, DELETE_ORDER,
    LOGIN_USER, LOGIN_PASSWORD, EDIT_ACCOUNT_NAME, EDIT_ACCOUNT_GROUP, EDIT_ACCOUNT_PHONE, ADMIN_MAIN, ADMIN_ORDERS,
    ADMIN_USERS, ADMIN_CALENDAR, ADMIN_DATE_ORDERS, ADMIN_CHANGE_STATUS, ADMIN_EDIT_USER_ID, ADMIN_RESET_PASSWORD,
    ADMIN_SET_LIMIT, EDIT_ACCOUNT, ADMIN_UPDATE_ORDER_STATUS, ADMIN_CONFIRM_STATUS, SETTINGS_NOTIFICATION
) = range(36)

user_data = {}
order_data = {}
db = Database()


def start(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.message.from_user.id)
        user = db.get_user_by_id(user_id)
        admin = db.get_admin_by_id(user_id)

        if user:
            context.user_data["id"] = user_id
            context.user_data["name"] = user['name']
            context.user_data["group"] = user['group_number']
            context.user_data["phone"] = user['phone']

            update.message.reply_text(
                f"Welcome back, {user['name']}! Here is the main menu.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Orders', 'Calendar', 'Settings', 'Log Out']],
                    one_time_keyboard=True
                )
            )
            return MAIN_MENU
        elif admin:
            context.user_data["id"] = user_id
            context.user_data["name"] = admin['name']
            context.user_data["phone"] = admin['phone']

            update.message.reply_text(
                f"Welcome back, Admin {admin['name']}! Here is the admin menu.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Orders', 'Users', 'Calendar', 'Log Out']],
                    one_time_keyboard=True
                )
            )
            return ADMIN_MAIN
        else:
            update.message.reply_text(
                "Welcome to the Vyazemsky dorm laundry bot! Please choose an option.",
                reply_markup=ReplyKeyboardMarkup([['Create Account', 'Log In']], one_time_keyboard=True)
            )
            return START
    except Exception as e:
        logger.error(f"Error in start function: {e}")
        update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END


def start_choice(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    if choice == 'Create Account':
        update.message.reply_text("What's your name?")
        return NAME
    elif choice == 'Log In':
        update.message.reply_text("Please enter your User ID:")
        return LOGIN_USER
    else:
        update.message.reply_text(
            "Please choose an option.",
            reply_markup=ReplyKeyboardMarkup([['Create Account', 'Log In']], one_time_keyboard=True)
        )
        return START


def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data["name"] = update.message.text
    update.message.reply_text("What's your User ID?")
    return USER_ID


def get_user_id(update: Update, context: CallbackContext) -> int:
    context.user_data["id"] = update.message.text
    user = db.get_user_by_id(context.user_data["id"])
    admin = db.get_admin_by_id(context.user_data["id"])

    if user or admin:
        update.message.reply_text(
            "This ID already exists. Please start again with a unique ID.",
            reply_markup=ReplyKeyboardMarkup([['Start']], one_time_keyboard=True)
        )
        return ConversationHandler.END
    else:
        update.message.reply_text("What's your group number?")
        return GROUP


def get_group(update: Update, context: CallbackContext) -> int:
    context.user_data["group"] = update.message.text
    update.message.reply_text("What's your phone number?")
    return PHONE


def get_phone(update: Update, context: CallbackContext) -> int:
    context.user_data["phone"] = update.message.text
    update.message.reply_text("Please set a password for your account:")
    return PASSWORD


def get_password(update: Update, context: CallbackContext) -> int:
    context.user_data["password"] = update.message.text

    try:
        db.add_user(
            context.user_data["name"], context.user_data["id"], context.user_data["group"],
            context.user_data["phone"], context.user_data["password"]
        )
        db.update_chat_id(context.user_data["id"], update.message.chat_id)

        logger.info(f"User {context.user_data['id']} created successfully and chat ID updated.")

        update.message.reply_text(
            "Account created successfully! Here is the main menu.",
            reply_markup=ReplyKeyboardMarkup(
                [['Orders', 'Calendar', 'Settings', 'Log Out']],
                one_time_keyboard=True
            )
        )
        return MAIN_MENU
    except ValueError as ve:
        logger.error(f"ValueError in get_password function: {ve}")
        update.message.reply_text(
            "The user ID already exists. Please start again with a unique ID.",
            reply_markup=ReplyKeyboardMarkup([['Start']], one_time_keyboard=True)
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in get_password function: {e}")
        update.message.reply_text(
            "An error occurred while creating your account. Please try again."
        )
        return ConversationHandler.END


def login(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Please enter your User ID:")
    return LOGIN_USER


def get_login_user(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    context.user_data["id"] = update.message.text
    context.user_data["chat_id"] = update.message.chat_id
    try:
        user = db.get_user_by_id(context.user_data["id"])
        admin = db.get_admin_by_id(context.user_data["id"])

        if user or admin:
            db.update_chat_id(context.user_data["id"], context.user_data["chat_id"])
            update.message.reply_text("Please enter your password:")
            return LOGIN_PASSWORD
        else:
            update.message.reply_text(
                "ID not found. Please start again or create a new account.",
                reply_markup=ReplyKeyboardMarkup([['/start']], one_time_keyboard=True)
            )
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in get_login_user function: {e}")
        update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END


def get_login_password(update: Update, context: CallbackContext) -> int:
    try:
        user = db.get_user_by_id(context.user_data["id"])
        admin = db.get_admin_by_id(context.user_data["id"])

        if user and db.verify_password(user['password'], update.message.text):
            context.user_data["name"] = user['name']
            context.user_data["group"] = user['group_number']
            context.user_data["phone"] = user['phone']
            context.user_data["chat_id"] = update.message.chat_id

            update.message.reply_text(
                "Login successful! Here is the main menu.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Orders', 'Calendar', 'Settings', 'Log Out']],
                    one_time_keyboard=True
                )
            )
            return MAIN_MENU
        elif admin and db.verify_password(admin['password'], update.message.text):
            context.user_data["name"] = admin['name']
            context.user_data["phone"] = admin['phone']
            context.user_data["chat_id"] = update.message.chat_id

            update.message.reply_text(
                "Admin login successful! Here is the admin menu.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Orders', 'Users', 'Calendar', 'Log Out']],
                    one_time_keyboard=True
                )
            )
            return ADMIN_MAIN
        else:
            update.message.reply_text(
                "Incorrect password. Please start again.",
                reply_markup=ReplyKeyboardMarkup([['Start']], one_time_keyboard=True)
            )
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in get_login_password function: {e}")
        update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END


def logout(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    update.message.reply_text(
        "You have been logged out.",
        reply_markup=ReplyKeyboardMarkup([['Create Account', 'Log In']], one_time_keyboard=True)
    )
    return START


def main_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if (menu_action := {
        'Orders': orders_menu,
        'Calendar': show_calendar,
        'Settings': settings_menu,
        'Log Out': logout
    }.get(text)):
        return menu_action(update, context)
    else:
        update.message.reply_text(
            "Main menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Calendar', 'Settings', 'Log Out']], one_time_keyboard=True)
        )
        return MAIN_MENU


def orders_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Create Order':
        show_order_dates(update, context)
        return CHOOSE_DATE
    elif text == 'Order Status':
        user_id = context.user_data["id"]
        orders = db.get_orders_by_user(user_id)
        if orders:
            status_message = "\n".join([
                f"Order ID: {order['order_id']}, Date: {order['date']}, Type: {order['type']}, "
                f"Amount: {order['amount']} Rubles, Status: {order['status']}"
                for order in orders])
            update.message.reply_text(
                f"Your orders:\n{status_message}",
                reply_markup=ReplyKeyboardMarkup([['Back to Orders'], ['Back to Main Menu']], one_time_keyboard=True)
            )
        else:
            update.message.reply_text(
                "You have no orders.",
                reply_markup=ReplyKeyboardMarkup([['Back to Orders'], ['Back to Main Menu']], one_time_keyboard=True)
            )
        return ORDER_STATUS
    elif text == 'Delete Order':
        update.message.reply_text("Please enter the order ID to delete:")
        return DELETE_ORDER
    elif text == 'Back to Main Menu':
        update.message.reply_text(
            "Main menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Calendar', 'Settings', 'Log Out']], one_time_keyboard=True)
        )
        return MAIN_MENU
    else:
        update.message.reply_text(
            "Orders menu:",
            reply_markup=ReplyKeyboardMarkup(
                [['Create Order', 'Order Status'], ['Delete Order'], ['Back to Main Menu']], one_time_keyboard=True)
        )
        return ORDERS


def order_status_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Back to Orders':
        update.message.reply_text(
            "Orders menu:",
            reply_markup=ReplyKeyboardMarkup(
                [['Create Order', 'Order Status'], ['Delete Order'], ['Back to Main Menu']], one_time_keyboard=True)
        )
        return ORDERS
    else:
        update.message.reply_text(
            "Main menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Calendar', 'Settings', 'Log Out']], one_time_keyboard=True)
        )
        return MAIN_MENU




def show_order_dates(update: Update, context: CallbackContext):
    today = datetime.today()
    dates = []
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        limit = db.get_order_limit(date_str)

        if not limit:
            db.set_order_limit(date_str, 50)
            limit = db.get_order_limit(date_str)

        limit_str = f"{limit['orders_placed']}/{limit['order_limit']} orders placed"
        dates.append([f"{date.strftime('%A')}, {date_str} - {limit_str}"])
    dates.append(['Back to Orders'])
    update.message.reply_text(
        "Choose a date for your order:",
        reply_markup=ReplyKeyboardMarkup(dates, one_time_keyboard=True)
    )


def choose_date(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Back to Orders':
        update.message.reply_text(
            "Orders menu:",
            reply_markup=ReplyKeyboardMarkup(
                [['Create Order', 'Order Status'], ['Delete Order'], ['Back to Main Menu']], one_time_keyboard=True)
        )
        return ORDERS

    try:
        selected_date = text.split(", ")[1].split(" - ")[0]
        context.user_data["date"] = selected_date

        remaining_spots = db.get_remaining_spots(selected_date)
        if remaining_spots <= 0:
            update.message.reply_text(
                f"Sorry, there are no remaining spots for {selected_date}. Please choose another date.",
                reply_markup=ReplyKeyboardMarkup([['Back to Orders']], one_time_keyboard=True)
            )
            return ORDERS

        update.message.reply_text(
            f"There are {remaining_spots} spots remaining. \nHow many orders do you want to place?",
            reply_markup=ReplyKeyboardMarkup([['Back to Orders']], one_time_keyboard=True)
        )
        return CHOOSE_COUNT
    except IndexError:
        update.message.reply_text(
            "Invalid selection. Please choose a date for your order:",
            reply_markup=ReplyKeyboardMarkup([['Back to Orders']], one_time_keyboard=True)
        )
        return CHOOSE_DATE


def choose_count(update: Update, context: CallbackContext) -> int:
    count = int(update.message.text)
    date = context.user_data["date"]
    remaining_spots = db.get_remaining_spots(date)

    if count > remaining_spots:
        update.message.reply_text(
            f"The number of orders you entered ({count}) exceeds the remaining spots ({remaining_spots}). "
            "Please enter a lower number."
        )
        return CHOOSE_COUNT

    context.user_data["count"] = count
    update.message.reply_text(
        "Choose the type of order:",
        reply_markup=ReplyKeyboardMarkup([['Clean', 'Clean + Dry', 'White Clothes']], one_time_keyboard=True)
    )
    return CHOOSE_TYPE


def choose_type(update: Update, context: CallbackContext) -> int:
    context.user_data["type"] = update.message.text
    context.user_data["total_price"] = calculate_total_price(
        context.user_data["type"], context.user_data["count"]
    )
    update.message.reply_text(
        f"Review your order:\nName: {context.user_data['name']}\nDate: {context.user_data['date']}\n"
        f"Number of orders: {context.user_data['count']}\nType: {context.user_data['type']}\n"
        f"Total Amount: {context.user_data['total_price']} Rubles\n\n"
        "Send 'Confirm' to place the order or 'Cancel' to discard.",
        reply_markup=ReplyKeyboardMarkup([['Confirm', 'Cancel'], ['Back to Orders']], one_time_keyboard=True)
    )
    return REVIEW_ORDER


def calculate_total_price(order_type, count):
    prices = {
        "Clean": 90,
        "Clean + Dry": 180,
        "White Clothes": 180
    }
    return prices.get(order_type, 0) * count


def review_order(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text.lower() == 'confirm':
        remaining_spots = db.get_remaining_spots(context.user_data["date"])
        if context.user_data["count"] > remaining_spots:
            update.message.reply_text(
                "Oops! It looks like the spots have filled up. Please try ordering on another day.",
                reply_markup=ReplyKeyboardMarkup([['Back to Orders']], one_time_keyboard=True)
            )
            return ORDERS

        try:
            amount = context.user_data["total_price"]
            order_id = db.add_order(
                context.user_data["id"], context.user_data["name"], context.user_data["date"],
                context.user_data["count"], context.user_data["type"], amount
            )

            update.message.reply_text(
                f"Order placed successfully! Your Order ID is {order_id}. Here is the main menu.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Orders', 'Calendar', 'Settings', 'Log Out']],
                    one_time_keyboard=True
                )
            )
            return MAIN_MENU
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            update.message.reply_text("An error occurred while placing your order. Please try again.")
            return ConversationHandler.END
    elif text.lower() == 'cancel':
        update.message.reply_text(
            "Order cancelled. Here is the main menu.",
            reply_markup=ReplyKeyboardMarkup(
                [['Orders', 'Calendar', 'Settings', 'Log Out']],
                one_time_keyboard=True
            )
        )
        return MAIN_MENU
    else:
        update.message.reply_text(
            f"Review your order:\nName: {context.user_data['name']}\nDate: {context.user_data['date']}\n"
            f"Number of orders: {context.user_data['count']}\nType: {context.user_data['type']}\n"
            f"Total Amount: {context.user_data['total_price']} Rubles\n\n"
            "Send 'Confirm' to place the order or 'Cancel' to discard.",
            reply_markup=ReplyKeyboardMarkup([['Confirm', 'Cancel']], one_time_keyboard=True)
        )
        return REVIEW_ORDER


def delete_order(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text.isdigit():
        order_id = text
        if db.delete_order_by_id(order_id):
            update.message.reply_text(
                f"Order with ID {order_id} has been deleted. Here is the main menu.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Orders', 'Calendar', 'Settings', 'Log Out']],
                    one_time_keyboard=True
                )
            )
        else:
            update.message.reply_text(
                f"Order with ID {order_id} could not be found or an error occurred. Please try again.",
                reply_markup=ReplyKeyboardMarkup(
                    [['Back to Orders'], ['Back to Main Menu']],
                    one_time_keyboard=True
                )
            )
        return MAIN_MENU
    else:
        update.message.reply_text(
            "Invalid Order ID. Please enter a numeric Order ID to delete:",
            reply_markup=ReplyKeyboardMarkup(
                [['Back to Orders'], ['Back to Main Menu']],
                one_time_keyboard=True
            )
        )
        return DELETE_ORDER


def settings_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Edit Account':
        update.message.reply_text(
            "Edit Account menu:",
            reply_markup=ReplyKeyboardMarkup(
                [['Change Name', 'Change Group Number', 'Change Phone Number'], ['Back to Main Menu']],
                one_time_keyboard=True
            )
        )
        return EDIT_ACCOUNT
    elif text == 'Notification':
        user = db.get_user_by_id(context.user_data["id"])
        notification_status = user.get("notification", "enabled")
        update.message.reply_text(
            f"Your current notification setting is: {notification_status}\n"
            "Would you like to enable or disable notifications?",
            reply_markup=ReplyKeyboardMarkup(
                [['Enable Notifications', 'Disable Notifications'], ['Back to Settings']],
                one_time_keyboard=True
            )
        )
        return SETTINGS_NOTIFICATION
    elif text == 'Help':
        update.message.reply_text("Help functionality not implemented yet.")
        return SETTINGS
    elif text == 'Delete Account':
        update.message.reply_text("Please enter your user ID to delete:")
        return DELETE_USER
    elif text == 'Back to Main Menu':
        update.message.reply_text(
            "Main menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Calendar', 'Settings', 'Log Out']], one_time_keyboard=True)
        )
        return MAIN_MENU
    else:
        update.message.reply_text(
            "Settings menu:",
            reply_markup=ReplyKeyboardMarkup(
                [['Edit Account', 'Notification', 'Help'], ['Delete Account'], ['Back to Main Menu']],
                one_time_keyboard=True
            )
        )
        return SETTINGS


def edit_account(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user_details = (
        f"Your account details:\nName: {context.user_data['name']}\nUser ID: {context.user_data['id']}\n"
        f"Group Number: {context.user_data['group']}\nPhone Number: {context.user_data['phone']}"
    )
    if text == 'Change Name':
        update.message.reply_text("Please enter your new name:")
        return EDIT_ACCOUNT_NAME
    elif text == 'Change Group Number':
        update.message.reply_text("Please enter your new group number:")
        return EDIT_ACCOUNT_GROUP
    elif text == 'Change Phone Number':
        update.message.reply_text("Please enter your new phone number:")
        return EDIT_ACCOUNT_PHONE
    elif text == 'Back to Main Menu':
        update.message.reply_text(
            "Main menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Calendar', 'Settings', 'Log Out']], one_time_keyboard=True)
        )
        return MAIN_MENU
    else:
        update.message.reply_text(
            user_details + "\n\nEdit Account menu:",
            reply_markup=ReplyKeyboardMarkup(
                [['Change Name', 'Change Group Number', 'Change Phone Number'], ['Back to Main Menu']],
                one_time_keyboard=True
            )
        )
        return EDIT_ACCOUNT


def update_name(update: Update, context: CallbackContext) -> int:
    new_name = update.message.text
    db.update_user(context.user_data["id"], name=new_name)
    context.user_data["name"] = new_name
    update.message.reply_text(
        "Name updated successfully. Here is the settings menu:",
        reply_markup=ReplyKeyboardMarkup(
            [['Change Name', 'Change Group Number', 'Change Phone Number'], ['Back to Main Menu']],
            one_time_keyboard=True
        )
    )
    return EDIT_ACCOUNT


def update_group_number(update: Update, context: CallbackContext) -> int:
    new_group_number = update.message.text
    db.update_user(context.user_data["id"], group_number=new_group_number)
    context.user_data["group"] = new_group_number
    update.message.reply_text(
        "Group number updated successfully. Here is the settings menu:",
        reply_markup=ReplyKeyboardMarkup(
            [['Change Name', 'Change Group Number', 'Change Phone Number'], ['Back to Main Menu']],
            one_time_keyboard=True
        )
    )
    return EDIT_ACCOUNT


def update_phone_number(update: Update, context: CallbackContext) -> int:
    new_phone_number = update.message.text
    db.update_user(context.user_data["id"], phone=new_phone_number)
    context.user_data["phone"] = new_phone_number
    update.message.reply_text(
        "Phone number updated successfully. Here is the settings menu:",
        reply_markup=ReplyKeyboardMarkup(
            [['Change Name', 'Change Group Number', 'Change Phone Number'], ['Back to Main Menu']],
            one_time_keyboard=True
        )
    )
    return EDIT_ACCOUNT


def settings_notification(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Enable Notifications':
        db.update_notification_setting(context.user_data["id"], "enabled")
        update.message.reply_text("Notifications have been enabled.")
    elif text == 'Disable Notifications':
        db.update_notification_setting(context.user_data["id"], "disabled")
        update.message.reply_text("Notifications have been disabled.")
    elif text == 'Back to Settings':
        return settings_menu(update, context)
    return SETTINGS


def send_notification(context, user, order):
    if user.get('notification', 'enabled') == 'enabled':
        chat_id = user.get('chat_id')
        if chat_id:
            try:
                message = (
                    f"Cleaning Done! You can pick up your baggage.\n"
                    f"Order ID: {order['order_id']}\nDate: {order['date']}\nType: {order['type']}\n"
                    f"Total Amount: {order['amount']} Rubles"
                )
                context.bot.send_message(
                    chat_id=chat_id, text=message,
                    reply_markup=ReplyKeyboardMarkup([['Back to Main Menu']], one_time_keyboard=True)
                )
            except Exception as e:
                logger.error(f"Error sending notification to user {user['user_id']} at chat {chat_id}: {e}")
        else:
            logger.error(f"No chat ID found for user {user['user_id']}")
    else:
        logger.info(f"Notifications are disabled for user {user['user_id']}")


def delete_user(update: Update, context: CallbackContext) -> int:
    user_id = update.message.text

    if user_id == context.user_data["id"]:
        db.delete_user_by_id(user_id)
        update.message.reply_text(
            f"Account with user ID {user_id} has been deleted.",
            reply_markup=ReplyKeyboardMarkup([['Create Account', 'Log In']], one_time_keyboard=True)
        )
        context.user_data.clear()
        return START
    else:
        update.message.reply_text(
            "Incorrect user ID. Please try again.",
            reply_markup=ReplyKeyboardMarkup([['Back to Main Menu']], one_time_keyboard=True)
        )
        return SETTINGS


def admin_main_menu(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if (menu_action := {
        'Orders': admin_orders,
        'Users': admin_users,
        'Calendar': admin_calendar,
        'Log Out': logout
    }.get(text)):
        return menu_action(update, context)
    else:
        update.message.reply_text(
            "Admin menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Users', 'Calendar', 'Log Out']], one_time_keyboard=True)
        )
        return ADMIN_MAIN


def admin_orders(update: Update, context: CallbackContext) -> int:
    show_order_dates(update, context)
    return ADMIN_DATE_ORDERS


def admin_users(update: Update, context: CallbackContext) -> int:
    user_id = update.message.text
    user = db.get_user_by_id(user_id)
    if user:
        context.user_data["id"] = user_id
        update.message.reply_text(
            f"User found: Name: {user['name']}, Group: {user['group_number']}, Phone: {user['phone']}",
            reply_markup=ReplyKeyboardMarkup(
                [['Reset Password', 'Delete User'], ['Back to Admin Main']],
                one_time_keyboard=True
            )
        )
        return ADMIN_EDIT_USER_ID
    else:
        update.message.reply_text(
            "User ID not found. Please try again.",
            reply_markup=ReplyKeyboardMarkup([['Back to Admin Main']], one_time_keyboard=True)
        )
        return ADMIN_USERS


def admin_calendar(update: Update, context: CallbackContext) -> int:
    show_calendar(update, context, admin=True)
    return ADMIN_CALENDAR


def show_calendar(update: Update, context: CallbackContext, admin=False) -> int:
    today = datetime.today()
    dates = [
        [f"{(date := today + timedelta(days=i)).strftime('%A')}, {date.strftime('%Y-%m-%d')} - "
         f"{(limit := db.get_order_limit(date.strftime('%Y-%m-%d')))['orders_placed']}/"
         f"{limit['order_limit']} orders placed"]
        for i in range(7)
    ]
    if admin:
        dates.append(['Set Limit'])
    dates.append(['Back to Main Menu'])

    update.message.reply_text(
        "Next 7 days:",
        reply_markup=ReplyKeyboardMarkup(dates, one_time_keyboard=True)
    )
    return ADMIN_CALENDAR if admin else CALENDAR


def admin_date_orders(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Back to Admin Main':
        update.message.reply_text(
            "Admin menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Users', 'Calendar', 'Log Out']], one_time_keyboard=True)
        )
        return ADMIN_MAIN

    try:
        date = text.split(", ")[1].split(" - ")[0]
    except IndexError:
        update.message.reply_text("Invalid date format. Please try again.",
                                  reply_markup=ReplyKeyboardMarkup([['Back to Admin Main']], one_time_keyboard=True))
        return ADMIN_MAIN

    orders = db.get_all_orders(date)
    orders_message = "\n".join([
        f"Order ID: {order['order_id']}, User ID: {order['user_id']}, Name: {order.get('user_name', 'N/A')}, "
        f"Type: {order['type']}, Amount: {order['amount']} Rubles, Status: {order['status']}"
        for order in orders])

    update.message.reply_text(
        f"Orders for {date}:\n{orders_message}",
        reply_markup=ReplyKeyboardMarkup([['Change Status'], ['Back to Admin Main']], one_time_keyboard=True)
    )
    return ADMIN_CHANGE_STATUS


def admin_change_status(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Back to Admin Main':
        update.message.reply_text(
            "Admin menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Users', 'Calendar', 'Log Out']], one_time_keyboard=True)
        )
        return ADMIN_MAIN

    update.message.reply_text("Please enter the order ID to update:",
                              reply_markup=ReplyKeyboardRemove())
    return ADMIN_UPDATE_ORDER_STATUS


def admin_update_order_status(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Back to Admin Main':
        update.message.reply_text(
            "Admin menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Users', 'Calendar', 'Log Out']], one_time_keyboard=True)
        )
        return ADMIN_MAIN

    order_id = text
    context.user_data['order_id'] = order_id

    order = db.get_order_by_id(order_id)
    if order:
        update.message.reply_text(
            "Please enter the new status:",
            reply_markup=ReplyKeyboardMarkup(
                [['Order under review', 'Order accepted', 'Cleaning in process', 'Cleaning Done!', 'Rejected'],
                 ['Back to Admin Main']],
                one_time_keyboard=True)
        )
        return ADMIN_CONFIRM_STATUS
    else:
        update.message.reply_text("Order ID not found. Please try again.",
                                  reply_markup=ReplyKeyboardMarkup([['Change Status'], ['Back to Admin Main']], one_time_keyboard=True))
        return ADMIN_CHANGE_STATUS


def admin_confirm_update_status(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Back to Admin Main':
        update.message.reply_text(
            "Admin menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Users', 'Calendar', 'Log Out']], one_time_keyboard=True)
        )
        return ADMIN_MAIN

    new_status = text
    order_id = context.user_data['order_id']
    try:
        db.update_order_status(
            order_id, new_status,
            notify_callback=lambda user, order: send_notification(context, user, order)
        )
        update.message.reply_text(
            f"Order ID {order_id} status updated to {new_status}.",
            reply_markup=ReplyKeyboardMarkup([['Back to Admin Main']], one_time_keyboard=True)
        )
        return ADMIN_MAIN
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        update.message.reply_text("An error occurred while updating the order status. Please try again.")
        return ADMIN_CHANGE_STATUS


def admin_edit_user(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    if text == 'Reset Password':
        update.message.reply_text("Please enter the new password:")
        return ADMIN_RESET_PASSWORD
    elif text == 'Delete User':
        db.delete_user_by_id(context.user_data["id"])
        update.message.reply_text(
            f"User with ID {context.user_data['id']} has been deleted.",
            reply_markup=ReplyKeyboardMarkup([['Back to Admin Main']], one_time_keyboard=True)
        )
        return ADMIN_MAIN
    elif text == 'Back to Admin Main':
        update.message.reply_text(
            "Admin menu:",
            reply_markup=ReplyKeyboardMarkup([['Orders', 'Users', 'Calendar', 'Log Out']], one_time_keyboard=True)
        )
        return ADMIN_MAIN
    else:
        update.message.reply_text(
            "User menu:",
            reply_markup=ReplyKeyboardMarkup([['Reset Password', 'Delete User'], ['Back to Admin Main']],
                                             one_time_keyboard=True)
        )
        return ADMIN_EDIT_USER_ID


def admin_reset_password(update: Update, context: CallbackContext) -> int:
    new_password = update.message.text
    db.change_user_password(context.user_data["id"], new_password)
    update.message.reply_text(
        "Password reset successfully.",
        reply_markup=ReplyKeyboardMarkup([['Back to Admin Main']], one_time_keyboard=True)
    )
    return ADMIN_MAIN


def admin_set_limit(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Please enter the date (YYYY-MM-DD) to set the limit:")
    return ADMIN_SET_LIMIT


def admin_confirm_set_limit(update: Update, context: CallbackContext) -> int:
    date = update.message.text
    context.user_data['date'] = date
    update.message.reply_text("Please enter the limit for this date:")
    return ADMIN_SET_LIMIT


def admin_execute_set_limit(update: Update, context: CallbackContext) -> int:
    order_limit = int(update.message.text)
    date = context.user_data['date']
    db.set_order_limit(date, order_limit)
    update.message.reply_text(
        f"Order limit for {date} set to {order_limit}.",
        reply_markup=ReplyKeyboardMarkup([['Back to Admin Main']], one_time_keyboard=True)
    )
    return ADMIN_MAIN


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Operation cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END


def main():
    updater = Updater("7457517990:AAH14m7EFdDpF0HLQGRtWQvut9sbJ4-vhPk", use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [MessageHandler(Filters.text, start_choice)],
            NAME: [MessageHandler(Filters.text, get_name)],
            USER_ID: [MessageHandler(Filters.text, get_user_id)],
            GROUP: [MessageHandler(Filters.text, get_group)],
            PHONE: [MessageHandler(Filters.text, get_phone)],
            PASSWORD: [MessageHandler(Filters.text, get_password)],
            LOGIN_USER: [MessageHandler(Filters.text, get_login_user)],
            LOGIN_PASSWORD: [MessageHandler(Filters.text, get_login_password)],
            MAIN_MENU: [MessageHandler(Filters.text, main_menu)],
            ORDERS: [MessageHandler(Filters.text, orders_menu)],
            ORDER_STATUS: [MessageHandler(Filters.text, order_status_menu)],
            CALENDAR: [MessageHandler(Filters.text, main_menu)],
            SETTINGS: [MessageHandler(Filters.text, settings_menu)],
            SETTINGS_NOTIFICATION: [MessageHandler(Filters.text, settings_notification)],
            CHOOSE_DATE: [MessageHandler(Filters.text, choose_date)],
            CHOOSE_COUNT: [MessageHandler(Filters.text, choose_count)],
            CHOOSE_TYPE: [MessageHandler(Filters.text, choose_type)],
            REVIEW_ORDER: [MessageHandler(Filters.text, review_order)],
            DELETE_ORDER: [MessageHandler(Filters.text, delete_order)],
            DELETE_USER: [MessageHandler(Filters.text, delete_user)],
            EDIT_ACCOUNT: [MessageHandler(Filters.text, edit_account)],
            EDIT_ACCOUNT_NAME: [MessageHandler(Filters.text, update_name)],
            EDIT_ACCOUNT_GROUP: [MessageHandler(Filters.text, update_group_number)],
            EDIT_ACCOUNT_PHONE: [MessageHandler(Filters.text, update_phone_number)],
            ADMIN_MAIN: [MessageHandler(Filters.text, admin_main_menu)],
            ADMIN_ORDERS: [MessageHandler(Filters.text, admin_orders)],
            ADMIN_USERS: [MessageHandler(Filters.text, admin_users)],
            ADMIN_CALENDAR: [MessageHandler(Filters.text, admin_calendar)],
            ADMIN_DATE_ORDERS: [MessageHandler(Filters.text, admin_date_orders)],
            ADMIN_CHANGE_STATUS: [MessageHandler(Filters.text, admin_change_status)],
            ADMIN_UPDATE_ORDER_STATUS: [MessageHandler(Filters.text, admin_update_order_status)],
            ADMIN_CONFIRM_STATUS: [MessageHandler(Filters.text, admin_confirm_update_status)],
            ADMIN_EDIT_USER_ID: [MessageHandler(Filters.text, admin_edit_user)],
            ADMIN_RESET_PASSWORD: [MessageHandler(Filters.text, admin_reset_password)],
            ADMIN_SET_LIMIT: [
                MessageHandler(Filters.text, admin_confirm_set_limit),
                MessageHandler(Filters.text, admin_execute_set_limit)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()








