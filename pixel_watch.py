import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import pyautogui
import cv2
import numpy as np
import winsound
import keyboard
import datetime
from PIL import Image, ImageTk  # ★ 이미지 처리를 위해 추가됨

class MacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("수강신청 빈자리 감지기 (이미지 확인 기능)")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        # --- 상태 변수 ---
        self.is_running = False
        self.region = None
        self.ref_imgs = []
        self.start_time = None
        self.subject_count = 5
        self.move_delay = 0.2

        # --- UI 구성 ---
        self.timer_label = tk.Label(root, text="대기 중...", font=("Arial", 24, "bold"), fg="blue")
        self.timer_label.pack(pady=20)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        self.btn_set_region = tk.Button(btn_frame, text="1. 영역 설정 (F2)", command=self.start_set_region_thread, width=20, height=2)
        self.btn_set_region.grid(row=0, column=0, padx=5, pady=5)

        self.btn_learn = tk.Button(btn_frame, text="2. 학습 시작 (F2)", command=self.start_learning_thread, width=20, height=2, state="disabled")
        self.btn_learn.grid(row=0, column=1, padx=5, pady=5)

        self.btn_start = tk.Button(root, text="3. 감시 시작 (3초 대기)", command=self.start_monitoring, width=40, height=3, bg="green", fg="white", font=("Arial", 12, "bold"), state="disabled")
        self.btn_start.pack(pady=10)

        self.btn_stop = tk.Button(root, text="중단 (ESC)", command=self.stop_monitoring, width=40, bg="orange", fg="black")
        self.btn_stop.pack(pady=2)

        self.btn_reset = tk.Button(root, text="↻ 초기화 (처음부터 다시)", command=self.reset_app, width=40, bg="lightblue", fg="black")
        self.btn_reset.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=55, height=12, state='disabled')
        self.log_area.pack(pady=10)

        tk.Button(root, text="소리 테스트", command=self.play_sound).place(x=420, y=10)

        self.log("프로그램 준비 완료.")
        self.log("1단계 [영역 설정]부터 진행해주세요.")

    def log(self, msg):
        self.log_area.config(state='normal')
        current_time = datetime.datetime.now().strftime("[%H:%M:%S] ")
        self.log_area.insert(tk.END, current_time + msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def play_sound(self):
        threading.Thread(target=lambda: winsound.Beep(2500, 300), daemon=True).start()

    def capture_screen(self):
        if self.region is None:
            return None
        screenshot = pyautogui.screenshot(region=self.region)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # --- ★ 이미지 팝업 도우미 함수들 ★ ---
    def popup_learning_result(self):
        """학습된 모든 이미지를 새 창에 띄워줌"""
        top = tk.Toplevel(self.root)
        top.title("학습된 이미지 확인")
        
        tk.Label(top, text="저장된 기준 이미지들입니다. (확인 후 닫기)", font=("Arial", 12)).pack(pady=10)
        
        frame = tk.Frame(top)
        frame.pack(padx=10, pady=10)

        for i, img_data in enumerate(self.ref_imgs):
            # CV2(Gray) -> PIL Image 변환
            img_rgb = cv2.cvtColor(img_data, cv2.COLOR_GRAY2RGB)
            pil_img = Image.fromarray(img_rgb)
            # 너무 작으면 보기 힘드니까 2배 확대
            pil_img = pil_img.resize((pil_img.width * 2, pil_img.height * 2), Image.Resampling.NEAREST)
            tk_img = ImageTk.PhotoImage(pil_img)

            sub_frame = tk.Frame(frame, borderwidth=1, relief="solid")
            sub_frame.grid(row=0, column=i, padx=5)
            
            lbl = tk.Label(sub_frame, image=tk_img)
            lbl.image = tk_img # 참조 유지
            lbl.pack()
            tk.Label(sub_frame, text=f"{i+1}번").pack()

    def popup_comparison(self, ref_img, curr_img, idx):
        """발견 시 기준 이미지 vs 현재 이미지 비교"""
        top = tk.Toplevel(self.root)
        top.title(f"빈자리 발견! ({idx}번째 줄)")
        top.attributes('-topmost', True) # 맨 위에 띄우기

        tk.Label(top, text=f"🔥 {idx}번째 줄에서 변화 감지! 🔥", font=("Arial", 14, "bold"), fg="red").pack(pady=10)

        frame = tk.Frame(top)
        frame.pack(padx=10, pady=10)

        # 1. 저장된 이미지 (Reference)
        img_ref_rgb = cv2.cvtColor(ref_img, cv2.COLOR_GRAY2RGB)
        pil_ref = Image.fromarray(img_ref_rgb)
        pil_ref = pil_ref.resize((pil_ref.width * 2, pil_ref.height * 2), Image.Resampling.NEAREST)
        tk_ref = ImageTk.PhotoImage(pil_ref)

        f1 = tk.Frame(frame)
        f1.pack(side="left", padx=20)
        tk.Label(f1, text="[저장된 화면]", fg="blue", font=("bold")).pack()
        lbl1 = tk.Label(f1, image=tk_ref)
        lbl1.image = tk_ref
        lbl1.pack()

        # 2. 현재 이미지 (Current)
        img_curr_rgb = cv2.cvtColor(curr_img, cv2.COLOR_GRAY2RGB)
        pil_curr = Image.fromarray(img_curr_rgb)
        pil_curr = pil_curr.resize((pil_curr.width * 2, pil_curr.height * 2), Image.Resampling.NEAREST)
        tk_curr = ImageTk.PhotoImage(pil_curr)

        f2 = tk.Frame(frame)
        f2.pack(side="left", padx=20)
        tk.Label(f2, text="[현재 발견된 화면]", fg="red", font=("bold")).pack()
        lbl2 = tk.Label(f2, image=tk_curr)
        lbl2.image = tk_curr
        lbl2.pack()

    # --- 초기화 로직 ---
    def reset_app(self):
        self.stop_monitoring() 
        self.region = None
        self.ref_imgs = []
        self.is_running = False
        
        self.timer_label.config(text="초기화됨", fg="blue")
        self.btn_set_region.config(state="normal")
        self.btn_learn.config(state="disabled")
        self.btn_start.config(state="disabled", bg="green")
        
        self.log("-----------------------------")
        self.log("모든 설정이 초기화되었습니다.")
        self.log("1단계부터 다시 시작하세요.")

    # --- 스레드 관리 ---
    def start_set_region_thread(self):
        threading.Thread(target=self.logic_set_region, daemon=True).start()

    def start_learning_thread(self):
        threading.Thread(target=self.logic_learning, daemon=True).start()

    def start_monitoring(self):
        if not self.ref_imgs:
            messagebox.showerror("에러", "학습부터 완료해주세요!")
            return
        
        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_set_region.config(state="disabled")
        self.btn_learn.config(state="disabled")
        self.btn_reset.config(state="disabled") 
        threading.Thread(target=self.logic_monitoring, daemon=True).start()

    def stop_monitoring(self):
        self.is_running = False
        self.log("중단 요청됨/완료.")
        self.timer_label.config(text="중단됨", fg="red")
        self.btn_start.config(state="normal")
        self.btn_set_region.config(state="normal")
        self.btn_learn.config(state="normal")
        self.btn_reset.config(state="normal", bg="lightblue")

    def update_timer(self):
        if self.is_running and self.start_time:
            elapsed = time.time() - self.start_time
            timer_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            self.timer_label.config(text=timer_str, fg="green")
            self.root.after(100, self.update_timer)

    # --- 로직 ---
    def logic_set_region(self):
        self.log("--- 영역 설정 ---")
        self.log("좌상단에 마우스 -> 'F2'")
        keyboard.wait('f2')
        x1, y1 = pyautogui.position()
        self.log(f"좌상단: {x1}, {y1}")
        time.sleep(0.5)

        self.log("우하단에 마우스 -> 'F2'")
        keyboard.wait('f2')
        x2, y2 = pyautogui.position()
        self.log(f"우하단: {x2}, {y2}")
        
        self.region = (x1, y1, x2 - x1, y2 - y1)
        self.log("설정 완료. [2. 학습 시작] 가능")
        self.btn_learn.config(state="normal")

    def logic_learning(self):
        if not self.region:
            self.log("오류: 영역 설정부터 하세요.")
            return

        self.log("--- 학습 모드 ---")
        self.ref_imgs = []
        
        for i in range(self.subject_count):
            self.log(f"[{i+1}/{self.subject_count}] 위치로 이동 후 'F2'")
            keyboard.wait('f2')
            time.sleep(0.2)
            
            img = self.capture_screen()
            if img is not None:
                self.ref_imgs.append(img)
                self.log(f"{i+1}번 저장 완료.")
            else:
                self.log("이미지 캡처 실패.")
                return
            time.sleep(0.5)

        self.log("학습 끝! 스크롤 올리고 준비되면 [3. 시작] 클릭")
        self.btn_start.config(state="normal")
        
        # ★ 학습 끝나면 저장된 이미지들 팝업으로 보여주기
        self.root.after(0, self.popup_learning_result)

    def logic_monitoring(self):
        self.log("버튼 클릭됨. 3초 뒤 시작!")
        for i in range(3, 0, -1):
            if not self.is_running: return
            self.log(f"{i}초 전... (스크롤 확인)")
            self.timer_label.config(text=f"준비 {i}...", fg="orange")
            time.sleep(1)

        if not self.is_running: return

        self.log("!!! 감시 시작 !!!")
        self.start_time = time.time()
        self.update_timer()
        
        curr_idx = 0
        direction = 1 
        
        while self.is_running:
            if keyboard.is_pressed('esc'):
                self.stop_monitoring()
                break

            try:
                curr_img = self.capture_screen()
                if curr_img is None: continue

                ref_img = self.ref_imgs[curr_idx]
                score = cv2.matchTemplate(ref_img, curr_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(score)
                
                if max_val < 0.99:
                    # ★ 발견 시 현재 이미지(curr_img)도 같이 넘김
                    self.found_empty_seat(curr_idx + 1, curr_img)
                    break
                
                if direction == 1:
                    pyautogui.press('down')
                    curr_idx += 1
                    if curr_idx == self.subject_count - 1:
                        direction = -1
                else:
                    pyautogui.press('up')
                    curr_idx -= 1
                    if curr_idx == 0:
                        direction = 1
                
                time.sleep(self.move_delay)
                
            except Exception as e:
                self.log(f"에러: {e}")
                self.stop_monitoring()
                break

    def found_empty_seat(self, idx, curr_img):
        self.stop_monitoring()
        
        # 초기화 버튼만 활성화 로직 유지
        self.btn_set_region.config(state="disabled")
        self.btn_learn.config(state="disabled")
        self.btn_start.config(state="disabled")

        self.is_running = False
        self.log(f"🔥 {idx}번째 줄 빈자리 발견! 🔥")
        self.timer_label.config(text="빈자리 발견! (초기화 필요)", fg="red")
        
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.root.focus_force()
        
        threading.Thread(target=self.play_alarm_sound, daemon=True).start()
        
        # ★ 알림창 뜨기 전에 비교 이미지 팝업 먼저 띄움
        saved_ref_img = self.ref_imgs[idx-1]
        self.root.after(0, lambda: self.popup_comparison(saved_ref_img, curr_img, idx))
        
        messagebox.showwarning("알림", f"{idx}번째 줄에 자리가 났습니다!\n확인 후 [초기화] 버튼을 눌러주세요.")
        
        self.root.attributes('-topmost', False)

    def play_alarm_sound(self):
        for _ in range(10):
            winsound.Beep(2500, 300)
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroApp(root)
    root.mainloop()