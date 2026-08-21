import tkinter as tk
from tkinter import ttk
import pyautogui
from PIL import Image, ImageTk, ImageDraw
import keyboard


class SmoothSniperPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("저격총 스코프 스포이드")
        self.root.geometry("260x380")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        self.is_picking = False
        self.current_hex = "#FFFFFF"
        self.scope_size = 180

        # 마우스를 따라다닐 미니 스코프 창 생성
        self.create_follower_window()

        self.create_fixed_image_window()

        self.setup_main_ui()

        # 단축키 등록
        keyboard.add_hotkey('ctrl+shift+c', self.toggle_picking)

        # 업데이트 루프 시작
        self.update_loop()

    def create_follower_window(self):
        # 마우스를 쫓아다니는 투명 창 (withdraw 사용 안 함!)
        self.follower = tk.Toplevel(self.root)
        self.follower.overrideredirect(True)
        self.follower.attributes("-topmost", True)
        
        # Windows 투명 색상 설정
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
        self.follower.withdraw()  # 처음에는 숨김

    def create_fixed_image_window(self):
      # 화면 고정 위치에 띄울 투명 창 생성
      self.fixed_win = tk.Toplevel(self.root)
      self.fixed_win.overrideredirect(True)
      self.fixed_win.attributes("-topmost", True)

      # 윈도우 자체의 투명색 기능(-transparentcolor)을 쓰면 테두리가 남으므로 제거합니다.
      # 대신 캔버스 배경을 투명하게 처리합니다.
      self.fixed_win.config(bg="systemTransparent" if self.root.tk.call('tk', 'windowingsystem') == 'aqua' else "#000001")
      
      try:
        # 1. 투명 PNG 이미지 불러오기
        pil_img = Image.open("python\\colorPicker\\gun.png").convert("RGBA")
        width, height = pil_img.size

        # 2. 윈도우 투명 색상 설정 (배경색과 동일하게 맞춤)
        bg_color = (0, 0, 1) # 거의 검은색에 가까운 색
        
        # 배경 이미지 생성 후 PNG 합성
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

        # 윈도우 배경색을 특정 색으로 투명하게 처리 (윈도우즈 전용)
        try:
            self.fixed_win.wm_attributes("-transparentcolor", "#000001")
        except:
            pass

        # 3. 모니터(화면) 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 4. 우측 하단 좌표 계산
        margin_right = 0
        margin_bottom = 10

        fix_x = screen_width - width - margin_right
        fix_y = screen_height - height - margin_bottom

        # 5. 계산된 좌표 적용
        self.fixed_win.geometry(f"{width}x{height}+{fix_x}+{fix_y}")

      except Exception as e:
        print(
            f"고정 이미지 로드 실패 ('python\\colorPicker\\gun.png' 파일 확인 필요): {e}"
        )
        tk.Label(self.fixed_win, text="[이미지 없음]", fg="red").pack()
        self.fixed_win.geometry("+100+100")

    def setup_main_ui(self):
        tk.Label(
            self.root, 
            text="[Ctrl + Shift + C]로 스포이드 켜기/끄기", 
            font=("Malgun Gothic", 9), pady=10
        ).pack()

        self.status_label = tk.Label(
            self.root, text="대기 중...", font=("Malgun Gothic", 11, "bold"), fg="gray"
        )
        self.status_label.pack(pady=5)

        self.color_preview = tk.Frame(
            self.root, width=120, height=35, bg="white", 
            highlightthickness=1, highlightbackground="gray"
        )
        self.color_preview.pack(pady=10)
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

    def create_circular_scope_image(self, pil_image):
        size = self.scope_size
        img_resized = pil_image.resize((size, size), Image.Resampling.NEAREST).convert("RGBA")
        
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((5, 5, size - 5, size - 5), fill=255)
        
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        # 테두리 및 십자선
        draw_overlay.ellipse((1, 1, size - 1, size - 1), outline=(20, 20, 20), width=5)
        draw_overlay.ellipse((6, 6, size - 6, size - 6), outline=(90, 100, 90), width=2)
        
        center = size // 2
        cross_color = (0, 255, 0, 220)
        draw_overlay.line([(center - 45, center), (center - 12, center)], fill=cross_color, width=2)
        draw_overlay.line([(center + 12, center), (center + 45, center)], fill=cross_color, width=2)
        draw_overlay.line([(center, center - 45), (center, center - 12)], fill=cross_color, width=2)
        draw_overlay.line([(center, center + 12), (center, center + 45)], fill=cross_color, width=2)
        draw_overlay.ellipse((center - 3, center - 3, center + 3, center + 3), outline=cross_color, width=2)

        img_resized.putalpha(mask)
        return Image.alpha_composite(img_resized, overlay)

    def toggle_picking(self):
        self.is_picking = not self.is_picking
        if self.is_picking:
            self.status_label.config(text="● 조준 스포이드 작동 중...", fg="red")
            self.follower.deiconify()
        else:
            self.status_label.config(text="색상 확정 완료!", fg="green")
            self.follower.withdraw()
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

            # [핵심 해결책] 스코프 창을 마우스 바로 뒤가 아니라, 
            # 마우스 커서 우측 하단에 띄웁니다.
            # 이렇게 하면 캡처 영역(마우스 중심)과 스코프 창이 서로 겹치지 않아 
            # withdraw를 쓰지 않아도 잔상/십자선 캡처 및 깜빡임이 안 생깁니다!
            self.follower.geometry(f"{self.scope_size}x{self.scope_size}+{x}+{y}")

            box_size = 18
            try:
                # 창을 숨기는 작업(withdraw) 없이 곧바로 화면 캡처 수행 (깜빡임 원인 차단)
                screenshot = pyautogui.screenshot(
                    region=(x - box_size, y - box_size, box_size * 2, box_size * 2)
                )

                center_rgb = screenshot.getpixel((box_size, box_size))
                self.current_hex = f"#{center_rgb[0]:02X}{center_rgb[1]:02X}{center_rgb[2]:02X}"

                # UI 업데이트
                self.hex_var.set(self.current_hex)
                self.color_preview.config(bg=self.current_hex)

                # 스코프 캔버스 업데이트
                scope_img = self.create_circular_scope_image(screenshot)
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