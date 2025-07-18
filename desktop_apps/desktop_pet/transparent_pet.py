#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk, ImageDraw
import os
import sys

class TransparentPet:
    def __init__(self, images_path=None):
        self.root = tk.Tk()
        self.root.title("Transparent Pet")
        
        # ウィンドウの装飾を削除（フレームレス）
        self.root.overrideredirect(True)
        
        # 常に最前面に表示
        self.root.attributes('-topmost', True)
        
        # 透過色を設定（この色が完全に透明になる）
        self.transparent_color = '#010101'  # ほぼ黒（純黒は避ける）
        
        # Windows用の透過設定
        self.root.attributes('-transparentcolor', self.transparent_color)
        
        # 初期サイズ
        self.size = 150
        self.root.geometry(f"{self.size}x{self.size}")
        
        # 画像リストとインデックス
        self.images = []
        self.photo_images = []
        self.current_index = 0
        self.animation_speed = 500
        self.is_animating = True
        
        # キャンバス作成（透過色で塗りつぶし）
        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size, 
                               bg=self.transparent_color, highlightthickness=0)
        self.canvas.pack()
        
        # 画像表示用
        self.image_label = None
        
        # ドラッグ用の変数
        self.start_x = None
        self.start_y = None
        
        # 自動移動関連
        self.auto_move = False
        self.target_x = None
        self.target_y = None
        self.move_speed = 2
        self.behavior_timer = 0
        self.current_behavior = 'idle'
        self.rest_timer = 0
        
        # デスクトップサイズ
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # 右クリックメニュー作成
        self.create_context_menu()
        
        # イベントバインド
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.canvas.bind("<Double-Button-1>", self.pet_touched)
        
        # 初期画像の読み込み
        if images_path:
            self.load_images(images_path)
        else:
            # デフォルトのキャラクター画像を作成
            self.create_default_character()
    
    def create_context_menu(self):
        """右クリックメニューの作成"""
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="画像を選択", command=self.load_images_dialog)
        self.context_menu.add_separator()
        
        # 動作モード
        self.context_menu.add_command(label="お散歩モード ON/OFF", command=self.toggle_auto_move)
        self.context_menu.add_separator()
        
        self.context_menu.add_command(label="速く", command=lambda: self.set_speed(200))
        self.context_menu.add_command(label="普通", command=lambda: self.set_speed(500))
        self.context_menu.add_command(label="遅く", command=lambda: self.set_speed(1000))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="小さく (100)", command=lambda: self.resize(100))
        self.context_menu.add_command(label="中 (150)", command=lambda: self.resize(150))
        self.context_menu.add_command(label="大きく (200)", command=lambda: self.resize(200))
        self.context_menu.add_command(label="特大 (300)", command=lambda: self.resize(300))
        self.context_menu.add_command(label="巨大 (500)", command=lambda: self.resize(500))
        self.context_menu.add_command(label="超巨大 (700)", command=lambda: self.resize(700))
        self.context_menu.add_command(label="極大 (1000)", command=lambda: self.resize(1000))
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="終了", command=self.root.quit)
    
    def show_context_menu(self, event):
        """右クリックメニューを表示"""
        self.context_menu.post(event.x_root, event.y_root)
    
    def create_default_character(self):
        """デフォルトのキャラクター画像を作成（透過付き）"""
        # 異なる表情のキャラクターを作成
        expressions = [
            {'eyes': 'open', 'mouth': 'smile'},
            {'eyes': 'closed', 'mouth': 'smile'},
            {'eyes': 'open', 'mouth': 'open'},
            {'eyes': 'wink', 'mouth': 'smile'},
            {'eyes': 'open', 'mouth': 'smile'},
        ]
        
        for expr in expressions:
            # 透明な背景の画像を作成
            img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # キャラクターの本体（円）
            body_color = '#FFD93D'  # 黄色
            margin = 30
            draw.ellipse([margin, margin, self.size-margin, self.size-margin], 
                        fill=body_color, outline='#FFA500', width=3)
            
            # 目を描画
            eye_y = self.size // 2 - 20
            eye_size = 15
            left_eye_x = self.size // 2 - 25
            right_eye_x = self.size // 2 + 10
            
            if expr['eyes'] == 'open':
                # 開いた目
                draw.ellipse([left_eye_x, eye_y, left_eye_x+eye_size, eye_y+eye_size], 
                           fill='white', outline='black', width=2)
                draw.ellipse([right_eye_x, eye_y, right_eye_x+eye_size, eye_y+eye_size], 
                           fill='white', outline='black', width=2)
                # 瞳
                draw.ellipse([left_eye_x+5, eye_y+5, left_eye_x+10, eye_y+10], fill='black')
                draw.ellipse([right_eye_x+5, eye_y+5, right_eye_x+10, eye_y+10], fill='black')
            elif expr['eyes'] == 'closed':
                # 閉じた目（線）
                draw.arc([left_eye_x, eye_y, left_eye_x+eye_size, eye_y+eye_size], 
                        0, 180, fill='black', width=3)
                draw.arc([right_eye_x, eye_y, right_eye_x+eye_size, eye_y+eye_size], 
                        0, 180, fill='black', width=3)
            elif expr['eyes'] == 'wink':
                # ウィンク
                draw.ellipse([left_eye_x, eye_y, left_eye_x+eye_size, eye_y+eye_size], 
                           fill='white', outline='black', width=2)
                draw.ellipse([left_eye_x+5, eye_y+5, left_eye_x+10, eye_y+10], fill='black')
                draw.arc([right_eye_x, eye_y, right_eye_x+eye_size, eye_y+eye_size], 
                        0, 180, fill='black', width=3)
            
            # 口を描画
            mouth_y = self.size // 2 + 10
            mouth_x = self.size // 2
            
            if expr['mouth'] == 'smile':
                # 笑顔
                draw.arc([mouth_x-20, mouth_y-10, mouth_x+20, mouth_y+20], 
                        0, 180, fill='black', width=3)
            elif expr['mouth'] == 'open':
                # 開いた口
                draw.ellipse([mouth_x-15, mouth_y, mouth_x+15, mouth_y+20], 
                           fill='#FF6B6B', outline='black', width=2)
            
            self.images.append(img)
            photo = ImageTk.PhotoImage(img)
            self.photo_images.append(photo)
        
        if self.photo_images:
            self.animate()
    
    def load_images_dialog(self):
        """画像選択ダイアログ"""
        files = filedialog.askopenfilenames(
            title="アニメーションする画像を選択（透過PNG推奨）",
            filetypes=[("PNG files", "*.png"), ("All image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if files:
            self.load_images_from_files(files)
    
    def load_images(self, directory):
        """ディレクトリから画像を読み込み"""
        if os.path.isdir(directory):
            files = []
            for file in sorted(os.listdir(directory)):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    files.append(os.path.join(directory, file))
            self.load_images_from_files(files)
        else:
            self.load_images_from_files([directory])
    
    def load_images_from_files(self, files):
        """ファイルリストから画像を読み込み"""
        self.images.clear()
        self.photo_images.clear()
        
        for file in files:
            try:
                img = Image.open(file)
                
                # GIFファイルの場合は各フレームを抽出
                if file.lower().endswith('.gif'):
                    # GIFアニメーションの各フレームを取得
                    try:
                        img.seek(0)
                        while True:
                            # 現在のフレームをコピー
                            frame = img.copy()
                            
                            # RGBA変換
                            if frame.mode != 'RGBA':
                                frame = frame.convert('RGBA')
                            
                            # リサイズとPhotoImage作成
                            frame.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
                            self.images.append(frame)
                            photo = ImageTk.PhotoImage(frame)
                            self.photo_images.append(photo)
                            
                            # 次のフレームへ
                            img.seek(img.tell() + 1)
                    except EOFError:
                        # 全フレーム読み込み完了
                        pass
                else:
                    # 通常の画像ファイル
                    # RGBA変換（透過対応）
                    if img.mode != 'RGBA':
                        # 背景を透明にする処理
                        img = img.convert('RGBA')
                        # 白い背景を透明にする（オプション）
                        datas = img.getdata()
                        newData = []
                        for item in datas:
                            # 白っぽい色を透明にする
                            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                                newData.append((255, 255, 255, 0))
                            else:
                                newData.append(item)
                        img.putdata(newData)
                    
                    # サイズ調整
                    img.thumbnail((self.size-10, self.size-10), Image.Resampling.LANCZOS)
                    
                    # 中央に配置するための新しい透明画像
                    centered_img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
                    # 画像を中央に貼り付け
                    x = (self.size - img.width) // 2
                    y = (self.size - img.height) // 2
                    centered_img.paste(img, (x, y), img)
                    
                    self.images.append(centered_img)
                    photo = ImageTk.PhotoImage(centered_img)
                    self.photo_images.append(photo)
            except Exception as e:
                print(f"画像読み込みエラー: {file} - {e}")
        
        if self.photo_images:
            self.current_index = 0
            self.animate()
    
    def animate(self):
        """アニメーション処理"""
        if not self.photo_images or not self.is_animating:
            return
            
        # 現在の画像を表示
        if self.image_label:
            self.canvas.delete(self.image_label)
        
        self.image_label = self.canvas.create_image(
            self.size//2, self.size//2, 
            image=self.photo_images[self.current_index],
            anchor=tk.CENTER
        )
        
        # 次のインデックスへ
        self.current_index = (self.current_index + 1) % len(self.photo_images)
        
        # 次のフレームをスケジュール
        self.root.after(self.animation_speed, self.animate)
    
    def pet_touched(self, event):
        """ペットをダブルクリックしたときの反応"""
        import random
        # ランダムな位置にジャンプ
        if self.auto_move:
            new_x = random.randint(50, self.screen_width - self.size - 50)
            new_y = random.randint(50, self.screen_height - self.size - 50)
            self.root.geometry(f"{self.size}x{self.size}+{new_x}+{new_y}")
    
    def toggle_auto_move(self):
        """自動移動のON/OFF"""
        self.auto_move = not self.auto_move
        if self.auto_move:
            self.start_wandering()
            print("お散歩モード: ON")
        else:
            print("お散歩モード: OFF")
    
    def start_wandering(self):
        """自動移動を開始"""
        if not self.auto_move:
            return
        
        import random
        
        # 行動タイマーを減らす
        self.behavior_timer -= 1
        
        # 新しい行動を決定
        if self.behavior_timer <= 0:
            behaviors = ['move', 'rest', 'edge_walk', 'center']
            self.current_behavior = random.choice(behaviors)
            self.behavior_timer = random.randint(30, 100)
            
            if self.current_behavior == 'move':
                # ランダムな位置に移動
                self.target_x = random.randint(50, self.screen_width - self.size - 50)
                self.target_y = random.randint(50, self.screen_height - self.size - 50)
                
            elif self.current_behavior == 'rest':
                # その場で休憩
                self.rest_timer = random.randint(20, 50)
                
            elif self.current_behavior == 'edge_walk':
                # 画面端を歩く
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                if edge == 'top':
                    self.target_x = random.randint(50, self.screen_width - self.size - 50)
                    self.target_y = 50
                elif edge == 'bottom':
                    self.target_x = random.randint(50, self.screen_width - self.size - 50)
                    self.target_y = self.screen_height - self.size - 100
                elif edge == 'left':
                    self.target_x = 50
                    self.target_y = random.randint(50, self.screen_height - self.size - 100)
                else:  # right
                    self.target_x = self.screen_width - self.size - 50
                    self.target_y = random.randint(50, self.screen_height - self.size - 100)
                    
            elif self.current_behavior == 'center':
                # 画面中央付近へ
                self.target_x = self.screen_width // 2 + random.randint(-100, 100)
                self.target_y = self.screen_height // 2 + random.randint(-100, 100)
        
        # 移動処理
        if self.target_x is not None and self.target_y is not None:
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            
            dx = self.target_x - current_x
            dy = self.target_y - current_y
            distance = (dx**2 + dy**2)**0.5
            
            if distance > self.move_speed:
                # 目標に向かって移動
                move_x = int(dx / distance * self.move_speed)
                move_y = int(dy / distance * self.move_speed)
                
                new_x = current_x + move_x
                new_y = current_y + move_y
                
                self.root.geometry(f"{self.size}x{self.size}+{new_x}+{new_y}")
            else:
                # 到着
                self.target_x = None
                self.target_y = None
        
        # 休憩中
        if self.rest_timer > 0:
            self.rest_timer -= 1
        
        # 次の更新
        self.root.after(50, self.start_wandering)
    
    def set_speed(self, speed):
        """アニメーション速度を設定"""
        self.animation_speed = speed
    
    def resize(self, new_size):
        """ウィンドウサイズを変更"""
        # サイズ制限
        new_size = max(50, min(2000, new_size))
        
        old_size = self.size
        self.size = new_size
        self.root.geometry(f"{self.size}x{self.size}")
        self.canvas.config(width=self.size, height=self.size)
        
        # 画像を再スケール
        if self.images and old_size != new_size:
            temp_images = []
            self.photo_images.clear()
            
            for img in self.images:
                # 元の画像から再スケール
                new_img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
                # スケール計算
                scale = new_size / old_size
                scaled_size = (int(img.width * scale), int(img.height * scale))
                if scaled_size[0] > 0 and scaled_size[1] > 0:
                    scaled_img = img.resize(scaled_size, Image.Resampling.LANCZOS)
                    x = (self.size - scaled_img.width) // 2
                    y = (self.size - scaled_img.height) // 2
                    new_img.paste(scaled_img, (x, y), scaled_img)
                
                temp_images.append(new_img)
                photo = ImageTk.PhotoImage(new_img)
                self.photo_images.append(photo)
            
            self.images = temp_images
    
    def start_move(self, event):
        """ドラッグ開始"""
        self.start_x = event.x_root
        self.start_y = event.y_root
    
    def do_move(self, event):
        """ドラッグ中"""
        if self.start_x is not None and self.start_y is not None:
            x = self.root.winfo_x() + (event.x_root - self.start_x)
            y = self.root.winfo_y() + (event.y_root - self.start_y)
            self.root.geometry(f"+{x}+{y}")
            self.start_x = event.x_root
            self.start_y = event.y_root
    
    def stop_move(self, event):
        """ドラッグ終了"""
        self.start_x = None
        self.start_y = None
    
    def run(self):
        """メインループ開始"""
        self.root.mainloop()

if __name__ == "__main__":
    images_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    app = TransparentPet(images_path)
    app.run()