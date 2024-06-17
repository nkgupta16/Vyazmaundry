import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt
import random

creds_file = "laundry-bot-426406-79fb2a9e73ae.json"


class Database:
    def __init__(self, spreadsheet_name='laundry_bot'):
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open(spreadsheet_name)
        self.users_sheet = self.sheet.worksheet("users")
        self.admins_sheet = self.sheet.worksheet("admins")
        self.orders_sheet = self.sheet.worksheet("orders")
        self.orders_limit_sheet = self.sheet.worksheet("orders_limit")

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode(), stored_password.encode())

    def add_user(self, name, user_id, group_number, phone, password):
        hashed_password = self.hash_password(password)
        try:
            self.users_sheet.append_row([name, user_id, group_number, phone, hashed_password, '', 'enabled'])
        except gspread.exceptions.APIError as e:
            print(f"APIError in add_user: {e}")
            raise ValueError("User ID already exists")
        except Exception as e:
            print(f"Error in add_user: {e}")
            raise e

    def update_chat_id(self, user_id, chat_id):
        try:
            cell = self.users_sheet.find(user_id)
            if cell:
                self.users_sheet.update_cell(cell.row, 6, chat_id)
            else:
                print(f"User ID {user_id} not found. Cannot update chat ID.")
        except Exception as e:
            print(f"Error updating chat ID: {e}")

    def add_admin(self, name, admin_id, phone, password):
        hashed_password = self.hash_password(password)
        try:
            self.admins_sheet.append_row([name, admin_id, phone, hashed_password])
        except gspread.exceptions.APIError:
            raise ValueError("Admin ID already exists")

    def get_user_by_id(self, user_id):
        try:
            users = self.get_all_users()
            for user in users:
                if str(user['user_id']) == str(user_id):
                    return user
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    def get_admin_by_id(self, admin_id):
        try:
            admins = self.get_all_admins()
            for admin in admins:
                if str(admin['admin_id']) == str(admin_id):
                    return admin
            return None
        except Exception as e:
            print(f"Error getting admin by ID: {e}")
            return None

    def get_all_users(self):
        try:
            expected_headers = ['name', 'user_id', 'group_number', 'phone', 'password', 'chat_id', 'notification']
            return self.users_sheet.get_all_records(expected_headers=expected_headers)
        except Exception as e:
            print(f"Error getting users: {e}")
            return []

    def get_all_admins(self):
        try:
            return self.admins_sheet.get_all_records()
        except Exception as e:
            print(f"Error getting admins: {e}")
            return []

    def add_order(self, user_id, user_name, date, count, order_type, amount, status='Order under review'):
        order_id = str(random.randint(1000, 9999))
        try:
            self.orders_sheet.append_row([order_id, user_id, user_name, date, count, order_type, amount, status])
        except Exception as e:
            print(f"Error adding order: {e}")
        return order_id

    def get_orders_by_user(self, user_id):
        try:
            orders = self.orders_sheet.get_all_records()
            user_orders = [order for order in orders if str(order['user_id']) == str(user_id)]
            return user_orders
        except Exception as e:
            print(f"Error accessing orders: {e}")
            return []

    def delete_user_by_id(self, user_id):
        try:
            cell = self.users_sheet.find(user_id)
            self.users_sheet.delete_rows(cell.row)
            print(f"User with ID {user_id} has been deleted.")
        except Exception as e:
            print(f"Error deleting user: {e}")

    def delete_order_by_id(self, order_id):
        try:
            cell = self.orders_sheet.find(order_id)
            if cell:
                self.orders_sheet.delete_rows(cell.row)
                print(f"Order with ID {order_id} has been deleted.")
                return True
            else:
                print(f"Order with ID {order_id} not found.")
                return False
        except Exception as e:
            print(f"Error deleting order: {e}")
            return False

    def set_order_limit(self, date, order_limit=50):
        try:
            limits = self.orders_limit_sheet.get_all_records()
            for limit in limits:
                if limit['date'] == date:
                    cell = self.orders_limit_sheet.find(date)
                    self.orders_limit_sheet.update_cell(cell.row, 2, order_limit)
                    return
            self.orders_limit_sheet.append_row([date, order_limit, 0])
        except Exception as e:
            print(f"Error setting order limit: {e}")

    def get_order_limit(self, date):
        try:
            limits = self.orders_limit_sheet.get_all_records()
            for limit in limits:
                if limit['date'] == date:
                    return limit
            return None
        except Exception as e:
            print(f"Error getting order limit: {e}")
            return None

    def get_remaining_spots(self, date):
        try:
            limit_info = self.get_order_limit(date)
            if limit_info:
                order_limit = int(limit_info['order_limit'])
                orders_placed = int(limit_info['orders_placed'])
                remaining_spots = order_limit - orders_placed
                return remaining_spots
            else:
                return 50  # Default remaining spots
        except Exception as e:
            print(f"Error getting remaining spots: {e}")
            return 0

    def update_user(self, user_id, name=None, group_number=None, phone=None):
        try:
            cell = self.users_sheet.find(user_id)
            if cell:
                row = cell.row
                if name:
                    self.users_sheet.update_cell(row, 1, name)
                if group_number:
                    self.users_sheet.update_cell(row, 3, group_number)
                if phone:
                    self.users_sheet.update_cell(row, 4, phone)
            else:
                print(f"User ID {user_id} not found.")
        except Exception as e:
            print(f"Error updating user: {e}")

    def update_notification_setting(self, user_id, setting):
        try:
            cell = self.users_sheet.find(user_id)
            self.users_sheet.update_cell(cell.row, 7, setting)
        except Exception as e:
            print(f"Error updating notification setting: {e}")

    def change_user_password(self, user_id, new_password):
        try:
            hashed_password = self.hash_password(new_password)
            users = self.users_sheet.get_all_records()
            for i, user in enumerate(users):
                if user['user_id'] == user_id:
                    self.users_sheet.update_cell(i + 2, 5, hashed_password)
                    return
        except Exception as e:
            print(f"Error changing user password: {e}")

    def get_all_orders(self, date):
        try:
            orders = self.orders_sheet.get_all_records()
            return [order for order in orders if order['date'] == date]
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

    def get_order_by_id(self, order_id):
        try:
            orders = self.orders_sheet.get_all_records()
            for order in orders:
                if str(order['order_id']) == str(order_id):
                    return order
            return None
        except Exception as e:
            print(f"Error getting order by Order ID: {e}")
            return None

    def update_order_status(self, order_id, new_status, notify_callback=None):
        try:
            orders = self.orders_sheet.get_all_records()
            for i, order in enumerate(orders):
                if str(order['order_id']) == str(order_id):
                    self.orders_sheet.update_cell(i + 2, 8, new_status)
                    if new_status == "Cleaning Done!" and notify_callback:
                        user_id = order['user_id']
                        user = self.get_user_by_id(user_id)
                        if user:
                            notify_callback(user, order)
                        else:
                            print(f"User with ID {user_id} not found.")
                    return
        except Exception as e:
            print(f"Error updating order status: {e}")

    def clear_database(self):
        try:
            self.users_sheet.clear()
            self.admins_sheet.clear()
            self.orders_sheet.clear()
            self.orders_limit_sheet.clear()
            self.users_sheet.append_row(
                ['name', 'user_id', 'group_number', 'phone', 'password', 'chat_id', 'notification']
            )
            self.admins_sheet.append_row(['name', 'admin_id', 'phone', 'password'])
            self.orders_sheet.append_row(
                ['order_id', 'user_id', 'user_name', 'date', 'count', 'type', 'amount', 'status']
            )
            self.orders_limit_sheet.append_row(['date', 'order_limit', 'orders_placed'])
            print("Database cleared and tables recreated.")
        except Exception as e:
            print(f"Error clearing database: {e}")
