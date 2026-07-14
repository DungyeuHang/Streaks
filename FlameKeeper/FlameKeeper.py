import customtkinter as ctk
import json
import os
import sys
from datetime import date, timedelta
import shutil

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả môi trường dev và PyInstaller """
    try:
        # PyInstaller tạo một thư mục tạm và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- Quản lý đường dẫn file ---
def get_app_data_dir():
    """Lấy đường dẫn đến thư mục dữ liệu của ứng dụng trong thư mục người dùng."""
    return os.path.join(os.path.expanduser("~"), "FlameKeeper")

def setup_user_files():
    """
    Đảm bảo các file data.json và settings.json tồn tại trong thư mục người dùng.
    Nếu không, sao chép từ file mặc định đi kèm trong gói.
    """
    app_dir = get_app_data_dir()
    os.makedirs(app_dir, exist_ok=True)

    user_data_file = os.path.join(app_dir, "data.json")
    user_settings_file = os.path.join(app_dir, "settings.json")

    if not os.path.exists(user_data_file):
        shutil.copy(resource_path("data.json"), user_data_file)
    if not os.path.exists(user_settings_file):
        shutil.copy(resource_path("settings.json"), user_settings_file)
    return user_data_file, user_settings_file
 
DATA_FILE, SETTINGS_FILE = setup_user_files()
# --- Quản lý Cài đặt ---
def load_settings():
    """Tải cài đặt giao diện từ file settings.json."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"appearance_mode": "dark", "color_theme": "blue"}

