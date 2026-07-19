import tkinter as tk
from tkinter import colorchooser
import math
import random
import threading
import json
import urllib.request
import urllib.error
import multiprocessing

class DesktopPet:
    """Клас, що відповідає за фігуру, яка бігає та думає за допомогою AI"""
    def __init__(self, root, items_data, width, height, start_x, start_y, api_key=""):
        self.top = root  
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.title("Desktop Pet")
        
        transparent_color = "#abcdef"
        try:
            self.top.attributes("-transparentcolor", transparent_color)
        except tk.TclError:
            pass 
            
        self.top.config(bg=transparent_color)
        
        self.screen_w = self.top.winfo_screenwidth()
        self.screen_h = self.top.winfo_screenheight()
        self.api_key = api_key
        
        self.bubble_space = 80
        padding = 10
        
        self.w = width + padding * 2
        self.h = height + padding * 2 + self.bubble_space
        
        self.x = start_x - padding
        self.base_y = self.screen_h - (height + padding * 2) - 40 
        
        self.canvas = tk.Canvas(self.top, width=self.w, height=self.h, 
                                bg=transparent_color, highlightthickness=0)
        self.canvas.pack()
        
        for itype, coords, fill, outline, w in items_data:
            shifted_coords = [c + padding if i % 2 == 0 else c + padding + self.bubble_space for i, c in enumerate(coords)]
            
            if itype == "line":
                self.canvas.create_line(*shifted_coords, fill=fill, width=w, capstyle=tk.ROUND, smooth=True)
            elif itype == "oval":
                self.canvas.create_oval(*shifted_coords, fill=fill, outline=outline, width=w)
            elif itype == "rectangle":
                self.canvas.create_rectangle(*shifted_coords, fill=fill, outline=outline, width=w)
            elif itype == "polygon":
                self.canvas.create_polygon(*shifted_coords, fill=fill, outline=outline, width=w)
        
        speeds = [-6, -5, -4, 4, 5, 6]
        self.dx = random.choice(speeds)
        self.step_counter = 0 
        
        self.bubble_bg = None
        self.bubble_text = None
        
        # Таймери для контролю думок, щоб вони не накладалися
        self.thought_timer = None
        self.clear_timer = None
        
        self.fallback_phrases = [
            "Ого, який великий курсор!",
            "Не клікай на мене!",
            "Де тут вихід?",
            "Я просто йду...",
            "Тут прохолодно.",
            "Скільки в тебе вікон відкрито?"
        ]
        
        # Лівий клік — знищити, Правий клік — написати йому повідомлення
        self.canvas.bind("<Button-1>", lambda e: self.top.destroy())
        self.canvas.bind("<Button-3>", self.open_chat_window)
        
        self.animate()
        self.schedule_thought()

    def animate(self):
        if not self.top.winfo_exists():
            return
            
        self.x += self.dx
        self.step_counter += 1
        
        if self.x <= 0:
            self.dx *= -1
            self.x = 0
        elif self.x + self.w >= self.screen_w:
            self.dx *= -1
            self.x = self.screen_w - self.w
            
        bounce_offset = abs(math.sin(self.step_counter * 0.4)) * 15
        current_y = self.base_y - self.bubble_space - bounce_offset
            
        self.top.geometry(f"{int(self.w)}x{int(self.h)}+{int(self.x)}+{int(current_y)}")
        self.top.after(25, self.animate)

    def open_chat_window(self, event=None):
        """Відкриває вікно для введення повідомлення чоловічку"""
        if hasattr(self, 'chat_win') and self.chat_win.winfo_exists():
            self.chat_win.focus()
            return
            
        self.chat_win = tk.Toplevel(self.top)
        self.chat_win.title("Розмова")
        self.chat_win.geometry("300x100")
        self.chat_win.attributes("-topmost", True)
        self.chat_win.resizable(False, False)
        
        # Позиціонуємо вікно чату поруч із чоловічком
        win_x = int(self.x) + 50
        win_y = int(self.base_y) - 100
        self.chat_win.geometry(f"+{win_x}+{win_y}")
        
        tk.Label(self.chat_win, text="Що скажеш улюбленцю?", font=("Arial", 10)).pack(pady=5)
        
        self.chat_entry = tk.Entry(self.chat_win, width=35)
        self.chat_entry.pack(pady=5)
        self.chat_entry.focus()
        
        self.chat_win.bind("<Return>", lambda e: self.send_reply())
        tk.Button(self.chat_win, text="Сказати", command=self.send_reply).pack()

    def send_reply(self):
        """Зчитує повідомлення і відправляє на генерацію відповіді"""
        text = self.chat_entry.get().strip()
        if text:
            self.chat_win.destroy()
            self.generate_thought(text)

    def schedule_thought(self):
        if not self.top.winfo_exists():
            return
        if self.thought_timer:
            self.top.after_cancel(self.thought_timer)
            
        delay = random.randint(10000, 20000)
        self.thought_timer = self.top.after(delay, self.generate_thought)

    def generate_thought(self, user_text=None):
        if self.thought_timer:
            self.top.after_cancel(self.thought_timer)
            
        threading.Thread(target=self._ai_thought_thread, args=(user_text,), daemon=True).start()

    def _ai_thought_thread(self, user_text):
        thought = random.choice(self.fallback_phrases)
        
        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                
                # Якщо є повідомлення від користувача — міняємо контекст для ШІ
                if user_text:
                    prompt = f"Ти - маленький намальований чоловічок. Користувач щойно сказав тобі: '{user_text}'. Відповідай йому дуже коротко і кумедно (максимум 5 слів) українською."
                else:
                    prompt = "Ти - маленький намальований чоловічок, що бігає по екрану комп'ютера. Скажи одну дуже коротку, кумедну фразу (максимум 5 слів) українською про своє життя."
                
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 20, "temperature": 0.9}
                }
                
                req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
                response = urllib.request.urlopen(req, timeout=5)
                res_data = json.loads(response.read().decode('utf-8'))
                
                ai_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                thought = ai_text.replace('"', '').replace("'", "")
                
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    thought = "Недійсний API ключ!"
                elif e.code == 403:
                    thought = "Немає доступу до API!"
                else:
                    thought = f"Помилка API: {e.code}"
            except Exception as e:
                print("Помилка AI:", e)
                thought = "Немає зв'язку з ШІ!"
                
        self.top.after(0, lambda: self.show_thought(thought))

    def show_thought(self, text):
        if not self.top.winfo_exists():
            return
            
        self.clear_thought()
        
        self.bubble_text = self.canvas.create_text(
            self.w / 2, self.bubble_space / 2, 
            text=text, font=("Arial", 10, "bold"), 
            justify=tk.CENTER, width=self.w - 10, fill="black"
        )
        
        bbox = self.canvas.bbox(self.bubble_text)
        
        self.bubble_bg = self.canvas.create_rectangle(
            bbox[0]-8, bbox[1]-8, bbox[2]+8, bbox[3]+8, 
            fill="white", outline="#333", width=2, rx=10 if hasattr(self.canvas, 'create_rounded_rect') else 0
        )
        
        self.canvas.tag_lower(self.bubble_bg, self.bubble_text)
        
        if self.clear_timer:
            self.top.after_cancel(self.clear_timer)
            
        # Даємо 5 секунд на те, щоб прочитати відповідь
        self.clear_timer = self.top.after(5000, self.clear_thought)
        self.schedule_thought()

    def clear_thought(self):
        if self.bubble_bg:
            self.canvas.delete(self.bubble_bg)
        if self.bubble_text:
            self.canvas.delete(self.bubble_text)
        self.bubble_bg = None
        self.bubble_text = None


