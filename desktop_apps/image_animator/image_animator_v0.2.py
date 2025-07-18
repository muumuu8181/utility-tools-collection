#!/usr/bin/env python3
# Image Animator v0.2
# 高品質画像リサイズ対応版
# - 元画像保持による品質劣化防止
# - 拡張サイズオプション (100px-1500px)
# - GIF完全対応

import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk, ImageDraw
import os
import sys

print("スクリプト開始")

class ImageAnimator:
    def __init__(self, images_path=None):
        print("ImageAnimator初期化開始")
        
        self.root = tk.Tk()
        self.root.title("Image Animator")
        
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
        self.original_images = []  # 元画像を保持（品質劣化防止）
        self.photo_images = []
        self.current_index = 0
        self.animation_speed = 500
        self.is_animating = True
        
        # キャンバス作成（透過色で塗りつぶし）
        self.canvas = tk.Canvas(self.root, width=self.size, height=self.size, 
                               bg=self.transparent_color, highlightthickness=0)
        self.canvas.pack()
        
        # 画像表示用のラベル
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
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.canvas.bind("<Double-Button-1>", self.toggle_animation)
        
        print("初期化完了")
        
        # 画像の読み込み
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
        self.context_menu.add_command(label="速く", command=lambda: self.set_speed(200))
        self.context_menu.add_command(label="普通", command=lambda: self.set_speed(500))
        self.context_menu.add_command(label="遅く", command=lambda: self.set_speed(1000))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="小さく", command=lambda: self.resize(100))
        self.context_menu.add_command(label="中", command=lambda: self.resize(150))
        self.context_menu.add_command(label="大きく", command=lambda: self.resize(200))
        self.context_menu.add_command(label="200%", command=lambda: self.resize(300))
        self.context_menu.add_command(label="300%", command=lambda: self.resize(450))
        self.context_menu.add_command(label="400%", command=lambda: self.resize(600))
        self.context_menu.add_command(label="500%", command=lambda: self.resize(750))
        self.context_menu.add_command(label="700%", command=lambda: self.resize(1050))
        self.context_menu.add_command(label="1000%", command=lambda: self.resize(1500))
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
        print("画像選択ダイアログを開きます")
        try:
            files = filedialog.askopenfilenames(
                title="アニメーションする画像を選択（透過PNG推奨）",
                filetypes=[("PNG files", "*.png"), ("All image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
            )
            print(f"選択されたファイル: {files}")
            if files:
                self.load_images_from_files(files)
        except Exception as e:
            print(f"ダイアログエラー: {e}")
    
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
        self.original_images.clear()
        self.photo_images.clear()
        
        for file in files:
            try:
                print(f"画像読み込み中: {file}")
                img = Image.open(file)
                
                # GIFアニメーションの場合、全フレームを読み込み
                if hasattr(img, 'is_animated') and img.is_animated:
                    print(f"アニメーションGIF検出: {img.n_frames}フレーム")
                    for frame_num in range(img.n_frames):
                        img.seek(frame_num)
                        frame = img.copy()
                        
                        # RGBA変換（透過対応）
                        if frame.mode != 'RGBA':
                            frame = frame.convert('RGBA')
                            # 白い背景を透明にする
                            datas = frame.getdata()
                            newData = []
                            for item in datas:
                                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                                    newData.append((255, 255, 255, 0))
                                else:
                                    newData.append(item)
                            frame.putdata(newData)
                        
                        # 元画像を保存（品質劣化防止）
                        self.original_images.append(frame.copy())
                        
                        # サイズ調整
                        resized_frame = frame.copy()
                        resized_frame.thumbnail((self.size-10, self.size-10), Image.Resampling.LANCZOS)
                        
                        # 中央に配置
                        centered_img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
                        x = (self.size - resized_frame.width) // 2
                        y = (self.size - resized_frame.height) // 2
                        centered_img.paste(resized_frame, (x, y), resized_frame)
                        
                        self.images.append(centered_img)
                        photo = ImageTk.PhotoImage(centered_img)
                        self.photo_images.append(photo)
                else:
                    # 通常の画像処理
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
                    
                    # 元画像を保存（品質劣化防止）
                    self.original_images.append(img.copy())
                    
                    # サイズ調整
                    resized_img = img.copy()
                    resized_img.thumbnail((self.size-10, self.size-10), Image.Resampling.LANCZOS)
                    
                    # 中央に配置するための新しい透明画像
                    centered_img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
                    # 画像を中央に貼り付け
                    x = (self.size - resized_img.width) // 2
                    y = (self.size - resized_img.height) // 2
                    centered_img.paste(resized_img, (x, y), resized_img)
                    
                    self.images.append(centered_img)
                    photo = ImageTk.PhotoImage(centered_img)
                    self.photo_images.append(photo)
            except Exception as e:
                print(f"画像読み込みエラー: {file} - {e}")
        
        if self.photo_images:
            print(f"{len(self.photo_images)}枚の画像を読み込みました")
            self.current_index = 0
            self.animate()
        else:
            print("画像を読み込めませんでした")
    
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
        old_size = self.size
        self.size = new_size
        self.root.geometry(f"{self.size}x{self.size}")
        self.canvas.config(width=self.size, height=self.size)
        
        # 元画像から高品質で再スケール
        if self.original_images and old_size != new_size:
            temp_images = []
            self.photo_images.clear()
            
            for original_img in self.original_images:
                # 元画像のコピーを作成
                resized_img = original_img.copy()
                
                # サイズ調整（高品質）
                resized_img.thumbnail((self.size-10, self.size-10), Image.Resampling.LANCZOS)
                
                # 中央に配置
                centered_img = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
                x = (self.size - resized_img.width) // 2
                y = (self.size - resized_img.height) // 2
                centered_img.paste(resized_img, (x, y), resized_img)
                
                temp_images.append(centered_img)
                photo = ImageTk.PhotoImage(centered_img)
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
        print("メインループ開始（拡張サイズ反映済み）")
        self.root.mainloop()

if __name__ == "__main__":
    print("プログラム開始")
    
    # コマンドライン引数で画像ディレクトリを指定可能
    images_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        app = ImageAnimator(images_path)
        app.run()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()