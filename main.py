import tkinter as tk
from tkinter import ttk
import pyautogui
from PIL import Image, ImageTk, ImageDraw
import keyboard
import colorsys
import sys
import os

def resource_path(relative_path):
    """ PyInstaller로 빌드했을 때와 일반 파이썬으로 실행할 때의 리소스 경로를 다르게 지정 """
    try:
        # PyInstaller가 임시로 풀어놓은 경로
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ColorSniper:
    def __init__(self, root):
        self.root = root
        self.root.title("저격총 스코프 스포이드")
        self.root.geometry("260x540")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        self.is_picking = False
        self.current_hex = "#FFFFFF"
        self.scope_size = 180
        self.crosshair_size = 44  

        self.gun_width = 100
        self.gun_height = 100
        self.base_gun_x = 0
        self.base_gun_y = 0

        # 최근 색상을 저장할 리스트 (최대 5개, 기본값 #FFFFFF 빈 슬롯)
        self.color_history = ["#FFFFFF"] * 5

        # 토글 상태 변수 정의
        self.show_scope_var = tk.BooleanVar(value=True)
        self.show_gun_var = tk.BooleanVar(value=True)
        self.show_ammo_var = tk.BooleanVar(value=True)

        # 화면 크기 및 중앙 좌표 계산
        self.screen_width, self.screen_height = pyautogui.size()
        self.screen_center_x = self.screen_width // 2

        # 마우스를 따라다닐 창들 생성
        self.create_follower_windows()

        # 고정 이미지 창 생성 (우측 하단 총)
        self.create_fixed_image_window()

        # 좌측 하단 고정 탄환 오버레이 창 생성
        self.create_ammo_overlay_window()

        # 메인 UI 설정
        self.setup_main_ui()

        # 단축키 등록 (스포이드 토글: Ctrl+Shift+C / 발사: Ctrl+Shift+X)
        keyboard.add_hotkey('ctrl+shift+c', self.toggle_picking)
        keyboard.add_hotkey('ctrl+shift+x', self.shoot_ammo)

        # 프로그램 켜자마자 미니 조준선 표시
        self.cross_follower.deiconify()

        # 초기 색상 디스플레이 설정
        self.update_color_displays("#FFFFFF")

        # 업데이트 루프 시작
        self.update_loop()

    def create_follower_windows(self):
        # 1. 스코프 창
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

        # 2. 조준선 전용 창
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
        
        self.create_crosshair_image()
        self.cross_follower.withdraw()

    def create_crosshair_image(self, size=44):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        cross_color = (0, 255, 0, 240)
        
        gap = 6
        length = 16
        
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
            pil_img = Image.open("python\\colorPicker\\ColorSniper\\gun.png").convert("RGBA")
            self.gun_width, self.gun_height = pil_img.size
            bg_color = (0, 0, 1) 
            
            base_img = Image.new("RGBA", (self.gun_width, self.gun_height), bg_color + (255,))
            base_img.paste(pil_img, (0, 0), pil_img)

            self.fixed_tk_img = ImageTk.PhotoImage(base_img)

            self.fixed_canvas = tk.Canvas(
                self.fixed_win,
                width=self.gun_width,
                height=self.gun_height,
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

            self.base_gun_x = self.screen_width - self.gun_width
            self.base_gun_y = self.screen_height - self.gun_height - 10
            self.fixed_win.geometry(f"{self.gun_width}x{self.gun_height}+{self.base_gun_x}+{self.base_gun_y}")

        except Exception as e:
            print(f"고정 이미지 로드 실패: {e}")
            tk.Label(self.fixed_win, text="[이미지 없음]", fg="red").pack()
            self.fixed_win.geometry("+100+100")

    def shake_gun_effect(self):
        """우측 하단 총 이미지가 좌우로 흔들리는 반동 효과 애니메이션"""
        if not self.show_gun_var.get():
            return
            
        offsets = [6, -6, 4, -4, 2, -2, 0]
        
        def animate_shake(index=0):
            if index < len(offsets):
                current_offset = offsets[index]
                new_x = self.base_gun_x + current_offset
                self.fixed_win.geometry(f"{self.gun_width}x{self.gun_height}+{new_x}+{self.base_gun_y}")
                self.root.after(25, lambda: animate_shake(index + 1))
            else:
                self.fixed_win.geometry(f"{self.gun_width}x{self.gun_height}+{self.base_gun_x}+{self.base_gun_y}")

        animate_shake()

    def create_ammo_overlay_window(self):
        self.ammo_win = tk.Toplevel(self.root)
        self.ammo_win.overrideredirect(True)
        self.ammo_win.attributes("-topmost", True)
        self.ammo_win.config(bg="systemTransparent" if self.root.tk.call('tk', 'windowingsystem') == 'aqua' else "#000002")

        self.ammo_overlay_frame = tk.Frame(self.ammo_win, bg="#000002")
        self.ammo_overlay_frame.pack(padx=5, pady=5)

        self.overlay_ammo_labels = []
        for i in range(5):
            lbl = tk.Label(self.ammo_overlay_frame, bg="#000002", bd=0, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=4)
            lbl.bind("<Button-1>", lambda e, idx=i: self.on_ammo_click(idx))
            self.overlay_ammo_labels.append(lbl)

        try:
            self.ammo_win.wm_attributes("-transparentcolor", "#000002")
        except:
            pass

        pos_x = 20
        pos_y = self.screen_height - 120
        self.ammo_win.geometry(f"+{pos_x}+{pos_y}")

    def setup_main_ui(self):
        tk.Label(
            self.root, 
            text="[Ctrl+Shift+C] 스포이드 / [Ctrl+Shift+X] 발사", 
            font=("Malgun Gothic", 8), pady=3
        ).pack()

        toggle_frame = tk.Frame(self.root)
        toggle_frame.pack(pady=2)

        self.scope_check = tk.Checkbutton(
            toggle_frame, text="스코프 표시", variable=self.show_scope_var,
            command=self.on_toggle_scope, font=("Malgun Gothic", 9)
        )
        self.scope_check.pack(side=tk.LEFT, padx=3)

        self.gun_check = tk.Checkbutton(
            toggle_frame, text="총 이미지 표시", variable=self.show_gun_var,
            command=self.on_toggle_gun, font=("Malgun Gothic", 9)
        )
        self.gun_check.pack(side=tk.LEFT, padx=3)

        self.ammo_check = tk.Checkbutton(
            self.root, text="좌측 하단 탄환 표시", variable=self.show_ammo_var,
            command=self.on_toggle_ammo, font=("Malgun Gothic", 9)
        )
        self.ammo_check.pack(pady=2)

        self.status_label = tk.Label(
            self.root, text="대기 중...", font=("Malgun Gothic", 10, "bold"), fg="gray"
        )
        self.status_label.pack(pady=2)

        self.color_preview = tk.Frame(
            self.root, width=120, height=30, bg="white", 
            highlightthickness=1, highlightbackground="gray"
        )
        self.color_preview.pack(pady=2)
        self.color_preview.pack_propagate(False)

        self.hex_var = tk.StringVar(value="#FFFFFF")
        hex_entry = tk.Entry(
            self.root, textvariable=self.hex_var, 
            font=("Consolas", 12), justify="center", width=12
        )
        hex_entry.pack(pady=2)

        copy_btn = ttk.Button(
            self.root, text="클립보드 복사", command=self.copy_to_clipboard
        )
        copy_btn.pack(pady=2)

        # 색상 포맷 정보 프레임 및 라벨들
        format_frame = tk.LabelFrame(self.root, text=" 색상 포맷 정보 ", font=("Malgun Gothic", 8))
        format_frame.pack(pady=4, padx=10, fill="x")

        self.rgb_label = tk.Label(format_frame, text="R: 255  G: 255  B: 255", font=("Consolas", 9), anchor="w")
        self.rgb_label.pack(fill="x", padx=5, pady=1)

        self.hsl_label = tk.Label(format_frame, text="H: 0°  S: 0%  L: 100%", font=("Consolas", 9), anchor="w")
        self.hsl_label.pack(fill="x", padx=5, pady=1)

        self.hsv_label = tk.Label(format_frame, text="H: 0°  S: 0%  V: 100%", font=("Consolas", 9), anchor="w")
        self.hsv_label.pack(fill="x", padx=5, pady=1)

        self.cmyk_label = tk.Label(format_frame, text="C: 0%  M: 0%  Y: 0%  K: 0%", font=("Consolas", 9), anchor="w")
        self.cmyk_label.pack(fill="x", padx=5, pady=1)

        history_frame = tk.LabelFrame(self.root, text=" 최근 탄환 색상 (클릭시 복사) ", font=("Malgun Gothic", 8))
        history_frame.pack(pady=4, padx=10, fill="x")

        self.ammo_container = tk.Frame(history_frame)
        self.ammo_container.pack(pady=2)

        self.ammo_labels = []
        for i in range(5):
            lbl = tk.Label(self.ammo_container, bd=1, relief="solid", cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<Button-1>", lambda e, idx=i: self.on_ammo_click(idx))
            self.ammo_labels.append(lbl)

        self.update_ammo_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def convert_color_formats(self, hex_code):
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)

        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hsv_str = f"H: {int(h * 360)}°  S: {int(s * 100)}%  V: {int(v * 100)}%"

        h_l, l, s_l = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        hsl_str = f"H: {int(h_l * 360)}°  S: {int(s_l * 100)}%  L: {int(l * 100)}%"

        if r == 0 and g == 0 and b == 0:
            cmyk_str = "C: 0%  M: 0%  Y: 0%  K: 100%"
        else:
            c = 1 - (r / 255.0)
            m = 1 - (g / 255.0)
            y = 1 - (b / 255.0)
            k = min(c, min(m, y))
            
            c = (c - k) / (1 - k) if (1 - k) > 0 else 0
            m = (m - k) / (1 - k) if (1 - k) > 0 else 0
            y = (y - k) / (1 - k) if (1 - k) > 0 else 0
            
            cmyk_str = f"C: {int(c * 100)}%  M: {int(m * 100)}%  Y: {int(y * 100)}%  K: {int(k * 100)}%"

        rgb_str = f"R: {r}  G: {g}  B: {b}"
        return rgb_str, hsl_str, hsv_str, cmyk_str

    def update_color_displays(self, hex_code):
        self.current_hex = hex_code
        self.hex_var.set(hex_code)
        self.color_preview.config(bg=hex_code)

        rgb_s, hsl_s, hsv_s, cmyk_s = self.convert_color_formats(hex_code)
        self.rgb_label.config(text=rgb_s)
        self.hsl_label.config(text=hsl_s)
        self.hsv_label.config(text=hsv_s)
        self.cmyk_label.config(text=cmyk_s)

    def update_ammo_ui(self):
        for i, hex_code in enumerate(self.color_history):
            try:
                if hex_code == "#FFFFFF":
                    rgb = (80, 80, 80)
                else:
                    rgb = tuple(int(hex_code[j:j+2], 16) for j in (1, 3, 5))

                if os.path.exists(resource_path("ammo.png")):
                    ammo_img_main = Image.open(resource_path("ammo.png")).convert("RGBA").resize((20, 38), Image.Resampling.NEAREST)
                    ammo_img_overlay = Image.open(resource_path("ammo.png")).convert("RGBA").resize((26, 50), Image.Resampling.NEAREST)
                    
                    def apply_color(img):
                        data = img.get_flattened_data()
                        new_data = []
                        for item in data:
                            if item[0] > 60 or item[1] > 60 or item[2] > 60:
                                alpha = item[3] if hex_code != "#FFFFFF" else int(item[3] * 0.4)
                                new_data.append(rgb + (alpha,))
                            else:
                                new_data.append(item)
                        img.putdata(new_data)
                        return img

                    processed_main = apply_color(ammo_img_main)
                    processed_overlay = apply_color(ammo_img_overlay)
                    
                    tk_img_main = ImageTk.PhotoImage(processed_main)
                    self.ammo_labels[i].config(image=tk_img_main, text="", bg="SystemButtonFace")
                    self.ammo_labels[i].image = tk_img_main
                    
                    tk_img_overlay = ImageTk.PhotoImage(processed_overlay)
                    self.overlay_ammo_labels[i].config(image=tk_img_overlay, text="", bg="#000002")
                    self.overlay_ammo_labels[i].image = tk_img_overlay
                else:
                    display_bg = hex_code if hex_code != "#FFFFFF" else "#222222"
                    self.ammo_labels[i].config(text=str(i+1), bg=display_bg, width=3, height=2)
                    self.overlay_ammo_labels[i].config(text=str(i+1), bg=display_bg, width=3, height=2)
            except Exception as e:
                print(f"탄환 이미지 처리 오류: {e}")

    def on_ammo_click(self, index):
        if index < len(self.color_history):
            selected_hex = self.color_history[index]
            self.update_color_displays(selected_hex)
            
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_hex)
            self.status_label.config(text=f"탄환 #{index+1} 선택됨! ({selected_hex})", fg="blue")
            self.root.after(1500, lambda: self.status_label.config(text="대기 중...", fg="gray"))

    def add_color_history(self, new_hex):
        valid_ammo = [c for c in self.color_history if c != "#FFFFFF"]
        
        if new_hex in valid_ammo:
            valid_ammo.remove(new_hex)
            
        valid_ammo.insert(0, new_hex)
        
        if len(valid_ammo) > 5:
            valid_ammo = valid_ammo[:5]
            
        while len(valid_ammo) < 5:
            valid_ammo.append("#FFFFFF")
            
        self.color_history = valid_ammo
        self.update_ammo_ui()

    def shoot_ammo(self):
        valid_ammo = [c for c in self.color_history if c != "#FFFFFF"]
        
        if valid_ammo:
            shot_hex = valid_ammo.pop(0)
            mx, my = pyautogui.position()
            self.show_shoot_effect(mx, my, shot_hex)

            self.shake_gun_effect()

            while len(valid_ammo) < 5:
                valid_ammo.append("#FFFFFF")
                
            self.color_history = valid_ammo
            self.update_ammo_ui()
            
            self.status_label.config(text=f"발사 완료! ({shot_hex})", fg="green")
            self.root.after(1500, lambda: self.status_label.config(text="대기 중...", fg="gray"))
        else:
            self.status_label.config(text="탄환이 없습니다!", fg="red")
            self.root.after(1500, lambda: self.status_label.config(text="대기 중...", fg="gray"))

    def show_shoot_effect(self, x, y, hex_color):
        shoot_win = tk.Toplevel(self.root)
        shoot_win.overrideredirect(True)
        shoot_win.attributes("-topmost", True)
        shoot_win.config(bg="systemTransparent" if self.root.tk.call('tk', 'windowingsystem') == 'aqua' else "#000003")

        canvas = tk.Canvas(shoot_win, width=120, height=120, bg="#000003", highlightthickness=0)
        canvas.pack()

        try:
            shoot_win.wm_attributes("-transparentcolor", "#000003")
        except:
            pass

        win_x = x - 60
        win_y = y - 60
        shoot_win.geometry(f"120x120+{win_x}+{win_y}")

        rgb = tuple(int(hex_color[j:j+2], 16) for j in (1, 3, 5))

        try:
            base_img = Image.open(resource_path("shoot.png")).convert("RGBA").resize((120, 120), Image.Resampling.NEAREST)
            data = base_img.get_flattened_data()
            new_data = []
            for item in data:
                if item[0] > 60 or item[1] > 60 or item[2] > 60:
                    new_data.append(rgb + (item[3],))
                else:
                    new_data.append((0, 0, 0, 0))
            base_img.putdata(new_data)

            tk_img = ImageTk.PhotoImage(base_img)
            canvas.create_image(0, 0, anchor="nw", image=tk_img)
            canvas.image = tk_img

        except Exception as e:
            print(f"shoot.png 로드 실패: {e}")
            shoot_win.destroy()
            return

        self.root.after(300, shoot_win.destroy)

    def on_toggle_scope(self):
        pass

    def on_toggle_gun(self):
        if self.show_gun_var.get():
            self.fixed_win.deiconify()
        else:
            self.fixed_win.withdraw()

    def on_toggle_ammo(self):
        if self.show_ammo_var.get():
            self.ammo_win.deiconify()
        else:
            self.ammo_win.withdraw()

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
        else:
            self.status_label.config(text="장전 완료!", fg="green")
            self.shake_gun_effect()
            self.add_color_history(self.current_hex)
            self.copy_to_clipboard()

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_hex)
        self.status_label.config(text="클립보드 복사됨!", fg="blue")
        self.root.after(1000, lambda: self.status_label.config(text="대기 중...", fg="green" if not self.is_picking else "red"))

    def update_loop(self):
        x, y = pyautogui.position()
        offset = self.crosshair_size // 2

        # 마우스 X위치에 따른 총 이미지 위치 연동 (Parallax 효과)
        if self.show_gun_var.get():
            max_offset = 60
            diff_x = x - self.screen_center_x
            gun_move_offset = int((diff_x / self.screen_center_x) * max_offset)
            gun_move_offset = max(-max_offset, min(max_offset, gun_move_offset))
            current_gun_x = self.base_gun_x + gun_move_offset
            self.fixed_win.geometry(f"{self.gun_width}x{self.gun_height}+{current_gun_x}+{self.base_gun_y}")

        # 1. 스포이드 작동 중일 때
        if self.is_picking:
            if self.show_scope_var.get():
                self.cross_follower.withdraw()
                self.follower.deiconify()
                self.follower.geometry(f"{self.scope_size}x{self.scope_size}+{x}+{y}")
            else:
                self.follower.withdraw()
                self.cross_follower.deiconify()
                self.cross_follower.geometry(f"{self.crosshair_size}x{self.crosshair_size}+{x - offset}+{y - offset}")

            box_size = 18
            try:
                screenshot = pyautogui.screenshot(
                    region=(x - box_size, y - box_size, box_size * 2, box_size * 2)
                )
                center_rgb = screenshot.getpixel((box_size, box_size))
                new_hex = f"#{center_rgb[0]:02X}{center_rgb[1]:02X}{center_rgb[2]:02X}"
                
                # 색상 동기화 및 포맷 업데이트 호출
                self.update_color_displays(new_hex)

                if self.show_scope_var.get():
                    scope_img = self.create_circular_scope_image(screenshot, center_rgb)
                    self.tk_scope_img = ImageTk.PhotoImage(scope_img)
                    self.scope_canvas.delete("all")
                    self.scope_canvas.create_image(0, 0, anchor="nw", image=self.tk_scope_img)

            except Exception as e:
                print(f"Error: {e}")

        # 2. 평소 대기 중이거나 발사할 때
        else:
            self.follower.withdraw()
            self.cross_follower.deiconify()
            self.cross_follower.geometry(f"{self.crosshair_size}x{self.crosshair_size}+{x - offset}+{y - offset}")

        self.root.after(30, self.update_loop)

    def on_close(self):
        keyboard.unhook_all()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorSniper(root)
    root.mainloop()