def run_pet_process(items_data, width, height, start_x, start_y, api_key):
    pet_root = tk.Tk()
    pet = DesktopPet(pet_root, items_data, width, height, start_x, start_y, api_key)
    pet_root.mainloop()


class PaintingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ШІ-Малювалка (Розумний улюбленець на робочий стіл)")
        self.root.geometry("1100x800")
        self.root.configure(bg="#f0f0f0")

        self.current_tool = "brush"
        self.current_color = "black"
        self.brush_size = 5
        self.start_x = None
        self.start_y = None
        self.temp_shape_id = None
        self.drawing = False
        
        self.history = []
        self.shape_count = 0        
        self.selected_tags = set()  
        self.selection_rect = None  
        self.drag_selection_rect = None 
        self.drag_selecting = False     
        self.dragging_items = False     
        
        self.canvas_w = 1500
        self.canvas_h = 1000
        self.popup_visible = False  
        
        self.api_key_var = tk.StringVar() 

        self.setup_ui()
        self.setup_canvas()
        self.setup_context_menu()
        
        self.root.bind("<Control-z>", self.undo)

    def setup_ui(self):
        top_toolbar = tk.Frame(self.root, bg="#f0f0f0", bd=1, relief="raised")
        top_toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_brush = tk.Button(top_toolbar, text="🖌 Пензель", bg="#e0e0e0", relief="sunken", command=lambda: self.set_tool("brush"))
        self.btn_brush.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.btn_select = tk.Button(top_toolbar, text="🖱 Виділення", bg="#f0f0f0", relief="raised", command=lambda: self.set_tool("select"))
        self.btn_select.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(top_toolbar, text="🎨 Колір", bg="#f0f0f0", command=self.change_color).pack(side=tk.LEFT, padx=5, pady=5)

        self.setup_base_colors(top_toolbar)

        tk.Button(top_toolbar, text="-", width=2, command=lambda: self.change_brush_size(-2)).pack(side=tk.LEFT, padx=2)
        self.lbl_thickness = tk.Label(top_toolbar, text=f"Товщина: {self.brush_size}", bg="#f0f0f0", width=11)
        self.lbl_thickness.pack(side=tk.LEFT, padx=2)
        tk.Button(top_toolbar, text="+", width=2, command=lambda: self.change_brush_size(2)).pack(side=tk.LEFT, padx=2)

        self.btn_toggle_figures = tk.Button(top_toolbar, text="📐 Фігури ▼", bg="#f0f0f0", command=self.toggle_figures_popup)
        self.btn_toggle_figures.pack(side=tk.LEFT, padx=10)

        tk.Label(top_toolbar, text="|", bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        
        tk.Button(top_toolbar, text="↩️ Скасувати", bg="#f0f0f0", command=self.undo).pack(side=tk.LEFT, padx=5)
        tk.Button(top_toolbar, text="🗑 Очистити", bg="#f0f0f0", command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

        self.btn_settings = tk.Button(top_toolbar, text="⚙️ Налаштування", bg="#f0f0f0", command=self.open_settings)
        self.btn_settings.pack(side=tk.RIGHT, padx=10, pady=5)

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Налаштування")
        settings_win.geometry("450x150")
        settings_win.configure(bg="#f0f0f0")
        settings_win.resizable(False, False)
        
        settings_win.transient(self.root)
        settings_win.grab_set()

        tk.Label(settings_win, text="Введіть або вставте ваш Gemini API Key:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        input_frame = tk.Frame(settings_win, bg="#f0f0f0")
        input_frame.pack(fill=tk.X, padx=20, pady=5)
        
        entry_api = tk.Entry(input_frame, textvariable=self.api_key_var, width=40, show="*")
        entry_api.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        def paste_from_clipboard():
            try:
                text = settings_win.clipboard_get()
                self.api_key_var.set(text)
            except tk.TclError:
                pass 

        btn_paste = tk.Button(input_frame, text="📋 Вставити", command=paste_from_clipboard)
        btn_paste.pack(side=tk.RIGHT, padx=(5, 0))

        tk.Button(settings_win, text="Зберегти", width=15, command=settings_win.destroy).pack(pady=15)

    def setup_base_colors(self, toolbar):
        frame = tk.Frame(toolbar, bg="#f0f0f0")
        frame.pack(side=tk.LEFT, padx=5)
        
        base_colors = ["black", "gray", "white", "red", "orange", "yellow", "green", "blue", "purple"]
        for color in base_colors:
            tk.Button(frame, bg=color, width=2, height=1, relief="flat",
                      command=lambda c=color: self.set_base_color(c)).pack(side=tk.LEFT, padx=1)

    def set_base_color(self, color):
        self.current_color = color

    def change_color(self):
        color = colorchooser.askcolor(color=self.current_color)[1]
        if color:
            self.current_color = color

    def change_brush_size(self, delta):
        self.brush_size = max(1, self.brush_size + delta)
        self.lbl_thickness.config(text=f"Товщина: {self.brush_size}")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.shape_count = 0
        self.history.clear()
        self.clear_selection()

    def undo(self, event=None):
        if self.history:
            last_tag = self.history.pop()
            self.canvas.delete(last_tag)
            if last_tag in self.selected_tags:
                self.selected_tags.remove(last_tag)
                self.update_selection_box()

    def setup_popups(self):
        self.popup_frame = tk.Frame(self.root, bg="#e0e0e0", bd=2, relief="raised")
        tk.Button(self.popup_frame, text="📏 Лінія", width=10, bg="#f0f0f0", command=lambda: self.set_tool("line")).grid(row=0, column=0, padx=2, pady=2)
        tk.Button(self.popup_frame, text="⭕ Коло", width=10, bg="#f0f0f0", command=lambda: self.set_tool("oval")).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(self.popup_frame, text="▭ Прямокут.", width=10, bg="#f0f0f0", command=lambda: self.set_tool("rect")).grid(row=0, column=2, padx=2, pady=2)
        tk.Button(self.popup_frame, text="△ Трикутник", width=10, bg="#f0f0f0", command=lambda: self.set_tool("triangle")).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(self.popup_frame, text="☆ Зірка", width=10, bg="#f0f0f0", command=lambda: self.set_tool("star")).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(self.popup_frame, text="⬡ Багатокут.", width=10, bg="#f0f0f0", command=lambda: self.set_tool("poly")).grid(row=1, column=2, padx=2, pady=2)

    def toggle_figures_popup(self):
        self.popup_visible = not self.popup_visible
        if self.popup_visible:
            self.root.update_idletasks() 
            x = self.btn_toggle_figures.winfo_rootx() - self.root.winfo_rootx()
            y = self.btn_toggle_figures.winfo_rooty() - self.root.winfo_rooty() + self.btn_toggle_figures.winfo_height()
            self.popup_frame.place(x=x, y=y)
        else:
            self.popup_frame.place_forget()

    def set_tool(self, tool):
        self.current_tool = tool
        self.btn_brush.config(relief="raised", bg="#f0f0f0")
        self.btn_select.config(relief="raised", bg="#f0f0f0")
        
        if tool == "brush":
            self.btn_brush.config(relief="sunken", bg="#e0e0e0")
        elif tool == "select":
            self.btn_select.config(relief="sunken", bg="#e0e0e0")
            
        if tool != "select":
            self.clear_selection()
            
        if tool not in ["brush", "select"] and self.popup_visible:
            self.toggle_figures_popup()

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🧠 Дати життя (Пустити на екран з ШІ)", command=self.give_life)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑 Видалити виділене", command=self.delete_selected)
        self.context_menu.add_command(label="⬆️ На передній план", command=self.bring_to_front)
        self.context_menu.add_command(label="⬇️ На задній план", command=self.send_to_back)

    def give_life(self):
        if not self.selected_tags: return
        
        bboxes = [self.canvas.bbox(tag) for tag in self.selected_tags]
        valid_bboxes = [b for b in bboxes if b is not None]
        if not valid_bboxes: return
        
        min_x = min(b[0] for b in valid_bboxes)
        min_y = min(b[1] for b in valid_bboxes)
        max_x = max(b[2] for b in valid_bboxes)
        max_y = max(b[3] for b in valid_bboxes)
        
        scale = 0.5
        w = (max_x - min_x) * scale
        h = (max_y - min_y) * scale
        
        items_data = []
        for tag in self.selected_tags:
            for item in self.canvas.find_withtag(tag):
                itype = self.canvas.type(item)
                coords = self.canvas.coords(item)
                
                shifted_coords = [(c - min_x) * scale if i % 2 == 0 else (c - min_y) * scale for i, c in enumerate(coords)]
                
                fill = self.canvas.itemcget(item, "fill")
                outline = ""
                try: outline = self.canvas.itemcget(item, "outline")
                except: pass
                
                width = 1
                try: 
                    width = max(1, float(self.canvas.itemcget(item, "width")) * scale)
                except: pass
                
                items_data.append((itype, shifted_coords, fill, outline, width))
                
        screen_x = self.canvas.winfo_rootx() + (min_x - self.canvas.canvasx(0))
        screen_y = self.canvas.winfo_rooty() + (min_y - self.canvas.canvasy(0))
        
        api_key = self.api_key_var.get().strip()
        
        p = multiprocessing.Process(
            target=run_pet_process, 
            args=(items_data, w, h, screen_x, screen_y, api_key)
        )
        p.start()
        
        self.delete_selected()

    def get_shape_tag(self, item_id):
        tags = self.canvas.gettags(item_id)
        for t in tags:
            if t.startswith("shape_"):
                return t
        return None

    def clear_selection(self):
        self.selected_tags.clear()
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

    def update_selection_box(self):
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
            
        if not self.selected_tags: return
        
        bboxes = [self.canvas.bbox(tag) for tag in self.selected_tags]
        valid_bboxes = [b for b in bboxes if b is not None]
        
        if valid_bboxes:
            min_x = min(b[0] for b in valid_bboxes)
            min_y = min(b[1] for b in valid_bboxes)
            max_x = max(b[2] for b in valid_bboxes)
            max_y = max(b[3] for b in valid_bboxes)
            
            self.selection_rect = self.canvas.create_rectangle(
                min_x-5, min_y-5, max_x+5, max_y+5,
                dash=(4, 4), outline="#0078D7", width=2, tags="system_ui"
            )

    def delete_selected(self):
        for tag in self.selected_tags:
            self.canvas.delete(tag)
        self.clear_selection()

    def bring_to_front(self):
        for tag in self.selected_tags:
            self.canvas.tag_raise(tag)
        self.update_selection_box()

    def send_to_back(self):
        for tag in self.selected_tags:
            self.canvas.tag_lower(tag)
        self.update_selection_box()

    def setup_canvas(self):
        canvas_container = tk.Frame(self.root)
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vbar = tk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar = tk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(canvas_container, bg="white", cursor="crosshair",
                                width=self.canvas_w, height=self.canvas_h,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set,
                                scrollregion=(0, 0, self.canvas_w, self.canvas_h))
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vbar.config(command=self.canvas.yview)
        hbar.config(command=self.canvas.xview)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)       
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)       
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)        
        self.canvas.bind("<Button-3>", self.on_right_click)        
        
        self.setup_popups()

    def get_item_under_cursor(self, cx, cy):
        items = self.canvas.find_overlapping(cx-5, cy-5, cx+5, cy+5)
        valid_items = [item for item in items if "system_ui" not in self.canvas.gettags(item)]
        if valid_items:
            return self.get_shape_tag(valid_items[-1])
        return None

    def on_right_click(self, event):
        if self.current_tool == "select":
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            
            tag = self.get_item_under_cursor(cx, cy)
            if tag:
                if tag not in self.selected_tags:
                    self.selected_tags = {tag}
                self.update_selection_box()
                self.context_menu.tk_popup(event.x_root, event.y_root)

    def on_canvas_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        if self.current_tool == "select":
            tag = self.get_item_under_cursor(cx, cy)
            
            if tag:
                if tag not in self.selected_tags:
                    self.selected_tags = {tag}
                self.update_selection_box()
                self.start_x, self.start_y = cx, cy
                self.dragging_items = True 
            else:
                self.clear_selection()
                self.start_x, self.start_y = cx, cy
                self.drag_selecting = True
            return
            
        self.clear_selection()
        self.drawing = True
        self.shape_count += 1
        self.current_tag = f"shape_{self.shape_count}"
        self.start_x, self.start_y = cx, cy
        
        if self.current_tool == "brush":
            self.canvas.create_oval(self.start_x - self.brush_size/2, self.start_y - self.brush_size/2,
                                  self.start_x + self.brush_size/2, self.start_y + self.brush_size/2,
                                  fill=self.current_color, outline=self.current_color, tags=(self.current_tag,))

    def on_canvas_drag(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        shift_held = event.state & 0x0001
        
        if self.current_tool == "select":
            if self.dragging_items and self.selected_tags:
                dx = cx - self.start_x
                dy = cy - self.start_y
                for tag in self.selected_tags:
                    self.canvas.move(tag, dx, dy)
                self.update_selection_box()
                self.start_x, self.start_y = cx, cy
            elif self.drag_selecting:
                if self.drag_selection_rect:
                    self.canvas.delete(self.drag_selection_rect)
                self.drag_selection_rect = self.canvas.create_rectangle(
                    self.start_x, self.start_y, cx, cy,
                    outline="#0078D7", dash=(2, 2), tags="system_ui"
                )
            return

        if not self.drawing: return

        x0, y0 = self.start_x, self.start_y
        
        if shift_held:
            if self.current_tool == "line":
                dx, dy = cx - x0, cy - y0
                angle = math.atan2(dy, dx)
                snapped_angle = round(angle / (math.pi / 4)) * (math.pi / 4)
                r = math.hypot(dx, dy)
                cx = x0 + r * math.cos(snapped_angle)
                cy = y0 + r * math.sin(snapped_angle)
            elif self.current_tool in ["oval", "rect"]:
                dx, dy = cx - x0, cy - y0
                r = max(abs(dx), abs(dy))
                cx = x0 + r * (1 if dx > 0 else -1)
                cy = y0 + r * (1 if dy > 0 else -1)

        if self.current_tool == "brush":
            self.canvas.create_line(self.start_x, self.start_y, cx, cy,
                                  width=self.brush_size, fill=self.current_color,
                                  capstyle=tk.ROUND, smooth=True, tags=(self.current_tag,))
            self.start_x, self.start_y = cx, cy

        elif self.current_tool in ["line", "oval", "rect", "triangle", "star", "poly"]:
            if self.temp_shape_id:
                self.canvas.delete(self.temp_shape_id)
            
            x1, y1 = cx, cy
            
            if self.current_tool == "line":
                self.temp_shape_id = self.canvas.create_line(x0, y0, x1, y1, width=self.brush_size, fill=self.current_color, tags=(self.current_tag,))
            elif self.current_tool == "oval":
                self.temp_shape_id = self.canvas.create_oval(x0, y0, x1, y1, outline=self.current_color, width=self.brush_size, tags=(self.current_tag,))
            elif self.current_tool == "rect":
                self.temp_shape_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline=self.current_color, width=self.brush_size, tags=(self.current_tag,))
            elif self.current_tool == "triangle":
                x_mid = (x0 + x1) / 2
                self.temp_shape_id = self.canvas.create_polygon(x_mid, y0, x1, y1, x0, y1, outline=self.current_color, width=self.brush_size, fill="", tags=(self.current_tag,))
            elif self.current_tool == "star":
                radius = max(5, math.hypot(x1-x0, y1-y0) / 2)
                cx_star, cy_star = (x0+x1)/2, (y0+y1)/2
                points = []
                for i in range(10):
                    angle = (i * 36 - 90) * math.pi / 180
                    r = radius if i % 2 == 0 else radius / 2
                    points.append(cx_star + r * math.cos(angle))
                    points.append(cy_star + r * math.sin(angle))
                self.temp_shape_id = self.canvas.create_polygon(points, outline=self.current_color, width=self.brush_size, fill="", tags=(self.current_tag,))
            elif self.current_tool == "poly":
                radius = max(5, math.hypot(x1-x0, y1-y0) / 2)
                cx_poly, cy_poly = (x0+x1)/2, (y0+y1)/2
                points = []
                for i in range(6):
                    angle = (i * 60) * math.pi / 180
                    points.append(cx_poly + radius * math.cos(angle))
                    points.append(cy_poly + radius * math.sin(angle))
                self.temp_shape_id = self.canvas.create_polygon(points, outline=self.current_color, width=self.brush_size, fill="", tags=(self.current_tag,))

    def on_canvas_release(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        
        if self.current_tool == "select":
            if self.drag_selecting:
                if self.drag_selection_rect:
                    self.canvas.delete(self.drag_selection_rect)
                    self.drag_selection_rect = None
                    
                x1, y1 = min(self.start_x, cx), min(self.start_y, cy)
                x2, y2 = max(self.start_x, cx), max(self.start_y, cy)
                
                items = self.canvas.find_overlapping(x1, y1, x2, y2)
                for item in items:
                    if "system_ui" not in self.canvas.gettags(item):
                        tag = self.get_shape_tag(item)
                        if tag:
                            self.selected_tags.add(tag)
                            
                self.update_selection_box()
                self.drag_selecting = False
                
            self.dragging_items = False
            return
            
        if self.drawing:
            self.history.append(self.current_tag)
            
        self.drawing = False
        self.temp_shape_id = None

if __name__ == "__main__":
    multiprocessing.freeze_support()  
    root = tk.Tk()
    app = PaintingApp(root)
    root.mainloop()
