import customtkinter as ctk
from ui.streak_card import StreakCard
# ----------------------------
# Theme
# ----------------------------
ctk.set_appearance_mode("Dark")      # Dark / Light / System
ctk.set_default_color_theme("blue")  # blue, green, dark-blue


class FlameKeeper(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("🔥 FlameKeeper")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # ==========================
        # Layout
        # ==========================

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Main
        self.main = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main.grid(row=0, column=1, sticky="nsew")

        self.main.grid_columnconfigure(0, weight=1)

        self.create_sidebar()
        self.create_dashboard()

    # ======================================

    def create_sidebar(self):

        title = ctk.CTkLabel(
            self.sidebar,
            text="🔥 FlameKeeper",
            font=("Segoe UI", 26, "bold")
        )

        title.pack(pady=(30, 25))

        add_btn = ctk.CTkButton(
            self.sidebar,
            text="+ Add Streak",
            height=42,
            font=("Segoe UI", 16)
        )

        add_btn.pack(fill="x", padx=20)

    # ======================================

    def create_dashboard(self):

        title = ctk.CTkLabel(
            self.main,
            text="Dashboard",
            font=("Segoe UI", 34, "bold")
        )

        title.pack(anchor="w", padx=35, pady=(30, 10))

        subtitle = ctk.CTkLabel(
            self.main,
            text="Welcome back 🔥",
            font=("Segoe UI", 18)
        )

        subtitle.pack(anchor="w", padx=35)

        cards = ctk.CTkScrollableFrame(self.main)

        cards.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=30
        )

        StreakCard(
            cards,
            "📚",
            "IELTS",
            18,
            42,
            True
        ).pack(fill="x", pady=10)

        StreakCard(
            cards,
            "💻",
            "Python",
            7,
            15,
            False
        ).pack(fill="x", pady=10)

        StreakCard(
            cards,
            "🏋",
            "Gym",
            62,
            90,
            True
        ).pack(fill="x", pady=10)

if __name__ == "__main__":
    app = FlameKeeper()
    app.mainloop()