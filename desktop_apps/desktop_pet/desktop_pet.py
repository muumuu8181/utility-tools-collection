#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk
import os
import sys

class DesktopPet:
    def __init__(self, images_path=None):
        self.root = tk.Tk()
        self.root.title("Desktop Pet")
        
        # ウィンドウの装飾を削除（フレームレス）
        self.root.overrideredirect(True)
        
        # 常に最前面に表示
        self.root.attributes('-topmost', True)
        
        # 透過設定（Windows）
        self.root.attributes('-alpha', 0.95)  # 少し透明度を設定
        
        # 初期サイズ
        self.size = 150
        self.root.geometry(f"{self.size}x{self.size}")
        
        # 画像リストとインデックス
        self.images = []
        self.photo_images = []
        self.current_index = 0
        self.animation_speed = 500  # ミリ秒
        self.is_animating = True
        
        # キャンバス作成（背景を薄いグレーに）
        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size, 
                               bg='#f0f0f0', highlightthickness=0)
        self.canvas.pack()
        
        # 画像表示用
        self.image_label = None
        
        # ドラッグ用の変数
        self.start_x = None
        self.start_y = None
        
        # 右クリックメニュー作成
        self.create_context_menu()
        
        # イベントバインド
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<Button-3>", self.show_context_menu)  # 右クリック
        self.canvas.bind("<Double-Button-1>", self.toggle_animation)  # ダブルクリック
        
        # 初期画像の読み込み
        if images_path:
            self.load_images(images_path)
        else:
            # デフォルトの簡単な画像を作成
            self.create_default_images()
    
    def create_context_menu(self):
        """右クリックメニューの作成"""
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="画像を選択", command=self.load_images_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="速く", command=lambda: self.set_speed(200))
        self.context_menu.add_command(label="普通", command=lambda: self.set_speed(500))
        self.context_menu.add_command(label="遅く", command=lambda: self.set_speed(1000))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="小さく", command=lambda: self.resize(100))
        self.context_menu.add_command(label="中", command=lambda: self.resize(150))
        self.context_menu.add_command(label="大きく", command=lambda: self.resize(200))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="終了", command=self.root.quit)
    
    def show_context_menu(self, event):
        """右クリックメニューを表示"""
        self.context_menu.post(event.x_root, event.y_root)
    
    def create_default_images(self):
        """デフォルトの画像を作成（カラフルな円）"""
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']
        for color in colors:
            img = Image.new('RGBA', (self.size, self.size), (255, 255, 255, 0))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            margin = 20
            draw.ellipse([margin, margin, self.size-margin, self.size-margin], 
                        fill=color, outline='white', width=3)
            self.images.append(img)
            photo = ImageTk.PhotoImage(img)
            self.photo_images.append(photo)
        
        if self.photo_images:
            self.animate()
    
    def load_images_dialog(self):
        """画像選択ダイアログ"""
        files = filedialog.askopenfilenames(
            title="アニメーションする画像を選択",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
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
                # RGBA変換（透過対応）
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img.thumbnail((self.size-20, self.size-20), Image.Resampling.LANCZOS)
                self.images.append(img)
                photo = ImageTk.PhotoImage(img)
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
    
    def toggle_animation(self, event):
        """アニメーションの一時停止/再開"""
        self.is_animating = not self.is_animating
        if self.is_animating:
            self.animate()
    
    def set_speed(self, speed):
        """アニメーション速度を設定"""
        self.animation_speed = speed
    
    def resize(self, new_size):
        """ウィンドウサイズを変更"""
        self.size = new_size
        self.root.geometry(f"{self.size}x{self.size}")
        self.canvas.config(width=self.size, height=self.size)
        
        # 画像を再読み込み
        if self.images:
            temp_images = self.images.copy()
            self.images.clear()
            self.photo_images.clear()
            
            for img in temp_images:
                img_copy = img.copy()
                img_copy.thumbnail((self.size-20, self.size-20), Image.Resampling.LANCZOS)
                self.images.append(img_copy)
                photo = ImageTk.PhotoImage(img_copy)
                self.photo_images.append(photo)
    
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
    
    app = DesktopPet(images_path)
    app.run()