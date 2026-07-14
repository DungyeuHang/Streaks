import customtkinter as ctk


class StreakCard(ctk.CTkFrame):

    def __init__(
        self,
        master,
        icon,
        name,
        current,
        best,
        completed=False
    ):
        super().__init__(
            master,
            corner_radius=18,
            height=180
        )

        self.pack_propagate(False)

        # ========= LEFT =========

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=20, pady=18)

        icon_label = ctk.CTkLabel(
            left,
            text=icon,
            font=("Segoe UI Emoji", 34)
        )
        icon_label.pack(anchor="w")

        name_label = ctk.CTkLabel(
            left,
            text=name,
            font=("Segoe UI", 22, "bold")
        )
        name_label.pack(anchor="w", pady=(5, 0))

        streak_label = ctk.CTkLabel(
            left,
            text=f"🔥 {current} DAYS      🏆 {best} DAYS",
            font=("Segoe UI Semibold", 18)
        )
        streak_label.pack(anchor="w", pady=(6, 0))

        # ========= RIGHT =========

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=20)

        self.checkbox = ctk.CTkCheckBox(
            right,
            text="Today",
            font=("Segoe UI", 16)
        )

        if completed:
            self.checkbox.select()

        self.checkbox.pack(expand=True)