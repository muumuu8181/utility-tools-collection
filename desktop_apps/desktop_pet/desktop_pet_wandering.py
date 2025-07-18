#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk, ImageDraw
import os
import sys
import random
import math
import time
import win32gui
import win32con
import win32api

class WanderingPet:
    def __init__(self, images_path=None):
        self.root = tk.Tk()
        self.root.title("Wandering Pet")
        
        # ウィンドウの装飾を削除（フレームレス）
        self.root.overrideredirect(True)
        
        # 常に最前面に表示
        self.root.attributes('-topmost', True)
        
        # 透過色を設定
        self.transparent_color = '#010101'
        self.root.attributes('-transparentcolor', self.transparent_color)
        
        # 初期サイズと位置
        self.size = 100
        self.x = 100
        self.y = 100
        self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")
        
        # 画像リスト
        self.images = {
            'walk_right': [],
            'walk_left': [],
            'idle': [],
            'sleep': [],
            'sit': []
        }
        self.current_state = 'idle'
        self.current_index = 0
        self.animation_speed = 200
        
        # 移動関連
        self.is_moving = False
        self.target_x = self.x
        self.target_y = self.y
        self.move_speed = 2
        self.direction = 'right'
        
        # 行動状態
        self.behavior_timer = 0
        self.current_behavior = 'idle'
        self.resting_on = None  # 休憩中のウィンドウ
        
        # デスクトップとウィンドウ情報
        self.desktop_width = self.root.winfo_screenwidth()
        self.desktop_height = self.root.winfo_screenheight()
        self.windows = []
        self.update_windows()
        
        # キャンバス作成
        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size, 
                               bg=self.transparent_color, highlightthickness=0)
        self.canvas.pack()
        
        # 画像表示用
        self.image_label = None
        
        # ドラッグ用
        self.start_x = None
        self.start_y = None
        self.is_dragging = False
        
        # 右クリックメニュー
        self.create_context_menu()
        
        # イベントバインド
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.canvas.bind("<Double-Button-1>", self.pet_interact)
        
        # 初期画像作成
        self.create_default_animations()
        
        # 行動開始
        self.update_behavior()
        self.animate()
        self.move()
    
    def create_context_menu(self):
        """右クリックメニュー"""
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="画像を選択", command=self.load_images_dialog)
        self.context_menu.add_separator()
        
        # 行動モード
        behavior_menu = Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="行動モード", menu=behavior_menu)
        behavior_menu.add_command(label="自由に歩き回る", command=lambda: self.set_behavior('wander'))
        behavior_menu.add_command(label="ウィンドウで休憩", command=lambda: self.set_behavior('rest'))
        behavior_menu.add_command(label="追いかけっこ", command=lambda: self.set_behavior('follow'))
        behavior_menu.add_command(label="おとなしく", command=lambda: self.set_behavior('idle'))
        
        self.context_menu.add_separator()
        
        # サイズ変更
        self.context_menu.add_command(label="小さく (50)", command=lambda: self.resize(50))
        self.context_menu.add_command(label="普通 (100)", command=lambda: self.resize(100))
        self.context_menu.add_command(label="大きく (150)", command=lambda: self.resize(150))
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="終了", command=self.root.quit)
    
    def create_default_animations(self):
        """デフォルトのアニメーション作成"""
        # 歩行アニメーション（右向き）
        for i in range(4):
            img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 体
            body_x = self.size // 2 + (i % 2) * 5
            draw.ellipse([body_x-20, 30, body_x+20, 70], fill='#FFD93D', outline='#FFA500', width=2)
            
            # 頭
            draw.ellipse([body_x-15, 20, body_x+15, 50], fill='#FFD93D', outline='#FFA500', width=2)
            
            # 目（右向き）
            draw.ellipse([body_x+2, 30, body_x+8, 36], fill='white', outline='black')
            draw.ellipse([body_x+4, 32, body_x+6, 34], fill='black')
            
            # 足（歩行アニメーション）
            leg_offset = (i % 2) * 10 - 5
            draw.ellipse([body_x-10+leg_offset, 65, body_x-5+leg_offset, 75], fill='#FFA500')
            draw.ellipse([body_x+5-leg_offset, 65, body_x+10-leg_offset, 75], fill='#FFA500')
            
            self.images['walk_right'].append(ImageTk.PhotoImage(img))
            
            # 左向きは反転
            img_left = img.transpose(Image.FLIP_LEFT_RIGHT)
            self.images['walk_left'].append(ImageTk.PhotoImage(img_left))
        
        # アイドル状態
        for i in range(2):
            img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 体
            draw.ellipse([30, 30, 70, 70], fill='#FFD93D', outline='#FFA500', width=2)
            
            # 頭
            draw.ellipse([35, 20, 65, 50], fill='#FFD93D', outline='#FFA500', width=2)
            
            # 目（瞬き）
            if i == 0:
                draw.ellipse([42, 30, 48, 36], fill='white', outline='black')
                draw.ellipse([52, 30, 58, 36], fill='white', outline='black')
                draw.ellipse([44, 32, 46, 34], fill='black')
                draw.ellipse([54, 32, 56, 34], fill='black')
            else:
                draw.line([42, 33, 48, 33], fill='black', width=2)
                draw.line([52, 33, 58, 33], fill='black', width=2)
            
            self.images['idle'].append(ImageTk.PhotoImage(img))
        
        # 睡眠状態
        img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 横たわった体
        draw.ellipse([20, 40, 80, 60], fill='#FFD93D', outline='#FFA500', width=2)
        
        # 頭
        draw.ellipse([15, 35, 40, 55], fill='#FFD93D', outline='#FFA500', width=2)
        
        # 閉じた目
        draw.arc([22, 42, 28, 48], 0, 180, fill='black', width=2)
        draw.arc([30, 42, 36, 48], 0, 180, fill='black', width=2)
        
        # Zzz
        draw.text((45, 30), "Zzz", fill='blue')
        
        self.images['sleep'].append(ImageTk.PhotoImage(img))
        
        # 座り状態
        img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 座った体
        draw.ellipse([30, 40, 70, 75], fill='#FFD93D', outline='#FFA500', width=2)
        
        # 頭
        draw.ellipse([35, 25, 65, 55], fill='#FFD93D', outline='#FFA500', width=2)
        
        # 目
        draw.ellipse([42, 35, 48, 41], fill='white', outline='black')
        draw.ellipse([52, 35, 58, 41], fill='white', outline='black')
        draw.ellipse([44, 37, 46, 39], fill='black')
        draw.ellipse([54, 37, 56, 39], fill='black')
        
        self.images['sit'].append(ImageTk.PhotoImage(img))
    
    def update_windows(self):
        """開いているウィンドウの情報を取得"""
        def enum_window_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                if rect[2] - rect[0] > 100 and rect[3] - rect[1] > 100:  # 小さすぎるウィンドウは除外
                    windows.append({
                        'hwnd': hwnd,
                        'title': win32gui.GetWindowText(hwnd),
                        'rect': rect  # (left, top, right, bottom)
                    })
            return True
        
        self.windows = []
        win32gui.EnumWindows(enum_window_callback, self.windows)
    
    def find_nearest_window(self):
        """最も近いウィンドウを探す"""
        self.update_windows()
        
        pet_center_x = self.x + self.size // 2
        pet_center_y = self.y + self.size // 2
        
        nearest = None
        min_distance = float('inf')
        
        for window in self.windows:
            rect = window['rect']
            # ウィンドウの上端の中心
            window_x = (rect[0] + rect[2]) // 2
            window_y = rect[1]
            
            distance = math.sqrt((window_x - pet_center_x)**2 + (window_y - pet_center_y)**2)
            
            if distance < min_distance and rect[1] > 50:  # タスクバーなどを除外
                min_distance = distance
                nearest = window
        
        return nearest
    
    def update_behavior(self):
        """行動パターンを更新"""
        self.behavior_timer -= 1
        
        if self.behavior_timer <= 0:
            # 新しい行動を決定
            behaviors = ['wander', 'rest', 'idle', 'follow_mouse']
            weights = [40, 30, 20, 10]  # 各行動の確率
            
            self.current_behavior = random.choices(behaviors, weights=weights)[0]
            self.behavior_timer = random.randint(50, 200)  # 行動の継続時間
            
            if self.current_behavior == 'wander':
                # ランダムな位置に移動
                self.target_x = random.randint(0, self.desktop_width - self.size)
                self.target_y = random.randint(0, self.desktop_height - self.size)
                self.is_moving = True
                
            elif self.current_behavior == 'rest':
                # 最寄りのウィンドウを探す
                window = self.find_nearest_window()
                if window:
                    rect = window['rect']
                    # ウィンドウの上端に移動
                    self.target_x = random.randint(rect[0], max(rect[0], rect[2] - self.size))
                    self.target_y = rect[1] - self.size + 20  # 少し重なるように
                    self.is_moving = True
                    self.resting_on = window['title']
                
            elif self.current_behavior == 'follow_mouse':
                # マウスカーソルの位置を取得
                cursor_x, cursor_y = win32api.GetCursorPos()
                self.target_x = cursor_x - self.size // 2
                self.target_y = cursor_y - self.size // 2
                self.is_moving = True
        
        # 定期的に行動を更新
        self.root.after(100, self.update_behavior)
    
    def move(self):
        """移動処理"""
        if self.is_moving and not self.is_dragging:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > self.move_speed:
                # 目標に向かって移動
                self.x += int(dx / distance * self.move_speed)
                self.y += int(dy / distance * self.move_speed)
                
                # 向きを更新
                if dx > 0:
                    self.direction = 'right'
                    self.current_state = 'walk_right'
                else:
                    self.direction = 'left'
                    self.current_state = 'walk_left'
                
                # ウィンドウ位置を更新
                self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")
            else:
                # 到着
                self.is_moving = False
                
                # 状態を更新
                if self.current_behavior == 'rest' and self.resting_on:
                    self.current_state = random.choice(['sleep', 'sit'])
                else:
                    self.current_state = 'idle'
        
        # 継続的に移動をチェック
        self.root.after(50, self.move)
    
    def animate(self):
        """アニメーション処理"""
        if self.current_state in self.images and self.images[self.current_state]:
            frames = self.images[self.current_state]
            
            if self.image_label:
                self.canvas.delete(self.image_label)
            
            self.image_label = self.canvas.create_image(
                self.size // 2, self.size // 2,
                image=frames[self.current_index % len(frames)],
                anchor=tk.CENTER
            )
            
            self.current_index += 1
        
        # アニメーション速度に応じて次のフレーム
        speed = self.animation_speed if not self.is_moving else 100
        self.root.after(speed, self.animate)
    
    def start_drag(self, event):
        """ドラッグ開始"""
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.is_dragging = True
        self.is_moving = False
        self.current_behavior = 'idle'
        self.behavior_timer = 50
    
    def do_drag(self, event):
        """ドラッグ中"""
        if self.is_dragging:
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y
            self.x = self.root.winfo_x() + dx
            self.y = self.root.winfo_y() + dy
            self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")
            self.start_x = event.x_root
            self.start_y = event.y_root
    
    def stop_drag(self, event):
        """ドラッグ終了"""
        self.is_dragging = False
        self.current_state = 'idle'
    
    def pet_interact(self, event):
        """ペットをダブルクリックしたときの反応"""
        reactions = ['idle', 'sit', 'sleep']
        self.current_state = random.choice(reactions)
        self.is_moving = False
        self.behavior_timer = 30
    
    def show_context_menu(self, event):
        """右クリックメニュー表示"""
        self.context_menu.post(event.x_root, event.y_root)
    
    def set_behavior(self, behavior):
        """行動モードを設定"""
        self.current_behavior = behavior
        self.behavior_timer = 0  # すぐに新しい行動を開始
    
    def resize(self, new_size):
        """サイズ変更"""
        self.size = new_size
        self.root.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")
        self.canvas.config(width=self.size, height=self.size)
        # 画像を再作成
        self.images = {
            'walk_right': [],
            'walk_left': [],
            'idle': [],
            'sleep': [],
            'sit': []
        }
        self.create_default_animations()
    
    def load_images_dialog(self):
        """画像選択ダイアログ"""
        # ここに画像読み込み処理を実装
        pass
    
    def run(self):
        """メインループ"""
        self.root.mainloop()

if __name__ == "__main__":
    # win32guiがない場合の簡易版
    try:
        import win32gui
        import win32con
        import win32api
        app = WanderingPet()
        app.run()
    except ImportError:
        print("このバージョンはWindows専用です。")
        print("必要なパッケージをインストールしてください:")
        print("pip install pywin32")
        print("\nまたは、transparent_pet.pyを使用してください。")