def save_settings(settings):
    """Lưu cài đặt giao diện vào file settings.json."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# --- Áp dụng cài đặt khi khởi động ---
settings = load_settings()
ctk.set_appearance_mode(settings["appearance_mode"])
ctk.set_default_color_theme(settings["color_theme"])

# =====================
# DATA
# =====================

def migrate_data_structure(data):
    """Tự động chuyển đổi cấu trúc note cũ sang cấu trúc mới."""
    migrated = False
    for streak in data.get("streaks", []):
        if "notes" in streak and streak["notes"]:
            for date_key, notes_val in streak["notes"].items():
                if isinstance(notes_val, str):
                    # Phát hiện định dạng cũ: "YYYY-MM-DD": "ghi chú"
                    # Chuyển thành: "YYYY-MM-DD": [{"text": "ghi chú", "done": True}]
                    streak["notes"][date_key] = [{"text": notes_val, "done": True}]
                    migrated = True
    return migrated

def load_data():

    if not os.path.exists(DATA_FILE):
        save_data({"streaks": []})
        return {"streaks": []}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {"streaks": []} # Trả về dữ liệu rỗng nếu file bị lỗi
    
    if migrate_data_structure(data):
        save_data(data)
        print("INFO: Cấu trúc dữ liệu cũ đã được tự động chuyển đổi.")
    return data


def save_data(data):

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

def calculate_streak(dates):

    if not dates:
        return 0

    days = sorted([date.fromisoformat(d) for d in dates], reverse=True)

    streak = 0
    today = date.today()

    # Sửa lỗi logic:
    # Bắt đầu kiểm tra từ hôm nay nếu ngày gần nhất là hôm nay,
    # hoặc từ hôm qua nếu ngày gần nhất không phải hôm nay.
    expected_day = today
    if days[0] < today:
        expected_day = today - timedelta(days=1)

    for day in days:
        if day == expected_day:
            streak += 1
            expected_day -= timedelta(days=1)
        else:
            break

    return streak

def calculate_best_streak(dates):
    if not dates:
        return 0

    # Convert to date objects and remove duplicates, then sort
    days = sorted(list(set([date.fromisoformat(d) for d in dates])))

    if not days:
        return 0

    max_streak = 0
    current_streak = 0

    if len(days) > 0:
        max_streak = 1
        current_streak = 1

    for i in range(1, len(days)):
        # Check if the current day is consecutive to the previous one
        if (days[i] - days[i-1]).days == 1:
            current_streak += 1
        # If there is a gap, reset the current streak
        elif (days[i] - days[i-1]).days > 1:
            current_streak = 1

        # Update the max streak if the current one is greater
        if current_streak > max_streak:
            max_streak = current_streak

    return max_streak

# =====================
# APP
# =====================

class FlameKeeper(ctk.CTk):

    def __init__(self):

        super().__init__()
        print("APP STARTED")
        self.title("🔥 FlameKeeper")
        self.geometry("900x650")

        # Sửa lỗi màn hình khởi động bị bé
        # Sử dụng kích thước đã định sẵn để tính toán vị trí căn giữa
        width = 900
        height = 650
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Lưu cài đặt và dữ liệu vào instance của class
        self.data = load_data()
        self.settings = settings

        # --- Khung chính chứa tiêu đề và cài đặt ---
        title_bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_bar_frame.pack(fill="x", pady=(10, 0), padx=20)
        title_bar_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            title_bar_frame,
            text="🔥 FlameKeeper",
            font=("Segoe UI", 32, "bold")
        )
        self.title_label.grid(row=0, column=0, pady=(10,0), sticky="w")

        # --- Khung Cài đặt Giao diện ---
        settings_frame = ctk.CTkFrame(title_bar_frame, fg_color="transparent")
        settings_frame.grid(row=0, column=2, sticky="e")

        self.mode_switch = ctk.CTkSwitch(
            settings_frame,
            text="Dark Mode",
            command=self._change_appearance_mode,
            font=("Segoe UI", 12)
        )
        self.mode_switch.pack(anchor="e", pady=2)
        if ctk.get_appearance_mode() == "Dark":
            self.mode_switch.select()

        theme_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["blue", "green", "dark-blue"],
            command=self._change_color_theme,
            font=("Segoe UI", 12)
        )
        theme_menu.set(self.settings["color_theme"])
        theme_menu.pack(anchor="e", pady=2)

        # --- Khung chứa các nút điều khiển chính ---
        top_button_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_button_frame.pack(pady=(0, 10))
        
        add_button = ctk.CTkButton(
            top_button_frame,
            text="+ Add Streak",
            command=self.add_streak,
            font=("Segoe UI", 16)
        )
        add_button.pack(side="left", padx=5)

        exit_button = ctk.CTkButton(
            top_button_frame,
            text="Thoát",
            command=self.confirm_exit,
            font=("Segoe UI", 16),
            fg_color="transparent",
            border_width=2
        )
        exit_button.pack(side="left", padx=5)

        self.container = ctk.CTkFrame(self)

        self.container.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=(10, 20)
        )

        # Gán phím ESC để thoát
        self.bind("<Escape>", lambda event: self.confirm_exit())

        # Lưu trữ các thẻ để cập nhật thay vì vẽ lại
        self.streak_cards = []

        self.refresh()

    def refresh(self):

        for widget in self.container.winfo_children():
            widget.destroy()

        self.streak_cards = []
        for streak in self.data["streaks"]:
            self.create_card(streak)

    def create_card(self, streak):

        card_data = {}

        card = ctk.CTkFrame(
            self.container,
            height=120,
            corner_radius=15,
            fg_color=("#ffffff", "#2b2b2b"), # Màu nền thẻ nổi bật hơn
            border_width=1
        ) 
        card.pack(fill="x", pady=10, padx=5)

        # Configure grid layout for the card
        card.grid_columnconfigure(0, weight=3)  # Name and Icon
        card.grid_columnconfigure(1, weight=3)  # Streaks
        card.grid_columnconfigure(2, weight=2)  # Buttons
        card.grid_rowconfigure(0, weight=1)

        # --- Left Part (Name & Icon) ---
        name_frame = ctk.CTkFrame(card, fg_color="transparent")
        name_frame.grid(row=0, column=0, sticky="w", padx=25)

        icon_label = ctk.CTkLabel(
            name_frame,
            text=streak.get('icon', '🔥'),
            font=("Segoe UI Emoji", 24, "bold") # Sử dụng font hỗ trợ emoji màu
        )
        icon_label.pack(side="left")

        name_label = ctk.CTkLabel(
            name_frame,
            text=f"  {streak['name']}",
            font=("Segoe UI", 24, "bold")
        )
        name_label.pack(side="left", anchor="w")

        # --- Middle Part (Streak Counts) ---
        streaks_frame = ctk.CTkFrame(card, fg_color="transparent")
        streaks_frame.grid(row=0, column=1, sticky="w", padx=10)
        streaks_frame.grid_columnconfigure(1, weight=1)

        current_streak_val = calculate_streak(streak['dates'])
        best_streak_val = calculate_best_streak(streak['dates'])

        # Current Streak
        ctk.CTkLabel(streaks_frame, text="🔥", font=("Segoe UI Emoji", 16)).grid(row=0, column=0, sticky="w")
        current_streak_label = ctk.CTkLabel(
            streaks_frame,
            text=f" Current: {current_streak_val} days",
            font=("Segoe UI", 16)
        )
        current_streak_label.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # Best Streak
        ctk.CTkLabel(streaks_frame, text="🏆", font=("Segoe UI Emoji", 16)).grid(row=1, column=0, sticky="w", pady=(5, 0))
        best_streak_label = ctk.CTkLabel(
            streaks_frame,
            text=f" Best: {best_streak_val} days",
            font=("Segoe UI", 16)
        )
        best_streak_label.grid(row=1, column=1, sticky="w", pady=(5, 0), padx=(5, 0))

        # --- Right Part (Buttons) ---
        buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
        buttons_frame.grid(row=0, column=2, sticky="e", padx=25)

        checked = date.today().isoformat() in streak["dates"]
        complete_btn = ctk.CTkButton(
            buttons_frame,
            text="DONE ✔" if checked else "TODAY",
            width=120,
            command=lambda s=streak: self.complete(s),
            state="disabled" if checked else "normal",
            fg_color="#218838" if checked else ctk.ThemeManager.theme["CTkButton"]["fg_color"], # Đồng bộ màu xanh đậm
            hover_color="#1c6e2e" if checked else ctk.ThemeManager.theme["CTkButton"]["hover_color"], # Đồng bộ màu hover
            text_color="white" if checked else ctk.ThemeManager.theme["CTkButton"]["text_color"], # Chữ màu trắng
            text_color_disabled="white", # QUAN TRỌNG: Giữ chữ màu trắng khi nút bị vô hiệu hóa
            font=("Segoe UI", 14, "bold"),
            border_width=2 if checked else 0,
            # Giữ viền trắng để nổi bật
            border_color="white" if checked else ctk.ThemeManager.theme["CTkButton"]["border_color"]
        )
        complete_btn.pack(pady=5)

        # Lưu các widget cần cập nhật
        card_data["streak_object"] = streak
        card_data["complete_button"] = complete_btn
        card_data["current_streak_label"] = current_streak_label
        card_data["best_streak_label"] = best_streak_label

        self.streak_cards.append(card_data)

        # Tối ưu hóa: Gán sự kiện click cho các thành phần không phải là button
        # Bằng cách tạo một hàm lambda để truyền streak vào handler
        handler = lambda event, s=streak: self._card_click_handler(event, s)
        
        # Danh sách các widget có thể click để mở chi tiết
        clickable_widgets = [
            card, name_frame, name_label, icon_label,
            streaks_frame, current_streak_label, best_streak_label
        ]
        for widget in clickable_widgets:
            widget.bind("<Button-1>", handler)

    def _card_click_handler(self, event, streak):
        # Bỏ qua sự kiện click nếu nó xảy ra trên một button
        if isinstance(event.widget, ctk.CTkButton):
            return
        self.show_streak_detail(streak)

    def complete(self, streak):

        today = date.today().isoformat()


        if today not in streak["dates"]:

            streak["dates"].append(today)

        save_data(self.data)

        self.update_cards_ui()

    def update_cards_ui(self):
        """Chỉ cập nhật giao diện các thẻ đã có thay vì vẽ lại toàn bộ."""
        for card in self.streak_cards:
            streak = card["streak_object"]
            checked = date.today().isoformat() in streak["dates"]

            # Cập nhật nút
            card["complete_button"].configure(
                text="DONE ✔" if checked else "TODAY",
                state="disabled" if checked else "normal",
                fg_color="#218838" if checked else ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                hover_color="#1c6e2e" if checked else ctk.ThemeManager.theme["CTkButton"]["hover_color"],
                text_color="white" if checked else ctk.ThemeManager.theme["CTkButton"]["text_color"],
                text_color_disabled="white", # QUAN TRỌNG: Giữ chữ màu trắng khi nút bị vô hiệu hóa
                border_width=2 if checked else 0,
                border_color="white" if checked else ctk.ThemeManager.theme["CTkButton"]["border_color"]
            )
            # Cập nhật số ngày
            card["current_streak_label"].configure(text=f" Current: {calculate_streak(streak['dates'])} days")


    def add_streak(self):

        self.withdraw()
        dialog = AddStreakDialog(self)
        new_streak_data = dialog.get_input()
        self.deiconify()

        if not new_streak_data:
            return


        new_streak = {
            "name": new_streak_data["name"],
            "icon": new_streak_data["icon"],
            "dates": [],
            "notes": {}
        }


        self.data["streaks"].append(new_streak)
        save_data(self.data)
        self.refresh()


    def show_streak_detail(self, streak):
        if "notes" not in streak or not isinstance(streak.get("notes"), dict):
            streak["notes"] = {}
        self.withdraw()
        dialog = StreakDetailDialog(self, streak, self)
        dialog.wait_window()
        self.deiconify()
        self.refresh() # Vẽ lại toàn bộ để cập nhật các thay đổi (sửa, xóa)

    def confirm_exit(self):
        dialog = ConfirmationDialog(self, "Xác nhận Thoát", "Bạn có chắc muốn thoát FlameKeeper không?")
        if dialog.get_result():
            self.destroy()

    def _change_appearance_mode(self):
        new_mode = "Dark" if self.mode_switch.get() == 1 else "Light"
        ctk.set_appearance_mode(new_mode)
        self.settings["appearance_mode"] = new_mode
        save_settings(self.settings)

    def _change_color_theme(self, new_theme: str):
        # Lưu ý: Thay đổi theme trong CustomTkinter yêu cầu khởi động lại ứng dụng
        # để áp dụng hoàn toàn cho tất cả các widget.
        self.settings["color_theme"] = new_theme
        save_settings(self.settings)

        dialog = ConfirmationDialog(
            self,
            "Yêu cầu khởi động lại",
            "Chủ đề đã được thay đổi.\nBạn có muốn khởi động lại ứng dụng ngay bây giờ không?",
            confirm_text="Khởi động lại",
            confirm_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
            hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"]
        )
        if dialog.get_result():
            self.restart_app()

    def restart_app(self):
        """Khởi động lại ứng dụng hiện tại."""
        for window in self.winfo_children():
            if isinstance(window, ctk.CTkToplevel):
                window.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)
        
class BaseDialog(ctk.CTkToplevel):
    """Một lớp dialog cơ sở có khả năng tự động căn giữa màn hình."""
    def __init__(self, master, title, width, height):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")

        # Tự động căn giữa màn hình
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.transient(master)
        self.grab_set()
        self.result = None

class AddStreakDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Add New Streak")
        self.geometry("350x230")
        self.transient(master)
        self.grab_set()

        # Căn giữa màn hình
        width = 350
        height = 230
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.result = None

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.name_label = ctk.CTkLabel(self.main_frame, text="Streak Name:", font=("Segoe UI", 14))
        self.name_label.pack(anchor="w")
        self.name_entry = ctk.CTkEntry(self.main_frame, width=250, font=("Segoe UI", 14))
        self.name_entry.pack(fill="x", pady=(0, 15))

        self.icon_label = ctk.CTkLabel(self.main_frame, text="Icon (emoji):", font=("Segoe UI", 14))
        self.icon_label.pack(anchor="w")
        self.icon_entry = ctk.CTkEntry(self.main_frame, width=50, font=("Segoe UI", 14))
        self.icon_entry.pack(anchor="w")
        self.icon_entry.insert(0, "🔥")

        self.add_button = ctk.CTkButton(self, text="Add", command=self.on_add, font=("Segoe UI", 14))
        self.add_button.pack(pady=(0, 20))

        self.name_entry.focus()
        self.bind("<Return>", lambda event: self.on_add())

    def on_add(self):
        name = self.name_entry.get()
        icon = self.icon_entry.get()
        if name and icon:
            self.result = {"name": name, "icon": icon}
            self.destroy()

    def get_input(self):
        self.wait_window()
        return self.result

class EditStreakDialog(ctk.CTkToplevel):
    def __init__(self, master, current_name, current_icon):
        super().__init__(master)
        self.title("Chỉnh sửa Streak")
        self.geometry("350x230")

        # Căn giữa màn hình
        width = 350
        height = 230
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.transient(master)
        self.grab_set()
        self.result = None

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(self.main_frame, text="Tên Streak:", font=("Segoe UI", 14)).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(self.main_frame, width=250, font=("Segoe UI", 14))
        self.name_entry.pack(fill="x", pady=(0, 15))
        self.name_entry.insert(0, current_name)

        ctk.CTkLabel(self.main_frame, text="Icon (emoji):", font=("Segoe UI", 14)).pack(anchor="w")
        self.icon_entry = ctk.CTkEntry(self.main_frame, width=50, font=("Segoe UI", 14))
        self.icon_entry.pack(anchor="w")
        self.icon_entry.insert(0, current_icon)

        ctk.CTkButton(self, text="Lưu thay đổi", command=self.on_save).pack(pady=(0, 20))
        self.name_entry.focus()
        self.bind("<Return>", lambda event: self.on_save())

    def on_save(self):
        self.result = {"name": self.name_entry.get(), "icon": self.icon_entry.get()}
        self.destroy()

class ConfirmationDialog(ctk.CTkToplevel):
    def __init__(self, master, title, text, confirm_text="Xác nhận", confirm_color="#c95151", hover_color="#a13f3f"):
        super().__init__(master)
        self.title(title)
        self.geometry("350x150")
        self.transient(master)
        self.grab_set()

        # Căn giữa màn hình
        width = 350
        height = 150
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.result = False

        label = ctk.CTkLabel(self, text=text, font=("Segoe UI", 14), wraplength=300, justify="center")
        label.pack(pady=20, padx=20, expand=True, fill="both")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        cancel_button = ctk.CTkButton(button_frame, text="Hủy", command=self.on_cancel)
        cancel_button.pack(side="left", padx=10)

        confirm_button = ctk.CTkButton(button_frame, text=confirm_text, command=self.on_confirm, fg_color=confirm_color, hover_color=hover_color)
        confirm_button.pack(side="right", padx=10)

    def on_confirm(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result

class MessageBox(ctk.CTkToplevel):
    def __init__(self, master, title, text):
        super().__init__(master)
        self.title(title)
        width, height = 300, 150
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text=text, wraplength=280, justify="center").pack(pady=20, expand=True)
        ctk.CTkButton(self, text="OK", command=self.destroy, width=80).pack(pady=(0, 15))
        self.wait_window()

class TimerDialog(ctk.CTkToplevel):
    def __init__(self, master, note, on_finish_callback):
        super().__init__(master)
        self.note = note
        self.on_finish_callback = on_finish_callback
        self.is_running = False
        self.app_data = master.app.data # Lấy tham chiếu đến dữ liệu chính

        self.title("Bộ đếm thời gian")
        width, height = 350, 220
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._finish) # Xử lý khi nhấn nút 'X'

        ctk.CTkLabel(self, text=self.note['text'], font=("Segoe UI", 16, "bold"), wraplength=300).pack(pady=(20, 5))
        
        self.time_label = ctk.CTkLabel(self, text=self._format_time(self.note.get("duration_seconds", 0)), font=("Courier", 48, "bold"))
        self.time_label.pack(pady=10, expand=True)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(10, 20))

        self.pause_button = ctk.CTkButton(button_frame, text="❚❚ Tạm dừng", command=self._toggle_pause)
        self.pause_button.pack(side="left", padx=10)

        finish_button = ctk.CTkButton(button_frame, text="Hoàn thành", command=self._finish, fg_color="#28a745", hover_color="#218838")
        finish_button.pack(side="left", padx=10)

        self.after_id = None
        self._start_timer()

    def _format_time(self, total_seconds):
        return f"{(total_seconds // 3600):02}:{(total_seconds % 3600 // 60):02}:{(total_seconds % 60):02}"

    def _start_timer(self):
        self.is_running = True; self.pause_button.configure(text="❚❚ Tạm dừng"); self._update_display()

    def _toggle_pause(self):
        self.is_running = not self.is_running
        if self.is_running: self._start_timer()
        else: self.after_cancel(self.after_id); self.pause_button.configure(text="▶ Tiếp tục"); save_data(self.app_data)

    def _update_display(self):
        if not self.is_running or not self.winfo_exists(): return
        self.note['duration_seconds'] = self.note.get('duration_seconds', 0) + 1
        self.time_label.configure(text=self._format_time(self.note['duration_seconds']))
        self.after_id = self.after(1000, self._update_display)

    def _finish(self):
        if self.is_running and self.after_id: self.after_cancel(self.after_id)
        save_data(self.app_data); self.on_finish_callback(); self.destroy()

class Tooltip:
    """Lớp tạo tooltip đơn giản khi di chuột qua một widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 20
        y = y + self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True) # Xóa viền và thanh tiêu đề
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, justify='left', corner_radius=6, padx=8, pady=5)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class StreakDetailDialog(ctk.CTkToplevel):
    def __init__(self, master, streak, app_instance):
        super().__init__(master)
        self.streak = streak
        self.app = app_instance
        self.today_str = date.today().isoformat()

        # --- State Management ---
        # Tham chiếu đến cửa sổ đếm giờ đang hoạt động để đảm bảo chỉ có một timer chạy
        self.active_timer_dialog = None
        # Set để theo dõi các tab đã được tải, giúp tăng tốc độ mở cửa sổ
        self.loaded_tabs = set()

        self.title(f"{self.streak.get('icon', '🔥')} {self.streak['name']}")
        self.geometry("550x700")

        # Căn giữa cửa sổ chi tiết khi mở ra
        width = 550
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.transient(master)
        self.grab_set()
        
        # Gán phím ESC để đóng cửa sổ
        self.bind("<Escape>", lambda event: self.close_dialog())

        # --- Layout chính ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Cho phép TabView mở rộng

        # --- 1. Khung Header (thống kê) ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        header_frame.grid_columnconfigure(2, weight=10) # Cột rỗng để đẩy label sang trái

        current_streak_val = calculate_streak(streak['dates'])
        best_streak_val = calculate_best_streak(streak['dates'])

        # Current Streak
        ctk.CTkLabel(header_frame, text="🔥", font=("Segoe UI Emoji", 16)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header_frame, text=f" Current: {current_streak_val} days", font=("Segoe UI", 16)).grid(row=0, column=1, sticky="w")

        # Best Streak
        ctk.CTkLabel(header_frame, text="🏆", font=("Segoe UI Emoji", 16)).grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(header_frame, text=f" Best: {best_streak_val} days", font=("Segoe UI", 16)).grid(row=1, column=1, sticky="w")

        edit_button = ctk.CTkButton(
            header_frame,
            text="Chỉnh sửa",
            command=self._edit_streak,
            width=90,
            font=("Segoe UI", 12)
        )
        edit_button.grid(row=0, column=3, rowspan=2, sticky="e", padx=10)

        # --- 2. TabView cho "Hôm nay" và "Lịch sử" ---
        self.tab_view = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tab_view.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.tab_view.add("Hôm nay")
        self.tab_view.add("Lịch sử")
        self.tab_view.add("Biểu đồ")

        # --- Cấu hình Tab "Hôm nay" ---
        today_tab = self.tab_view.tab("Hôm nay")
        today_tab.grid_columnconfigure(0, weight=1)

        today_input_frame = ctk.CTkFrame(today_tab, fg_color="transparent")
        today_input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        today_input_frame.grid_columnconfigure(0, weight=1)

        self.note_entry = ctk.CTkEntry(today_input_frame, placeholder_text="Thêm công việc mới...")
        self.note_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.note_entry.bind("<Return>", lambda event: self._add_new_note())

        ctk.CTkButton(today_input_frame, text="+ Thêm", width=70, command=self._add_new_note).grid(row=0, column=1, sticky="e")

        self.today_notes_container = ctk.CTkScrollableFrame(today_tab, fg_color="transparent")
        self.today_notes_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        today_tab.grid_rowconfigure(1, weight=1)

        # --- Cấu hình Tab "Lịch sử" ---
        history_tab = self.tab_view.tab("Lịch sử")
        history_tab.grid_rowconfigure(0, weight=1)
        history_tab.grid_columnconfigure(0, weight=1)

        self.history_frame = ctk.CTkScrollableFrame(history_tab)
        self.history_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # --- Cấu hình Tab "Biểu đồ" ---
        heatmap_tab = self.tab_view.tab("Biểu đồ")
        heatmap_tab.grid_rowconfigure(0, weight=1)
        heatmap_tab.grid_columnconfigure(0, weight=1)
        self.heatmap_frame = ctk.CTkFrame(heatmap_tab, fg_color="transparent")
        self.heatmap_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # --- 3. Khung dưới cùng (nút xóa) ---
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")

        close_button = ctk.CTkButton(
            bottom_frame,
            text="Đóng",
            command=self.close_dialog,
            width=120
        )
        close_button.pack(side="left")

        delete_button = ctk.CTkButton(
            bottom_frame,
            text="Xóa Streak",
            command=self._delete_streak,
            fg_color="#c95151",
            hover_color="#a13f3f",
            width=120)
        delete_button.pack(side="right")

        # Tải ngay tab đầu tiên. Các tab khác sẽ được tải khi người dùng nhấp vào.
        self._refresh_today_notes()
        self.loaded_tabs.add("Hôm nay")

    def close_dialog(self):
        """Đóng cửa sổ timer đang chạy (nếu có) trước khi đóng cửa sổ chi tiết."""
        if self.active_timer_dialog and self.active_timer_dialog.winfo_exists():
            # Việc hủy cửa sổ timer sẽ tự động kích hoạt lưu dữ liệu
            self.active_timer_dialog.destroy()
        
        self.destroy()

    def _delete_streak(self):
        dialog = ConfirmationDialog(self, "Xác nhận Xóa", f"Bạn có chắc muốn xóa streak '{self.streak['name']}' không?\nHành động này không thể hoàn tác.")
        if dialog.get_result():
            # User confirmed
            self.app.data["streaks"].remove(self.streak)
            save_data(self.app.data)
            self.close_dialog() # Close the detail dialog
 
    def _edit_streak(self):
        """Mở dialog để chỉnh sửa tên và icon của streak."""
        self.withdraw()
        dialog = EditStreakDialog(self, self.streak['name'], self.streak.get('icon', '🔥'))
        dialog.wait_window()
        self.deiconify()
        new_data = dialog.result

        if new_data and (new_data['name'] != self.streak['name'] or new_data['icon'] != self.streak.get('icon')):
            self.streak['name'] = new_data['name']
            self.streak['icon'] = new_data['icon']
            save_data(self.app.data)
            self.title(f"{self.streak.get('icon', '🔥')} {self.streak['name']}") # Cập nhật tiêu đề cửa sổ
            # Không cần refresh toàn bộ, việc update_cards_ui() khi đóng dialog là đủ

    def _add_new_note(self):
        note_text = self.note_entry.get()
        if not note_text:
            return

        new_note = {"text": note_text, "done": False, "duration_seconds": 0}
        if self.today_str not in self.streak["notes"]:
            self.streak["notes"][self.today_str] = []

        self.streak["notes"][self.today_str].append(new_note)
        save_data(self.app.data)

        self.note_entry.delete(0, "end")
        self._refresh_today_notes()

    def _toggle_note_status(self, note_object, checkbox_var):
        # Sửa lỗi khi đóng cửa sổ note
        # Thêm kiểm tra winfo_exists() ở đầu hàm để thoát ngay lập tức
        # nếu cửa sổ đang trong quá trình bị hủy.
        if not self.winfo_exists():
            return
        note_object["done"] = checkbox_var.get()
        save_data(self.app.data)

    def _delete_note(self, note_to_delete):
        """Xóa một ghi chú cụ thể khỏi danh sách của ngày hôm nay."""
        # Nếu công việc đang bị xóa có bộ đếm thời gian đang chạy, hãy đóng nó.
        if self.active_timer_dialog and self.active_timer_dialog.winfo_exists() and self.active_timer_dialog.note == note_to_delete:
            self.active_timer_dialog.destroy()
            self.active_timer_dialog = None # Xóa tham chiếu

        today_notes = self.streak["notes"].get(self.today_str, [])
        
        # Tìm và xóa ghi chú
        if note_to_delete in today_notes:
            today_notes.remove(note_to_delete)
            
            # Nếu không còn ghi chú nào trong ngày, xóa luôn key của ngày đó
            if not today_notes and self.today_str in self.streak["notes"]:
                del self.streak["notes"][self.today_str]

            save_data(self.app.data)
            self._refresh_today_notes()

    def _refresh_today_notes(self):
        for widget in self.today_notes_container.winfo_children():
            widget.destroy()

        today_notes = self.streak["notes"].get(self.today_str, [])
        for note in today_notes:
            note_frame = ctk.CTkFrame(self.today_notes_container, fg_color="transparent")
            note_frame.pack(anchor="w", pady=2, fill="x")

            # --- Cấu hình layout dạng bảng (grid) cho mỗi dòng note ---
            note_frame.grid_columnconfigure(1, weight=1) # Cho phép cột text co giãn

            # --- Checkbox (Cột 0) ---
            checkbox_var = ctk.BooleanVar(value=note["done"])
            checkbox_var.trace_add("write", lambda name, index, mode, n=note, v=checkbox_var: self._toggle_note_status(n, v))
            cb = ctk.CTkCheckBox(
                note_frame,
                text="",
                variable=checkbox_var,
            )
            cb.grid(row=0, column=0, sticky="w", padx=(0, 5))

            # --- Label (Cột 1, co giãn) ---
            label = ctk.CTkLabel(
                note_frame,
                text=note["text"],
                wraplength=300, # Điều chỉnh lại một chút
                justify="left"
            )
            label.grid(row=0, column=1, sticky="ew", padx=5)
            label.bind("<Button-1>", lambda e, v=checkbox_var: v.set(not v.get()))

            # --- Nhãn hiển thị thời gian (Cột 2) ---
            duration = note.get("duration_seconds", 0)
            time_label = ctk.CTkLabel(note_frame, text=self._format_time(duration), font=("Segoe UI", 12), width=70) # Thêm width cố định
            time_label.grid(row=0, column=2, sticky="e", padx=(5, 5))

            # --- Nút timer (Cột 3) ---
            timer_button = ctk.CTkButton(
                note_frame, text="▶", width=28, height=28
            )
            timer_button.grid(row=0, column=3, sticky="e", padx=(0, 5))

            # --- Nút xóa (Cột 4) ---
            delete_button = ctk.CTkButton(
                note_frame, text="🗑️", command=lambda n=note: self._delete_note(n),
                width=28, height=28, fg_color="transparent", hover_color="#c95151"
            )
            delete_button.grid(row=0, column=4, sticky="e", padx=(0, 5))
            
            # Gán lệnh cho nút timer
            timer_button.configure(command=lambda n=note: self._start_timer_dialog(n))

    def _format_time(self, total_seconds): return f"{(total_seconds // 3600):02}:{(total_seconds % 3600 // 60):02}:{(total_seconds % 60):02}"

    def _start_timer_dialog(self, note):
        """Mở một cửa sổ đếm giờ riêng biệt cho một công việc."""
        if self.active_timer_dialog and self.active_timer_dialog.winfo_exists():
            MessageBox(self, "Thông báo", "Một bộ đếm thời gian khác đang chạy.\nVui lòng hoàn thành nó trước khi bắt đầu một bộ đếm mới.")
            self.active_timer_dialog.lift(); self.active_timer_dialog.focus()
            return
        
        self.withdraw() # Ẩn cửa sổ chi tiết
        self.active_timer_dialog = TimerDialog(self, note, on_finish_callback=self._on_timer_finished)

    def _on_timer_finished(self):
        """Callback được gọi khi cửa sổ timer đóng lại."""
        self.active_timer_dialog = None
        self._refresh_today_notes() # Cập nhật lại nhãn thời gian trong danh sách
        self.deiconify() # Hiện lại cửa sổ chi tiết

    def _on_tab_change(self):
        """Tải nội dung của tab khi nó được chọn lần đầu tiên (lazy loading)."""
        selected_tab = self.tab_view.get()
        if selected_tab not in self.loaded_tabs:
            if selected_tab == "Lịch sử":
                self._refresh_history()
            elif selected_tab == "Biểu đồ":
                self._create_heatmap()
            self.loaded_tabs.add(selected_tab)

    def _refresh_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        # --- Hiển thị lịch sử các ngày đã hoàn thành ---

        # --- Hiển thị lịch sử các ghi chú cũ ---
        past_notes_frame = ctk.CTkFrame(self.history_frame, border_width=1)
        past_notes_frame.pack(fill="x", pady=(5, 15))
        ctk.CTkLabel(past_notes_frame, text="Ghi chú đã qua", font=("Segoe UI", 16, "bold")).pack(pady=(5, 10), padx=10, anchor="w")
        
        sorted_notes = sorted(self.streak["notes"].items(), key=lambda item: item[0], reverse=True)

        found_any = False
        for day, notes_list in sorted_notes:
            if day == self.today_str:
                continue
            
            found_any = True
            # Tạo một khung riêng cho mỗi ngày trong lịch sử
            day_frame = ctk.CTkFrame(past_notes_frame, fg_color=("#e3e3e3", "#2b2b2b"))
            day_frame.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(day_frame, text=day, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(5,0))

            # Khung chứa các ghi chú của ngày đó
            notes_container_in_day = ctk.CTkFrame(day_frame, fg_color="transparent")
            notes_container_in_day.pack(fill="x", padx=10, pady=(5,10))

            for note in notes_list:
                icon = "☑" if note.get("done", False) else "☐"
                duration = note.get("duration_seconds", 0)
                duration_str = ""
                if duration > 0:
                    duration_str = f" ({self._format_time(duration)})"
                
                ctk.CTkLabel(notes_container_in_day, text=f"{icon} {note['text']}{duration_str}", wraplength=450, justify="left").pack(anchor="w", padx=(10, 0))

        if not found_any:
            ctk.CTkLabel(past_notes_frame, text="Không có ghi chú nào trong quá khứ.").pack(pady=20)

        # --- Hiển thị lịch sử các ngày đã hoàn thành (chuyển xuống dưới) ---
        completed_dates_frame = ctk.CTkFrame(self.history_frame, border_width=1)
        completed_dates_frame.pack(fill="x", pady=(5, 15))
        ctk.CTkLabel(completed_dates_frame, text="Ngày hoàn thành Streak", font=("Segoe UI", 16, "bold")).pack(pady=(5, 10), padx=10, anchor="w")
        
        if not self.streak['dates']:
            ctk.CTkLabel(completed_dates_frame, text="Chưa có ngày nào được hoàn thành.").pack(pady=5, padx=10)
        else:
            sorted_dates = sorted(self.streak['dates'], reverse=True)
            ctk.CTkLabel(completed_dates_frame, text="\n".join(sorted_dates), justify="left").pack(pady=(0, 10), padx=10, anchor="w")

    def _create_heatmap(self):
        """Tạo và vẽ biểu đồ lịch (calendar heatmap) cho 365 ngày gần nhất."""
        for widget in self.heatmap_frame.winfo_children():
            widget.destroy()
        
        # LƯU Ý: Biểu đồ này chỉ hiển thị dữ liệu trong 365 ngày gần nhất.

        completed_dates = set(self.streak['dates'])
        today = date.today()
        # Bắt đầu từ Chủ Nhật của tuần chứa ngày đầu tiên trong khoảng 365 ngày
        start_date_365 = today - timedelta(days=364)
        # Sửa lỗi tính toán: căn chỉnh ngày bắt đầu về thứ Hai của tuần đó
        start_date = start_date_365 - timedelta(days=start_date_365.weekday())

        # Màu sắc
        empty_color = ("#e0e0e0", "#333333")
        completed_color = "#28a745"
        cell_size = 15
        cell_padding = 2

        # --- Khung chính của biểu đồ ---
        main_heatmap_frame = ctk.CTkFrame(self.heatmap_frame)
        main_heatmap_frame.pack(pady=20, padx=10, anchor="center")

        # --- Nhãn các ngày trong tuần (T2, T4, T6) ---
        days_of_week = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        for i, day_name in enumerate(days_of_week):
            if i % 2 == 0: # Chỉ hiển thị T2, T4, T6, CN cho gọn
                label = ctk.CTkLabel(main_heatmap_frame, text=day_name, font=("Segoe UI", 10))
                label.grid(row=i + 1, column=0, padx=(0, 5), sticky="w")

        # --- Vẽ các ô ngày và nhãn tháng ---
        last_month = -1
        for day_offset in range((today - start_date).days + 1):
            current_day = start_date + timedelta(days=day_offset)
            week_num = day_offset // 7
            day_of_week = current_day.weekday() # Monday is 0 and Sunday is 6

            # Thêm nhãn tháng khi tháng thay đổi
            if current_day.month != last_month:
                month_label = ctk.CTkLabel(main_heatmap_frame, text=current_day.strftime("%b"), font=("Segoe UI", 10))
                month_label.grid(row=0, column=week_num + 1, columnspan=4, sticky="w")
                last_month = current_day.month

            # Chỉ vẽ các ô trong khoảng 365 ngày
            if current_day > today:
                continue

            # Xác định màu sắc của ô
            is_completed = current_day.isoformat() in completed_dates
            color = completed_color if is_completed else empty_color

            # Tạo ô
            day_cell = ctk.CTkFrame(main_heatmap_frame, width=cell_size, height=cell_size, fg_color=color, corner_radius=3)
            day_cell.grid(row=day_of_week + 1, column=week_num + 1, padx=cell_padding, pady=cell_padding)

            # Thêm tooltip cho mỗi ô
            tooltip_text = f"{current_day.strftime('%d-%m-%Y')}\nHoàn thành" if is_completed else current_day.strftime('%d-%m-%Y')
            Tooltip(day_cell, tooltip_text)

        # Thêm chú thích
        legend_frame = ctk.CTkFrame(self.heatmap_frame, fg_color="transparent")
        legend_frame.pack(pady=(10, 0), anchor="e", padx=20)
        ctk.CTkLabel(legend_frame, text="Hoàn thành ").pack(side="left")
        ctk.CTkFrame(legend_frame, width=15, height=15, fg_color=completed_color, corner_radius=3).pack(side="left")

if __name__ == "__main__":
    # Biến 'settings' đã được định nghĩa ở phạm vi toàn cục ở trên
    # và được sử dụng bên trong __init__ của FlameKeeper.
    app = FlameKeeper()
    app.mainloop()