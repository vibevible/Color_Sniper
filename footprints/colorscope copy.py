import tkinter as tk
from tkinter import ttk
import pyautogui
from PIL import Image, ImageTk, ImageDraw
import keyboard


class SmoothSniperPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("저격총 스코프 스포이드")
        self.root.geometry("260x440")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        self.is_picking = False
        self.current_hex = "#FFFFFF"
        self.scope_size = 180
        self.crosshair_size = 44  # 조준선 전용 창 크기

        # 토글 상태 변수 정의 (기본값: 둘 다 켜짐)
        self.show_scope_var = tk.BooleanVar(value=True)
        self.show_gun_var = tk.BooleanVar(value=True)

        # 마우스를 따라다닐 창들 생성
        self.create_follower_windows()

        # 고정 이미지 창 생성
        self.create_fixed_image_window()

        # 메인 UI 설정
        self.setup_main_ui()

        # 단축키 등록
        keyboard.add_hotkey('ctrl+shift+c', self.toggle_picking)

        # 업데이트 루프 시작
        self.update_loop()

    def create_follower_windows(self):
        # 1. 기존 스코프 창
        self.follower = tk.Toplevel(self.root)
        self.follower.overrideredirect(True)
        self.follower.attributes("-topmost", True)
        self.follower.config(bg="magenta")
        self.follower.wm_attributes("-transparentcolor", "magenta")

        self.scope_canvas = tk.Canvas(
            self.follower,
            width=self.scope_size,
            height=self.scope_size,
            bg="magenta",
            highlightthickness=0
        )
        self.scope_canvas.pack()
        self.follower.withdraw()

        # 2. 조준선 전용 창 (중앙이 뚫린 형태)
        self.cross_follower = tk.Toplevel(self.root)
        self.cross_follower.overrideredirect(True)
        self.cross_follower.attributes("-topmost", True)
        self.cross_follower.config(bg="magenta")
        self.cross_follower.wm_attributes("-transparentcolor", "magenta")

        self.cross_canvas = tk.Canvas(
            self.cross_follower,
            width=self.crosshair_size,
            height=self.crosshair_size,
            bg="magenta",
            highlightthickness=0
        )
        self.cross_canvas.pack()
        
        # 조준선 이미지 미리 생성
        self.create_crosshair_image()
        self.cross_follower.withdraw()

    def create_crosshair_image(self):
        # 중앙을 과감히 비우고 바깥쪽 선만 남긴 투명 오버레이 이미지 생성
        size = self.crosshair_size
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        cross_color = (0, 255, 0, 240)
        
        # 중앙을 비우기 위해 간격을 띄움 (시작점과 끝점 조정)
        gap = 6
        length = 16
        
        # 상/하/좌/우 십자선 (중앙 공백 유지)
        draw.line([(center, center - length), (center, center - gap)], fill=cross_color, width=2)
        draw.line([(center, center + gap), (center, center + length)], fill=cross_color, width=2)
        draw.line([(center - length, center), (center - gap, center)], fill=cross_color, width=2)
        draw.line([(center + gap, center), (center + length, center)], fill=cross_color, width=2)
        
        self.tk_cross_img = ImageTk.PhotoImage(img)
        self.cross_canvas.delete("all")
        self.cross_canvas.create_image(0, 0, anchor="nw", image=self.tk_cross_img)

    def create_fixed_image_window(self):
        self.fixed_win = tk.Toplevel(self.root)
        self.fixed_win.overrideredirect(True)
        self.fixed_win.attributes("-topmost", True)

        self.fixed_win.config(bg="systemTransparent" if self.root.tk.call('tk', 'windowingsystem') == 'aqua' else "#000001")
        
        try:
            pil_img = Image.open("python\\colorPicker\\gun.png").convert("RGBA")
            width, height = pil_img.size
            bg_color = (0, 0, 1) 
            
            base_img = Image.new("RGBA", (width, height), bg_color + (255,))
            base_img.paste(pil_img, (0, 0), pil_img)

            self.fixed_tk_img = ImageTk.PhotoImage(base_img)

            self.fixed_canvas = tk.Canvas(
                self.fixed_win,
                width=width,
                height=height,
                bg="#000001",
                highlightthickness=0,
            )
            self.fixed_canvas.pack()
            self.fixed_canvas.create_image(
                0, 0, anchor="nw", image=self.fixed_tk_img
            )

            try:
                self.fixed_win.wm_attributes("-transparentcolor", "#000001")
            except:
                pass

            screen_width, screen_height = pyautogui.size()
            fix_x = screen_width - width
            fix_y = screen_height - height - 10
            self.fixed_win.geometry(f"{width}x{height}+{fix_x}+{fix_y}")

        except Exception as e:
            print(f"고정 이미지 로드 실패: {e}")
            tk.Label(self.fixed_win, text="[이미지 없음]", fg="red").pack()
            self.fixed_win.geometry("+100+100")

    def setup_main_ui(self):
        tk.Label(
            self.root, 
            text="[Ctrl + Shift + C]로 스포이드 켜기/끄기", 
            font=("Malgun Gothic", 9), pady=5
        ).pack()

        toggle_frame = tk.Frame(self.root)
        toggle_frame.pack(pady=5)

        self.scope_check = tk.Checkbutton(
            toggle_frame, text="스코프 표시", variable=self.show_scope_var,
            command=self.on_toggle_scope, font=("Malgun Gothic", 9)
        )
        self.scope_check.pack(side=tk.LEFT, padx=5)

        self.gun_check = tk.Checkbutton(
            toggle_frame, text="총 이미지 표시", variable=self.show_gun_var,
            command=self.on_toggle_gun, font=("Malgun Gothic", 9)
        )
        self.gun_check.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            self.root, text="대기 중...", font=("Malgun Gothic", 11, "bold"), fg="gray"
        )
        self.status_label.pack(pady=5)

        self.color_preview = tk.Frame(
            self.root, width=120, height=35, bg="white", 
            highlightthickness=1, highlightbackground="gray"
        )
        self.color_preview.pack(pady=5)
        self.color_preview.pack_propagate(False)

        self.hex_var = tk.StringVar(value="#FFFFFF")
        hex_entry = tk.Entry(
            self.root, textvariable=self.hex_var, 
            font=("Consolas", 14), justify="center", width=12
        )
        hex_entry.pack(pady=5)

        copy_btn = ttk.Button(
            self.root, text="클립보드 복사", command=self.copy_to_clipboard
        )
        copy_btn.pack(pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_toggle_scope(self):
        if self.is_picking:
            if self.show_scope_var.get():
                self.follower.deiconify()
                self.cross_follower.withdraw()
            else:
                self.follower.withdraw()
                self.cross_follower.deiconify()

    def on_toggle_gun(self):
        if self.show_gun_var.get():
            self.fixed_win.deiconify()
        else:
            self.fixed_win.withdraw()

    def create_circular_scope_image(self, pil_image, current_rgb):
        size = self.scope_size
        img_resized = pil_image.resize((size, size), Image.Resampling.NEAREST).convert("RGBA")
        
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((5, 5, size - 5, size - 5), fill=255)
        
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        draw_overlay.ellipse((1, 1, size - 1, size - 1), outline=(20, 20, 20), width=5)
        draw_overlay.ellipse((6, 6, size - 6, size - 6), outline=(90, 100, 90), width=2)
        
        center = size // 2
        cross_color = (0, 255, 0, 220)
        draw_overlay.line([(center - 45, center), (center - 12, center)], fill=cross_color, width=2)
        draw_overlay.line([(center + 12, center), (center + 45, center)], fill=cross_color, width=2)
        draw_overlay.line([(center, center - 45), (center, center - 12)], fill=cross_color, width=2)
        draw_overlay.line([(center, center + 12), (center, center + 45)], fill=cross_color, width=2)
        draw_overlay.ellipse((center - 3, center - 3, center + 3, center + 3), outline=cross_color, width=2)

        chip_x, chip_y = size - 48, 22
        chip_radius = 14
        
        draw_overlay.ellipse(
            (chip_x - chip_radius - 2, chip_y - chip_radius - 2, chip_x + chip_radius + 2, chip_y + chip_radius + 2),
            fill=(255, 255, 255, 230), outline=(50, 50, 50), width=2
        )
        draw_overlay.ellipse(
            (chip_x - chip_radius, chip_y - chip_radius, chip_x + chip_radius, chip_y + chip_radius),
            fill=current_rgb + (255,)
        )

        img_resized.putalpha(mask)
        return Image.alpha_composite(img_resized, overlay)

    def toggle_picking(self):
        self.is_picking = not self.is_picking
        if self.is_picking:
            self.status_label.config(text="● 조준 스포이드 작동 중...", fg="red")
            if self.show_scope_var.get():
                self.follower.deiconify()
            else:
                self.cross_follower.deiconify()
        else:
            self.status_label.config(text="색상 확정 완료!", fg="green")
            self.follower.withdraw()
            self.cross_follower.withdraw()
            self.copy_to_clipboard()

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_hex)
        old_text = self.status_label.cget("text")
        self.status_label.config(text="클립보드 복사됨!", fg="blue")
        self.root.after(1000, lambda: self.status_label.config(text=old_text, fg="green" if not self.is_picking else "red"))

    def update_loop(self):
        if self.is_picking:
            x, y = pyautogui.position()
            
            if self.show_scope_var.get():
                self.follower.geometry(f"{self.scope_size}x{self.scope_size}+{x}+{y}")
            else:
                offset = self.crosshair_size // 2
                self.cross_follower.geometry(f"{self.crosshair_size}x{self.crosshair_size}+{x - offset}+{y - offset}")

            box_size = 18
            try:
                screenshot = pyautogui.screenshot(
                    region=(x - box_size, y - box_size, box_size * 2, box_size * 2)
                )

                center_rgb = screenshot.getpixel((box_size, box_size))
                self.current_hex = f"#{center_rgb[0]:02X}{center_rgb[1]:02X}{center_rgb[2]:02X}"

                self.hex_var.set(self.current_hex)
                self.color_preview.config(bg=self.current_hex)

                if self.show_scope_var.get():
                    scope_img = self.create_circular_scope_image(screenshot, center_rgb)
                    self.tk_scope_img = ImageTk.PhotoImage(scope_img)
                    self.scope_canvas.delete("all")
                    self.scope_canvas.create_image(0, 0, anchor="nw", image=self.tk_scope_img)

            except Exception as e:
                print(f"Error: {e}")

        self.root.after(30, self.update_loop)

    def on_close(self):
        keyboard.unhook_all()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmoothSniperPicker(root)
    root.mainloop()