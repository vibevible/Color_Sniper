import tkinter as tk
from tkinter import ttk
import pyautogui
from PIL import Image, ImageTk, ImageDraw
import colorsys
import keyboard
import os


class SmoothSniperPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("저격총 스코프 스포이드")
        self.root.geometry("260x440")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        # 화면 중앙 X좌표 계산을 위한 변수
        self.screen_width, self.screen_height = pyautogui.size()
        self.screen_center_x = self.screen_width // 2

        self.is_picking = False
        self.current_hex = "#FFFFFF"
        self.scope_size = 180
        self.crosshair_size = 44  

        # 최근 색상을 저장할 리스트 (최대 5개, 기본값 흰색)
        self.color_history = ["#FFFFFF"] * 5

        # 토글 상태 변수 정의
        self.show_scope_var = tk.BooleanVar(value=True)
        self.show_gun_var = tk.BooleanVar(value=True)
        self.show_ammo_var = tk.BooleanVar(value=True)

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
            pil_img = Image.open("python\\colorPicker\\gun.png").convert("RGBA")
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

            screen_width, screen_height = pyautogui.size()
            self.base_gun_x = screen_width - self.gun_width
            self.base_gun_y = screen_height - self.gun_height - 10
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

        screen_height = pyautogui.size()[1]
        pos_x = 20
        pos_y = screen_height - 120
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

    def update_ammo_ui(self):
        ammo_path = "python\\colorPicker\\ammo.png"
        for i, hex_code in enumerate(self.color_history):
            try:
                # 색상이 #FFFFFF(빈 슬롯)이든 실제 색상이든 상관없이 ammo.png 기본 틀을 사용합니다.
                # 비어있을 때는 어두운 회색조(예: RGB 80, 80, 80)로 탄환 모양을 유지합니다.
                if hex_code == "#FFFFFF":
                    rgb = (80, 80, 80)  # 빈 탄환은 어두운 회색으로 표시
                else:
                    rgb = tuple(int(hex_code[j:j+2], 16) for j in (1, 3, 5))

                if os.path.exists(ammo_path):
                    ammo_img_main = Image.open(ammo_path).convert("RGBA").resize((20, 38), Image.Resampling.NEAREST)
                    ammo_img_overlay = Image.open(ammo_path).convert("RGBA").resize((26, 50), Image.Resampling.NEAREST)
                    
                    def apply_color(img):
                        data = img.getdata()
                        new_data = []
                        for item in data:
                            if item[0] > 60 or item[1] > 60 or item[2] > 60:
                                # 빈 슬롯(#FFFFFF)일 때는 투명도를 조금 낮춰서(예: 100) 비어있는 느낌을 줍니다.
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
                    # 이미지 파일이 없을 경우의 대체 코드
                    display_bg = hex_code if hex_code != "#FFFFFF" else "#222222"
                    self.ammo_labels[i].config(text=str(i+1), bg=display_bg, width=3, height=2)
                    self.overlay_ammo_labels[i].config(text=str(i+1), bg=display_bg, width=3, height=2)
            except Exception as e:
                print(f"탄환 이미지 처리 오류: {e}")

    def on_ammo_click(self, index):
        if index < len(self.color_history):
            selected_hex = self.color_history[index]
            self.current_hex = selected_hex
            self.hex_var.set(selected_hex)
            self.color_preview.config(bg=selected_hex)
            
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_hex)
            self.status_label.config(text=f"탄환 #{index+1} 선택됨! ({selected_hex})", fg="blue")
            self.root.after(1500, lambda: self.status_label.config(text="대기 중...", fg="gray"))

    def add_color_history(self, new_hex):
        # 이미 존재하는 색상이라도 순서대로 쌓이게 하려면 중복 제거를 빼거나 최신순으로 정렬
        # 여기서는 게임의 탄창처럼 얻은 순서대로 최대 5발까지 쌓이게 합니다.
        
        # 만약 이미 리스트에 5발이 꽉 찼다면 더 안 들어가게 하거나 밀어내야 합니다.
        # 기존처럼 중복을 제거하고 맨 앞에 넣되, 하얀색(#FFFFFF)은 가상의 빈칸이 아니라 진짜 색상으로 취급하지 않도록 합니다.
        
        # 하얀색(#FFFFFF) 빈 자리를 제외한 실제 장전된 탄환들만 가져옴
        valid_ammo = [c for c in self.color_history if c != "#FFFFFF"]
        
        if new_hex in valid_ammo:
            valid_ammo.remove(new_hex)
            
        valid_ammo.insert(0, new_hex)
        
        # 최대 5개까지만 유지
        if len(valid_ammo) > 5:
            valid_ammo = valid_ammo[:5]
            
        # 남은 자리는 #FFFFFF로 채워서 총 5개 길이를 유지
        while len(valid_ammo) < 5:
            valid_ammo.append("#FFFFFF")
            
        self.color_history = valid_ammo
        self.update_ammo_ui()

    def shoot_ammo(self):
        # 유효한 탄환(하얀색이 아닌 것)들만 필터링
        valid_ammo = [c for c in self.color_history if c != "#FFFFFF"]
        
        if valid_ammo:
            # 가장 먼저 장전된 탄환(또는 최근 탄환) 발사 - 여기서는 첫 번째(인덱스 0)를 발사한다고 가정
            shot_hex = valid_ammo.pop(0) 
            mx, my = pyautogui.position()
            self.show_shoot_effect(mx, my, shot_hex)

            # 발사 시 총 흔들림(반동) 효과 실행
            self.shake_gun_effect()

            # 남은 유효 탄환 뒤에 하얀색 빈칸을 채워 총 5개 유지
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

        shoot_path = "python\\colorPicker\\shoot.png"
        rgb = tuple(int(hex_color[j:j+2], 16) for j in (1, 3, 5))

        try:
            base_img = Image.open(shoot_path).convert("RGBA").resize((120, 120), Image.Resampling.NEAREST)
            
            # 이미지 색상 적용 (투명도 변화 없이 원본 색상 유지)
            data = base_img.getdata()
            new_data = []
            for item in data:
                if item[0] > 60 or item[1] > 60 or item[2] > 60:
                    new_data.append(rgb + (item[3],))
                else:
                    new_data.append((0, 0, 0, 0))
            base_img.putdata(new_data)

            tk_img = ImageTk.PhotoImage(base_img)
            canvas.create_image(0, 0, anchor="nw", image=tk_img)
            canvas.image = tk_img # 가비지 컬렉션 방지

        except Exception as e:
            print(f"shoot.png 로드 실패: {e}")
            shoot_win.destroy()
            return

        # 애니메이션 없이 일정 시간(예: 1200ms) 동안 유지된 후 바로 창 닫기
        self.root.after(1200, shoot_win.destroy)

        # def animate():
        #     if current_step[0] > 0:
        #         # 현재 단계에 따른 투명도 비율 계산 (점점 투명해짐)
        #         alpha_ratio = current_step[0] / steps
                
        #         # 투명도 조절을 위해 알파 채널 값 변경
        #         temp_img = tinted_img.copy()
        #         data = temp_img.getdata()
        #         new_data = []
        #         for item in data:
        #             if item[3] > 0:
        #                 new_alpha = int(item[3] * alpha_ratio)
        #                 new_data.append(item[:3] + (new_alpha,))
        #             else:
        #                 new_data.append((0, 0, 0, 0))
        #         temp_img.putdata(new_data)

        #         tk_img = ImageTk.PhotoImage(temp_img)
        #         canvas.delete("all")
        #         canvas.create_image(0, 0, anchor="nw", image=tk_img)
        #         canvas.image = tk_img

        #         current_step[0] -= 1
        #         self.root.after(30, animate)
        #     else:
        #         shoot_win.destroy()

        # animate()

        # def animate():
        #     if current_step[0] > 0:
        #         alpha = int((current_step[0] / steps) * 255)
        #         temp_img = base_img.copy()
        #         data = temp_img.getdata()
        #         new_data = []
        #         for item in data:
        #             if item[0] > 60 or item[1] > 60 or item[2] > 60:
        #                 new_data.append(rgb + (int(item[3] * (alpha / 255)),))
        #             else:
        #                 new_data.append((0, 0, 0, 0))
        #         temp_img.putdata(new_data)

        #         tk_img = ImageTk.PhotoImage(temp_img)
        #         canvas.delete("all")
        #         canvas.create_image(0, 0, anchor="nw", image=tk_img)
        #         canvas.image = tk_img

        #         current_step[0] -= 1
        #         self.root.after(30, animate)
        #     else:
        #         shoot_win.destroy()

        # animate()

    def on_toggle_scope(self):
        # 체크박스를 건드릴 때는 즉시 창을 숨기거나 띄우지 않고, 다음 업데이트 루프(스포이드 상태 여부)에 맡깁니다.
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
            
            # 장전 완료 시 총 흔들림 효과 실행
            self.shake_gun_effect()

            self.add_color_history(self.current_hex)
            self.copy_to_clipboard()

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_hex)
        old_text = self.status_label.cget("text")
        self.status_label.config(text="클립보드 복사됨!", fg="blue")
        self.root.after(1000, lambda: self.status_label.config(text="대기 중...", fg="green" if not self.is_picking else "red"))

    def update_loop(self):
        x, y = pyautogui.position()
        offset = self.crosshair_size // 2

        # --- [추가] 마우스 X위치에 따른 총 이미지 위치 연동 ---
        if self.show_gun_var.get():
            # 모니터 중앙(self.screen_center_x)을 기준으로 마우스가 떨어진 거리 계산
            # 예: max_offset으로 움직일 수 있는 최대 이동 폭 제한 (예: 50픽셀)
            max_offset = 50
            diff_x = x - self.screen_center_x
            
            # 편차를 비율로 환산하여 제한된 범위 내로 이동량 조절
            # 화면 끝까지 갔을 때 최대 max_offset 만큼 움직이도록 설정
            gun_move_offset = int((diff_x / self.screen_center_x) * max_offset)
            
            # 너무 과도하게 움직이지 않도록 범위 제한 (-max_offset ~ max_offset)
            gun_move_offset = max(-max_offset, min(max_offset, gun_move_offset))
            
            # 기존 기본 X좌표에 연동 오프셋을 더해줌
            current_gun_x = self.base_gun_x + gun_move_offset
            self.fixed_win.geometry(f"{self.gun_width}x{self.gun_height}+{current_gun_x}+{self.base_gun_y}")
        # ----------------------------------------------------

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
    app = SmoothSniperPicker(root)
    root.mainloop()