#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import sys

class ImageAnimator:
    def __init__(self, images_path=None):
        self.root = tk.Tk()
        self.root.title("Image Animator")
        
        # ウィンドウの装飾を削除（フレームレス）
        self.root.overrideredirect(True)
        
        # 透過設定（Windows）
        self.root.attributes('-topmost', True)
        self.root.wm_attributes('-transparentcolor', 'white')
        
        # 画像リストとインデックス
        self.images = []
        self.photo_images = []
        self.current_index = 0
        
        # キャンバス作成
        self.canvas = tk.Canvas(self.root, width=200, height=200, bg='white', highlightthickness=0)
        self.canvas.pack()
        
        # 画像表示用のラベル
        self.image_label = None
        
        # ドラッグ用の変数
        self.start_x = None
        self.start_y = None
        
        # イベントバインド
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        self.root.bind("<q>", lambda e: self.root.quit())
        
        # 画像の読み込み
        if images_path:
            self.load_images(images_path)
        else:
            self.load_images_dialog()
        
        # アニメーション開始
        if self.images:
            self.animate()
    
    def load_images_dialog(self):
        """画像選択ダイアログ"""
        files = filedialog.askopenfilenames(
            title="アニメーションする画像を選択",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
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
            # 単一ファイルまたはワイルドカード
            self.load_images_from_files([directory])
    
    def load_images_from_files(self, files):
        """ファイルリストから画像を読み込み"""
        for file in files:
            try:
                img = Image.open(file)
                # サイズ調整（必要に応じて）
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                self.images.append(img)
                # PhotoImageに変換
                photo = ImageTk.PhotoImage(img)
                self.photo_images.append(photo)
            except Exception as e:
                print(f"画像読み込みエラー: {file} - {e}")
    
    def animate(self):
        """アニメーション処理"""
        if not self.photo_images:
            return
            
        # 現在の画像を表示
        if self.image_label:
            self.canvas.delete(self.image_label)
        
        self.image_label = self.canvas.create_image(
            100, 100, 
            image=self.photo_images[self.current_index],
            anchor=tk.CENTER
        )
        
        # 次のインデックスへ
        self.current_index = (self.current_index + 1) % len(self.photo_images)
        
        # 次のフレームをスケジュール（200ms後）
        self.root.after(200, self.animate)
    
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
    # コマンドライン引数で画像ディレクトリを指定可能
    images_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    app = ImageAnimator(images_path)
    app.run()