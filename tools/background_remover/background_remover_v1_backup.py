#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import os

class BackgroundRemover:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("背景透過化ツール")
        self.root.geometry("800x600")
        
        # 変数
        self.original_image = None
        self.processed_image = None
        self.preview_image = None
        self.threshold = tk.IntVar(value=10)  # 透過の閾値（デフォルトを小さく）
        self.target_colors = [[255, 255, 255]]  # 透過する色のリスト（デフォルト白）
        self.color_mode = tk.StringVar(value="multiple")  # single/multiple（デフォルト複数色）
        self.fill_mode = tk.BooleanVar(value=True)  # 塗りつぶしモード（デフォルトON）
        self.edge_mode = tk.BooleanVar(value=True)  # 輪郭表示モード（デフォルトON）
        self.click_points = []  # クリックした座標のリスト
        self.processing = False  # 処理中フラグ
        self.color_thresholds = {}  # 各色の個別閾値
        self.edge_overlay = None  # 輪郭線オーバーレイ（レイヤー用）
        
        self.setup_ui()
    
    def setup_ui(self):
        """UIセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ファイル選択ボタン
        ttk.Button(button_frame, text="画像を選択", command=self.load_image).pack(side=tk.LEFT, padx=(0, 5))
        
        # 色選択ボタン
        ttk.Button(button_frame, text="透過色を選択", command=self.pick_color).pack(side=tk.LEFT, padx=(0, 5))
        
        # 色リセットボタン
        ttk.Button(button_frame, text="色リセット", command=self.reset_colors).pack(side=tk.LEFT, padx=(0, 5))
        
        # 輪郭外選択ボタン
        ttk.Button(button_frame, text="輪郭の外を選択", command=self.select_outside_edges).pack(side=tk.LEFT, padx=(0, 5))
        
        # プレビューボタン
        ttk.Button(button_frame, text="プレビュー更新", command=self.update_preview).pack(side=tk.LEFT, padx=(0, 5))
        
        # 保存ボタン
        ttk.Button(button_frame, text="保存", command=self.save_image).pack(side=tk.LEFT, padx=(0, 5))
        
        # 設定フレーム
        settings_frame = ttk.LabelFrame(main_frame, text="設定")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # モード選択
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(mode_frame, text="モード:").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="単色", variable=self.color_mode, value="single").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="複数色", variable=self.color_mode, value="multiple").pack(side=tk.LEFT)
        
        # 塗りつぶしモード
        ttk.Checkbutton(mode_frame, text="連続領域のみ", variable=self.fill_mode).pack(side=tk.LEFT, padx=(10, 0))
        
        # 輪郭表示モード
        ttk.Checkbutton(mode_frame, text="輪郭表示", variable=self.edge_mode).pack(side=tk.LEFT, padx=(10, 0))
        
        # 閾値設定
        threshold_label = ttk.Label(settings_frame, text="透過の範囲:")
        threshold_label.pack(side=tk.LEFT, padx=(5, 5))
        threshold_scale = ttk.Scale(settings_frame, from_=0, to=50, 
                                   variable=self.threshold, orient=tk.HORIZONTAL)
        threshold_scale.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        ttk.Label(settings_frame, textvariable=self.threshold).pack(side=tk.LEFT, padx=(0, 5))
        
        # プリセットボタン
        preset_frame = ttk.Frame(settings_frame)
        preset_frame.pack(side=tk.RIGHT, padx=(10, 5))
        ttk.Button(preset_frame, text="白", command=lambda: self.set_preset_color([255, 255, 255])).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="黒", command=lambda: self.set_preset_color([0, 0, 0])).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="緑", command=lambda: self.set_preset_color([0, 255, 0])).pack(side=tk.LEFT, padx=2)
        
        # 選択した色の表示
        self.color_list_frame = ttk.LabelFrame(main_frame, text="選択した色")
        self.color_list_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 色表示用のフレーム（スクロール可能）
        self.color_canvas = tk.Canvas(self.color_list_frame, height=80)
        self.color_scrollbar = ttk.Scrollbar(self.color_list_frame, orient="horizontal", command=self.color_canvas.xview)
        self.color_display_frame = ttk.Frame(self.color_canvas)
        
        self.color_canvas.configure(xscrollcommand=self.color_scrollbar.set)
        self.color_canvas.pack(fill=tk.X, pady=5)
        self.color_scrollbar.pack(fill=tk.X)
        self.color_canvas.create_window((0, 0), window=self.color_display_frame, anchor="nw")
        
        self.color_list_label = ttk.Label(self.color_list_frame, text="")
        self.color_list_label.pack(pady=5)
        self.update_color_list_display()
        
        # 画像表示フレーム
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True)
        
        # オリジナル画像
        original_frame = ttk.LabelFrame(image_frame, text="オリジナル")
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.original_label = ttk.Label(original_frame, text="画像を選択してください")
        self.original_label.pack(expand=True)
        
        # プレビュー画像
        preview_frame = ttk.LabelFrame(image_frame, text="プレビュー")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.preview_label = ttk.Label(preview_frame, text="プレビューエリア")
        self.preview_label.pack(expand=True)
        
        # プログレスバー
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(5, 0))
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_label = ttk.Label(self.progress_frame, text="")
        
        # ステータスバー
        self.status_var = tk.StringVar(value="画像を選択してください")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def load_image(self):
        """画像を読み込み"""
        file_path = filedialog.askopenfilename(
            title="透過化する画像を選択",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.original_image = Image.open(file_path)
                if self.original_image.mode != 'RGBA':
                    self.original_image = self.original_image.convert('RGBA')
                
                # プレビュー用にリサイズ
                self.display_original()
                
                # 輪郭線を自動生成（レイヤーとして）
                self.generate_edge_overlay()
                
                self.status_var.set(f"画像を読み込みました: {os.path.basename(file_path)} - プレビュー更新ボタンを押してください")
            except Exception as e:
                messagebox.showerror("エラー", f"画像の読み込みに失敗しました: {e}")
    
    def display_original(self):
        """オリジナル画像を表示"""
        if self.original_image:
            # 表示用にリサイズ
            display_img = self.original_image.copy()
            display_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # チェッカーボード背景を作成
            checker_size = 20
            checker_img = Image.new('RGBA', display_img.size, (255, 255, 255, 255))
            checker_draw = ImageDraw.Draw(checker_img)
            
            for x in range(0, display_img.width, checker_size):
                for y in range(0, display_img.height, checker_size):
                    if (x // checker_size + y // checker_size) % 2:
                        checker_draw.rectangle([x, y, x + checker_size, y + checker_size], 
                                             fill=(200, 200, 200, 255))
            
            # 画像を合成
            checker_img.paste(display_img, (0, 0), display_img)
            
            # Tkinter用に変換
            photo = ImageTk.PhotoImage(checker_img)
            self.original_label.configure(image=photo)
            self.original_label.image = photo
    
    def pick_color(self):
        """色を選択（画像上でクリック）"""
        if not self.original_image:
            messagebox.showwarning("警告", "まず画像を選択してください")
            return
        
        # 色選択ウィンドウを作成
        color_window = tk.Toplevel(self.root)
        color_window.title("透過する色を選択")
        color_window.geometry("500x550")  # サイズを大きく
        
        # 上部に説明ラベル
        instruction_label = ttk.Label(color_window, text="透過したい色の部分をクリックしてください", 
                                    font=('Arial', 12))
        instruction_label.pack(pady=10)
        
        # 画像を表示
        display_img = self.original_image.copy()
        display_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(display_img)
        
        canvas = tk.Canvas(color_window, width=display_img.width, height=display_img.height,
                          highlightthickness=1, highlightbackground="gray")
        canvas.pack(pady=10)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo  # 参照を保持
        
        # 複数色選択用の変数
        self.temp_colors = []
        self.temp_points = []
        
        def on_click(event):
            # クリック位置の色を取得
            scale_x = self.original_image.width / display_img.width
            scale_y = self.original_image.height / display_img.height
            x = int(event.x * scale_x)
            y = int(event.y * scale_y)
            
            if 0 <= x < self.original_image.width and 0 <= y < self.original_image.height:
                pixel = self.original_image.getpixel((x, y))
                new_color = list(pixel[:3])  # RGBのみ
                
                if self.color_mode.get() == "single":
                    self.target_colors = [new_color]
                    self.click_points = [(x, y)]
                    color_window.destroy()
                    self.update_color_list_display()
                    self.status_var.set(f"透過色を設定: RGB{tuple(new_color)} - プレビュー更新ボタンを押してください")
                else:
                    # 複数色モード：色を追加（まだ確定しない）
                    if new_color not in self.temp_colors:
                        self.temp_colors.append(new_color)
                        self.temp_points.append((x, y))
                        
                        # 選択した色を画像上に表示
                        canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, 
                                         fill='red', outline='white', width=2)
                        canvas.create_text(event.x+10, event.y-10, text=str(len(self.temp_colors)), 
                                         fill='red', font=('Arial', 12, 'bold'))
                        
                        status_text.config(text=f"{len(self.temp_colors)}色選択中 - 完了ボタンを押してください")
        
        def finish_selection():
            if self.temp_colors:
                self.target_colors = self.temp_colors.copy()
                self.click_points = self.temp_points.copy()
                color_window.destroy()
                self.update_color_list_display()
                self.status_var.set(f"{len(self.target_colors)}色を選択しました - プレビュー更新ボタンを押してください")
            else:
                messagebox.showwarning("警告", "色を選択してください")
        
        def reset_selection():
            self.temp_colors = []
            self.temp_points = []
            canvas.delete("all")
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            canvas.image = photo
            status_text.config(text="透過したい色の部分をクリックしてください")
        
        canvas.bind("<Button-1>", on_click)
        
        # ステータス表示（動的更新用）
        status_text = ttk.Label(color_window, text="透過したい色の部分をクリックしてください", 
                              font=('Arial', 10))
        status_text.pack(pady=5)
        
        # 複数色選択用のUI
        button_frame = ttk.Frame(color_window)
        button_frame.pack(pady=15)
        
        finish_btn = ttk.Button(button_frame, text="✓ 選択完了", command=finish_selection, 
                               style="Accent.TButton")
        finish_btn.pack(side=tk.LEFT, padx=10)
        
        reset_btn = ttk.Button(button_frame, text="🔄 リセット", command=reset_selection)
        reset_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = ttk.Button(button_frame, text="✕ キャンセル", command=color_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # モード説明
        if self.color_mode.get() == "multiple":
            mode_text = ttk.Label(color_window, text="複数色モード: 複数の色をクリックして「選択完了」を押してください", 
                                font=('Arial', 9), foreground="blue")
        else:
            mode_text = ttk.Label(color_window, text="単色モード: 1つの色をクリックすると自動で終了します", 
                                font=('Arial', 9), foreground="green")
        mode_text.pack(pady=5)
    
    def set_preset_color(self, color):
        """プリセット色を設定"""
        if self.color_mode.get() == "single":
            self.target_colors = [color]
        else:
            if color not in self.target_colors:
                self.target_colors.append(color)
        
        self.update_color_list_display()
        self.status_var.set(f"透過色を設定: RGB{tuple(color)} - プレビュー更新ボタンを押してください")
    
    def reset_colors(self):
        """色リセット"""
        self.target_colors = [[255, 255, 255]]  # デフォルトに戻す
        self.click_points = []  # クリック位置もリセット
        self.update_color_list_display()
        self.status_var.set("色をリセットしました - プレビュー更新ボタンを押してください")
    
    def update_color_list_display(self):
        """選択した色のリストを表示"""
        # 既存の色表示ウィジェットを削除
        for widget in self.color_display_frame.winfo_children():
            widget.destroy()
        
        if not self.target_colors:
            self.color_list_label.config(text="色が選択されていません")
        else:
            # 各色を視覚的に表示
            for i, color in enumerate(self.target_colors):
                # 色ごとのフレーム
                color_frame = ttk.Frame(self.color_display_frame)
                color_frame.pack(side=tk.LEFT, padx=5, pady=2)
                
                # 色見本のキャンバス
                color_canvas = tk.Canvas(color_frame, width=40, height=30, 
                                       highlightthickness=1, highlightbackground="black")
                color_canvas.pack()
                
                # 色を塗りつぶし
                color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                color_canvas.create_rectangle(0, 0, 40, 30, fill=color_hex, outline="")
                
                # RGB値のラベル
                color_label = ttk.Label(color_frame, 
                                      text=f"RGB{tuple(color)}", 
                                      font=("Arial", 7))
                color_label.pack()
                
                # 個別閾値スライダー
                color_key = tuple(color)
                if color_key not in self.color_thresholds:
                    self.color_thresholds[color_key] = 10
                
                threshold_var = tk.IntVar(value=self.color_thresholds[color_key])
                
                # スライダーと微調整ボタンのフレーム
                slider_frame = ttk.Frame(color_frame)
                slider_frame.pack()
                
                # 左の微調整ボタン（-1）
                def decrease_threshold(key=color_key, var=threshold_var, label_ref=[None]):
                    current = var.get()
                    if current > 0:
                        var.set(current - 1)
                        self.color_thresholds[key] = current - 1
                        if label_ref[0]:
                            label_ref[0].config(text=f"閾値: {current - 1}")
                
                left_btn = ttk.Button(slider_frame, text="◀", width=3, command=decrease_threshold)
                left_btn.pack(side=tk.LEFT)
                
                # メインスライダー
                threshold_scale = ttk.Scale(slider_frame, from_=0, to=50, 
                                          variable=threshold_var, orient=tk.HORIZONTAL,
                                          length=120)  # 微調整ボタン分少し短く
                threshold_scale.pack(side=tk.LEFT, padx=2)
                
                # 右の微調整ボタン（+1）
                def increase_threshold(key=color_key, var=threshold_var, label_ref=[None]):
                    current = var.get()
                    if current < 50:
                        var.set(current + 1)
                        self.color_thresholds[key] = current + 1
                        if label_ref[0]:
                            label_ref[0].config(text=f"閾値: {current + 1}")
                
                right_btn = ttk.Button(slider_frame, text="▶", width=3, command=increase_threshold)
                right_btn.pack(side=tk.LEFT)
                
                # 閾値ラベル
                threshold_label = ttk.Label(color_frame, text=f"閾値: {threshold_var.get()}", 
                                          font=("Arial", 7))
                threshold_label.pack()
                
                # ラベル参照を更新
                decrease_threshold.__defaults__ = (color_key, threshold_var, [threshold_label])
                increase_threshold.__defaults__ = (color_key, threshold_var, [threshold_label])
                
                # 閾値更新のコールバック
                def update_threshold(value, key=color_key, label=threshold_label, var=threshold_var):
                    self.color_thresholds[key] = int(float(value))
                    label.config(text=f"閾値: {var.get()}")
                
                threshold_scale.config(command=update_threshold)
            
            self.color_list_label.config(text=f"{len(self.target_colors)}色選択中")
            
            # スクロール領域を更新
            self.color_display_frame.update_idletasks()
            self.color_canvas.configure(scrollregion=self.color_canvas.bbox("all"))
    
    def update_preview(self, *args):
        """プレビューを更新"""
        if not self.original_image or self.processing:
            return
        
        # 処理開始
        self.processing = True
        self.show_progress("画像を処理中...")
        
        # UIを無効化
        self.root.config(cursor="wait")
        
        try:
            if self.fill_mode.get() and self.click_points:
                # 塗りつぶしモード
                self.processed_image = self.flood_fill_transparent()
            else:
                # 通常モード
                self.update_progress_text("通常モードで処理中...")
                self.processed_image = self.original_image.copy()
                data = list(self.processed_image.getdata())
                
                threshold = self.threshold.get()
                total_pixels = len(data)
                
                new_data = []
                for i, pixel in enumerate(data):
                    # 定期的にプログレスバーを更新
                    if i % 10000 == 0:
                        self.root.update_idletasks()
                    
                    r, g, b = pixel[:3]
                    should_remove = False
                    
                    # 各ターゲット色と比較（個別閾値使用）
                    for target_color in self.target_colors:
                        target_r, target_g, target_b = target_color
                        color_key = tuple(target_color)
                        
                        # この色の個別閾値を取得
                        color_threshold = self.color_thresholds.get(color_key, threshold)
                        
                        # 色の差を計算
                        diff = abs(r - target_r) + abs(g - target_g) + abs(b - target_b)
                        
                        if diff <= color_threshold * 3:  # 個別閾値を使用
                            should_remove = True
                            break
                    
                    if should_remove:
                        # 透明にする
                        new_data.append((r, g, b, 0))
                    else:
                        # そのまま
                        if len(pixel) == 4:
                            new_data.append(pixel)
                        else:
                            new_data.append((r, g, b, 255))
                
                self.processed_image.putdata(new_data)
            
            # プレビュー表示（輪郭は別レイヤーとして表示）
            self.update_progress_text("プレビューを更新中...")
            self.display_preview()
            
        finally:
            # 処理終了
            self.processing = False
            self.hide_progress()
            self.root.config(cursor="")
            self.status_var.set("プレビュー更新完了")
    
    def show_progress(self, text="処理中..."):
        """プログレスバーを表示"""
        self.progress_label.config(text=text)
        self.progress_label.pack(side=tk.LEFT, padx=(0, 10))
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_bar.start(10)
        self.root.update_idletasks()
    
    def update_progress_text(self, text):
        """プログレスバーのテキストを更新"""
        self.progress_label.config(text=text)
        self.root.update_idletasks()
    
    def hide_progress(self):
        """プログレスバーを非表示"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
    
    def generate_edge_overlay(self):
        """輪郭線オーバーレイを生成（レイヤー用）"""
        if not self.original_image:
            return
        
        import numpy as np
        from PIL import ImageFilter, ImageEnhance
        
        # グレースケール変換
        gray_img = self.original_image.convert('L')
        
        # エッジ検出フィルタを適用
        edges = gray_img.filter(ImageFilter.FIND_EDGES)
        
        # エッジを強調
        enhancer = ImageEnhance.Contrast(edges)
        edges = enhancer.enhance(2.0)
        
        # エッジを透明な赤線として作成
        edge_array = np.array(edges)
        height, width = edge_array.shape
        
        # 透明な画像を作成
        overlay_array = np.zeros((height, width, 4), dtype=np.uint8)
        
        # エッジ部分を赤色で描画
        edge_mask = edge_array > 50
        overlay_array[edge_mask] = [255, 0, 0, 128]  # 半透明の赤
        
        self.edge_overlay = Image.fromarray(overlay_array, 'RGBA')
    
    def flood_fill_transparent(self):
        """塗りつぶし透過処理"""
        import numpy as np
        from collections import deque
        
        self.update_progress_text("連続領域を検出中...")
        
        # 画像をnumpy配列に変換
        img_array = np.array(self.original_image)
        height, width = img_array.shape[:2]
        
        # 結果用の画像をコピー
        result_array = img_array.copy()
        
        # アルファチャンネルを追加（必要な場合）
        if result_array.shape[2] == 3:
            alpha = np.full((height, width, 1), 255, dtype=np.uint8)
            result_array = np.concatenate([result_array, alpha], axis=2)
        
        # マスク作成（透過する領域）
        mask = np.zeros((height, width), dtype=bool)
        threshold = self.threshold.get()
        
        # 各クリック位置から塗りつぶし
        for i, (start_x, start_y) in enumerate(self.click_points):
            self.update_progress_text(f"領域 {i+1}/{len(self.click_points)} を処理中...")
            
            # この開始位置用の訪問済みフラグ
            visited = np.zeros((height, width), dtype=bool)
            
            # 開始位置の色（ターゲット色リストから取得）
            if i < len(self.target_colors):
                target_color = np.array(self.target_colors[i])
            else:
                target_color = img_array[start_y, start_x, :3]
            
            # BFS用のキュー
            queue = deque([(start_x, start_y)])
            visited[start_y, start_x] = True
            temp_mask = np.zeros((height, width), dtype=bool)
            temp_mask[start_y, start_x] = True
            
            processed_pixels = 0
            while queue:
                x, y = queue.popleft()
                processed_pixels += 1
                
                # 定期的にUIを更新
                if processed_pixels % 1000 == 0:
                    self.root.update_idletasks()
                
                # 8方向の隣接ピクセルをチェック（より滑らかな境界のため）
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                            
                        nx, ny = x + dx, y + dy
                        
                        if (0 <= nx < width and 0 <= ny < height and 
                            not visited[ny, nx]):
                            
                            # 現在のピクセルの色
                            current_color = img_array[ny, nx, :3]
                            
                            # 各色チャンネルの差を個別に計算
                            color_diff = np.abs(current_color.astype(int) - target_color.astype(int))
                            
                            # ユークリッド距離で判定（個別閾値使用）
                            distance = np.sqrt(np.sum(color_diff ** 2))
                            
                            # この色の個別閾値を取得
                            color_key = tuple(target_color)
                            color_threshold = self.color_thresholds.get(color_key, threshold)
                            
                            if distance <= color_threshold:
                                visited[ny, nx] = True
                                temp_mask[ny, nx] = True
                                queue.append((nx, ny))
            
            # マスクを更新
            mask = mask | temp_mask
        
        # マスクを適用して透明化
        result_array[mask, 3] = 0
        
        # numpy配列をPIL画像に戻す
        return Image.fromarray(result_array, 'RGBA')
    
    def select_outside_edges(self):
        """輪郭の外側を自動選択"""
        if not self.original_image:
            messagebox.showwarning("警告", "まず画像を選択してください")
            return
        
        try:
            self.show_progress("輪郭を検出中...")
            import numpy as np
            from PIL import ImageFilter, ImageEnhance
            
            # グレースケール変換
            gray_img = self.original_image.convert('L')
            
            # エッジ検出
            edges = gray_img.filter(ImageFilter.FIND_EDGES)
            enhancer = ImageEnhance.Contrast(edges)
            edges = enhancer.enhance(2.0)
            
            # エッジをバイナリ化（閾値を下げて、より細かいエッジも検出）
            edge_array = np.array(edges)
            edge_binary = edge_array > 20  # 閾値を50→20に下げる
            
            self.update_progress_text("外側領域を検出中...")
            
            # 画像の4つの角から塗りつぶし（外側領域を検出）
            height, width = edge_binary.shape
            visited = np.zeros((height, width), dtype=bool)
            outside_mask = np.zeros((height, width), dtype=bool)
            
            # 画像の周囲全体からフラッドフィル（より広範囲にチェック）
            from collections import deque
            
            # 上下の端から開始
            for x in range(0, width, max(1, width//20)):  # 20分割でチェック
                for y in [0, height-1]:
                    if not visited[y, x] and not edge_binary[y, x]:
                        queue = deque([(x, y)])
                        visited[y, x] = True
                        
                        while queue:
                            cx, cy = queue.popleft()
                            outside_mask[cy, cx] = True
                            
                            # 4方向チェック
                            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                nx, ny = cx + dx, cy + dy
                                
                                if (0 <= nx < width and 0 <= ny < height and 
                                    not visited[ny, nx] and not edge_binary[ny, nx]):
                                    visited[ny, nx] = True
                                    queue.append((nx, ny))
            
            # 左右の端から開始
            for y in range(0, height, max(1, height//20)):  # 20分割でチェック
                for x in [0, width-1]:
                    if not visited[y, x] and not edge_binary[y, x]:
                        queue = deque([(x, y)])
                        visited[y, x] = True
                        
                        while queue:
                            cx, cy = queue.popleft()
                            outside_mask[cy, cx] = True
                            
                            # 4方向チェック
                            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                nx, ny = cx + dx, cy + dy
                                
                                if (0 <= nx < width and 0 <= ny < height and 
                                    not visited[ny, nx] and not edge_binary[ny, nx]):
                                    visited[ny, nx] = True
                                    queue.append((nx, ny))
            
            self.update_progress_text("外側領域の色を分析中...")
            
            # 外側領域の代表色を取得
            img_array = np.array(self.original_image)
            if img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]  # RGBのみ
            
            outside_pixels = img_array[outside_mask]
            
            print(f"外側領域のピクセル数: {len(outside_pixels)}")  # デバッグ用
            
            if len(outside_pixels) > 10:  # 最小ピクセル数をさらに下げる
                try:
                    # K-meansクラスタリングで代表色を取得
                    from sklearn.cluster import KMeans
                    
                    # ピクセル数が多い場合はサンプリング
                    if len(outside_pixels) > 10000:
                        indices = np.random.choice(len(outside_pixels), 10000, replace=False)
                        sample_pixels = outside_pixels[indices]
                    else:
                        sample_pixels = outside_pixels
                    
                    # 2-7個の代表色を取得（より多くの色を検出）
                    unique_colors = len(np.unique(sample_pixels.view(np.void), axis=0))
                    n_colors = min(7, max(2, unique_colors // 100 + 2))  # より多くの色を検出
                    print(f"検出する色数: {n_colors}")  # デバッグ用
                    
                    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
                    kmeans.fit(sample_pixels)
                    
                    # 代表色を追加
                    self.target_colors = []
                    self.click_points = []
                    
                    for color in kmeans.cluster_centers_:
                        color_int = [int(c) for c in color]
                        self.target_colors.append(color_int)
                        
                        # 対応する座標を見つける
                        distances = np.sum((sample_pixels - color) ** 2, axis=1)
                        closest_idx = np.argmin(distances)
                        
                        # 元の画像での座標を推定
                        mask_indices = np.where(outside_mask)
                        if len(mask_indices[0]) > closest_idx:
                            y_coord = mask_indices[0][closest_idx]
                            x_coord = mask_indices[1][closest_idx]
                            self.click_points.append((x_coord, y_coord))
                    
                    self.update_color_list_display()
                    self.status_var.set(f"輪郭外の{len(self.target_colors)}色を自動選択しました - プレビュー更新ボタンを押してください")
                
                except Exception as e:
                    print(f"K-means処理エラー: {e}")  # デバッグ用
                    # K-meansが失敗した場合は単純な色分析を実行
                    try:
                        # 最頻色を取得
                        unique_colors, counts = np.unique(sample_pixels.view(np.void), return_counts=True, axis=0)
                        most_common_indices = np.argsort(counts)[::-1][:5]  # 上位5色
                        
                        self.target_colors = []
                        self.click_points = []
                        
                        for idx in most_common_indices:
                            color_bytes = unique_colors[idx].view(np.uint8).reshape(-1, 3)[0]
                            color_int = [int(c) for c in color_bytes]
                            self.target_colors.append(color_int)
                            
                            # 対応する座標を見つける
                            mask_indices = np.where(outside_mask)
                            if len(mask_indices[0]) > 0:
                                y_coord = mask_indices[0][0]
                                x_coord = mask_indices[1][0]
                                self.click_points.append((x_coord, y_coord))
                        
                        self.update_color_list_display()
                        self.status_var.set(f"輪郭外の{len(self.target_colors)}色を単純分析で選択しました - プレビュー更新ボタンを押してください")
                    except Exception as e2:
                        print(f"単純分析も失敗: {e2}")
                        messagebox.showerror("エラー", f"色の分析に失敗しました: {e}")
            else:
                print(f"外側領域が少なすぎます: {len(outside_pixels)}ピクセル")  # デバッグ用
                messagebox.showinfo("情報", f"輪郭外の領域が少なすぎます（{len(outside_pixels)}ピクセル）\\n手動で色を選択してください")
                
        except ImportError:
            messagebox.showerror("エラー", "この機能にはscikit-learnが必要です:\npip install scikit-learn")
        except Exception as e:
            messagebox.showerror("エラー", f"輪郭検出に失敗しました: {e}")
        finally:
            self.hide_progress()
    
    def display_preview(self):
        """プレビュー画像を表示"""
        if self.processed_image:
            # 表示用にリサイズ
            display_img = self.processed_image.copy()
            display_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # 輪郭線オーバーレイを合成（レイヤー表示）
            if self.edge_mode.get() and self.edge_overlay:
                edge_resized = self.edge_overlay.copy()
                edge_resized.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # 輪郭線を合成
                display_img = Image.alpha_composite(display_img, edge_resized)
            
            # チェッカーボード背景を作成
            checker_size = 20
            checker_img = Image.new('RGBA', display_img.size, (255, 255, 255, 255))
            checker_draw = ImageDraw.Draw(checker_img)
            
            for x in range(0, display_img.width, checker_size):
                for y in range(0, display_img.height, checker_size):
                    if (x // checker_size + y // checker_size) % 2:
                        checker_draw.rectangle([x, y, x + checker_size, y + checker_size], 
                                             fill=(200, 200, 200, 255))
            
            # 画像を合成
            checker_img.paste(display_img, (0, 0), display_img)
            
            # Tkinter用に変換
            photo = ImageTk.PhotoImage(checker_img)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
    
    def save_image(self):
        """画像を保存"""
        if not self.processed_image:
            messagebox.showwarning("警告", "処理する画像がありません")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="透過画像を保存",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # 保存時は輪郭線を含めない（元の処理済み画像のみ）
                save_image = self.processed_image.copy()
                save_image.save(file_path, "PNG")
                messagebox.showinfo("完了", f"画像を保存しました: {os.path.basename(file_path)}")
                self.status_var.set(f"保存完了: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました: {e}")
    
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BackgroundRemover()
    app.run()