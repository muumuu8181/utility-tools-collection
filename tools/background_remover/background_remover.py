#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import time

# Pillowバージョン互換性対応
try:
    from PIL.Image import Resampling
    LANCZOS = Resampling.LANCZOS
    NEAREST = Resampling.NEAREST
except ImportError:
    from PIL import Image
    LANCZOS = Image.LANCZOS
    NEAREST = Image.NEAREST

class BackgroundRemoverOptimized:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("背景透過化ツール (高速版)")
        self.root.geometry("800x600")
        
        # 変数
        self.original_image = None
        self.processed_image = None
        self.preview_image = None
        self.threshold = tk.IntVar(value=10)
        self.target_colors = [[255, 255, 255]]
        self.color_mode = tk.StringVar(value="multiple")
        self.fill_mode = tk.BooleanVar(value=True)
        self.edge_mode = tk.BooleanVar(value=True)
        self.smooth_edges = tk.BooleanVar(value=True)  # エッジスムージング
        self.smooth_strength = tk.IntVar(value=2)  # スムージング強度
        self.click_points = []
        self.processing = False
        self.color_thresholds = {}
        self.edge_overlay = None
        
        # 高速化用のキャッシュ
        self.image_cache = {}
        self.preview_cache = {}
        
        # マルチスレッド用
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.processing_queue = Queue()
        
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
        ttk.Button(button_frame, text="プレビュー更新", command=self.update_preview_threaded).pack(side=tk.LEFT, padx=(0, 5))
        
        # 保存ボタン
        ttk.Button(button_frame, text="保存", command=self.save_image).pack(side=tk.LEFT, padx=(0, 5))
        
        # MP4→GIF変換ボタン
        ttk.Button(button_frame, text="MP4→GIF", command=self.convert_mp4_to_gif).pack(side=tk.LEFT, padx=(0, 5))
        
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
        
        # エッジスムージング
        ttk.Checkbutton(mode_frame, text="エッジを滑らかに", variable=self.smooth_edges).pack(side=tk.LEFT, padx=(10, 0))
        
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
        
        # 選択した色の表示（スクロール可能）
        self.color_list_frame = ttk.LabelFrame(main_frame, text="選択した色")
        self.color_list_frame.pack(fill=tk.X, pady=(0, 10))
        
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
                # 高速読み込み：キャッシュをクリア
                self.image_cache.clear()
                self.preview_cache.clear()
                
                self.original_image = Image.open(file_path)
                if self.original_image.mode != 'RGBA':
                    self.original_image = self.original_image.convert('RGBA')
                
                # プレビュー用にリサイズ
                self.display_original()
                
                # 輪郭線を非同期で生成
                self.generate_edge_overlay_async()
                
                self.status_var.set(f"画像を読み込みました: {os.path.basename(file_path)} - プレビュー更新ボタンを押してください")
            except Exception as e:
                messagebox.showerror("エラー", f"画像の読み込みに失敗しました: {e}")
    
    def generate_edge_overlay_async(self):
        """輪郭線オーバーレイを非同期生成"""
        def _generate():
            if not self.original_image:
                return
            
            from PIL import ImageFilter, ImageEnhance
            
            # numpy配列に変換（高速化）
            img_array = np.array(self.original_image.convert('L'))
            
            # Sobelフィルタで高速エッジ検出
            from scipy import ndimage
            sobel_x = ndimage.sobel(img_array, axis=1)
            sobel_y = ndimage.sobel(img_array, axis=0)
            edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
            
            # 正規化とバイナリ化
            edge_magnitude = (edge_magnitude / edge_magnitude.max() * 255).astype(np.uint8)
            edge_mask = edge_magnitude > 50
            
            # オーバーレイ作成
            height, width = edge_mask.shape
            overlay_array = np.zeros((height, width, 4), dtype=np.uint8)
            overlay_array[edge_mask] = [255, 0, 0, 128]
            
            self.edge_overlay = Image.fromarray(overlay_array, 'RGBA')
        
        # バックグラウンドで実行
        self.executor.submit(_generate)
    
    def update_preview_threaded(self):
        """プレビュー更新（マルチスレッド版）"""
        if not self.original_image or self.processing:
            return
        
        self.processing = True
        self.show_progress("高速処理中...")
        self.root.config(cursor="wait")
        
        def _process():
            try:
                if self.fill_mode.get() and self.click_points:
                    # 連続領域処理（numpy最適化版）
                    result = self.flood_fill_transparent_optimized()
                else:
                    # 通常処理（numpy最適化版）
                    result = self.process_normal_optimized()
                
                # メインスレッドで結果を適用
                self.root.after(0, lambda: self._apply_result(result))
                
            except Exception as e:
                self.root.after(0, lambda: self._handle_error(e))
        
        # バックグラウンドで実行
        self.executor.submit(_process)
    
    def process_normal_optimized(self):
        """通常処理の最適化版（numpy使用）"""
        self.update_progress_text("numpy最適化処理中...")
        
        # numpy配列に変換
        img_array = np.array(self.original_image)
        rgb_array = img_array[:, :, :3]  # RGBのみ
        alpha_array = img_array[:, :, 3:4] if img_array.shape[2] == 4 else np.full((img_array.shape[0], img_array.shape[1], 1), 255)
        
        # 全ピクセルの処理を一度に実行（超高速）
        should_remove = np.zeros(rgb_array.shape[:2], dtype=bool)
        
        # 各ターゲット色と比較（ベクトル化）
        for target_color in self.target_colors:
            color_key = tuple(target_color)
            color_threshold = self.color_thresholds.get(color_key, self.threshold.get())
            
            target_array = np.array(target_color)
            
            # 色の差を一括計算（超高速）
            diff = np.abs(rgb_array - target_array)
            total_diff = np.sum(diff, axis=2)
            
            # 閾値判定
            mask = total_diff <= color_threshold * 3
            should_remove |= mask
        
        # アルファチャンネルを更新
        new_alpha = alpha_array.copy()
        new_alpha[should_remove] = 0
        
        # 結果画像を作成
        result_array = np.concatenate([rgb_array, new_alpha], axis=2)
        result_image = Image.fromarray(result_array, 'RGBA')
        
        # エッジスムージング適用
        if self.smooth_edges.get():
            result_image = self.apply_edge_smoothing(result_image)
        
        return result_image
    
    def flood_fill_transparent_optimized(self):
        """連続領域処理の最適化版"""
        self.update_progress_text("高速連続領域検出中...")
        
        # numpy配列に変換
        img_array = np.array(self.original_image)
        height, width = img_array.shape[:2]
        
        # 結果配列を準備
        result_array = img_array.copy()
        if result_array.shape[2] == 3:
            alpha = np.full((height, width, 1), 255, dtype=np.uint8)
            result_array = np.concatenate([result_array, alpha], axis=2)
        
        # 高速フラッドフィル（scipy使用）
        from scipy import ndimage
        
        # 全体のマスクを作成
        total_mask = np.zeros((height, width), dtype=bool)
        
        for i, (start_x, start_y) in enumerate(self.click_points):
            if i < len(self.target_colors):
                target_color = np.array(self.target_colors[i])
                color_key = tuple(self.target_colors[i])
                threshold = self.color_thresholds.get(color_key, self.threshold.get())
                
                # 色の類似度マップを作成
                color_diff = np.sum(np.abs(img_array[:, :, :3] - target_color), axis=2)
                similarity_mask = color_diff <= threshold
                
                # 連結成分ラベリング（超高速）
                labeled, num_labels = ndimage.label(similarity_mask)
                
                # 開始点が含まれる領域のラベル
                if 0 <= start_y < height and 0 <= start_x < width:
                    start_label = labeled[start_y, start_x]
                    if start_label > 0:
                        region_mask = labeled == start_label
                        total_mask |= region_mask
        
        # アルファチャンネルを更新
        result_array[total_mask, 3] = 0
        
        result_image = Image.fromarray(result_array, 'RGBA')
        
        # エッジスムージング適用
        if self.smooth_edges.get():
            result_image = self.apply_edge_smoothing(result_image)
        
        return result_image
    
    def _apply_result(self, result):
        """処理結果を適用"""
        self.processed_image = result
        self.display_preview()
        self._finish_processing()
    
    def _handle_error(self, error):
        """エラーハンドリング"""
        messagebox.showerror("エラー", f"処理中にエラーが発生しました: {error}")
        self._finish_processing()
    
    def _finish_processing(self):
        """処理完了"""
        self.processing = False
        self.hide_progress()
        self.root.config(cursor="")
        self.status_var.set("プレビュー更新完了")
    
    def apply_edge_smoothing(self, image):
        """エッジスムージング処理"""
        self.update_progress_text("エッジを滑らかに処理中...")
        
        try:
            from scipy import ndimage
            import numpy as np
            
            # アルファチャンネルをnumpy配列で取得
            alpha_array = np.array(image.split()[-1])  # アルファチャンネル
            
            # エッジ検出（透明度の境界を検出）
            edge_kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
            edges = ndimage.convolve(alpha_array.astype(float), edge_kernel)
            edge_mask = np.abs(edges) > 50  # エッジ部分のマスク
            
            # ガウシアンフィルタでスムージング
            smooth_strength = self.smooth_strength.get()
            sigma = smooth_strength * 0.8  # スムージング強度
            
            # アルファチャンネルをスムージング
            smoothed_alpha = ndimage.gaussian_filter(alpha_array.astype(float), sigma=sigma)
            
            # エッジ部分のみスムージング適用
            result_alpha = alpha_array.astype(float)
            
            # エッジ付近をより滑らかに
            dilated_edges = ndimage.binary_dilation(edge_mask, iterations=smooth_strength)
            result_alpha[dilated_edges] = smoothed_alpha[dilated_edges]
            
            # アンチエイリアシング効果（グラデーション作成）
            for strength in range(1, smooth_strength + 1):
                kernel_size = strength * 2 + 1
                kernel = np.ones((kernel_size, kernel_size)) / (kernel_size ** 2)
                temp_alpha = ndimage.convolve(result_alpha, kernel)
                
                # 境界付近のみ適用
                boundary_mask = ndimage.binary_dilation(edge_mask, iterations=strength)
                blend_factor = 0.3 / strength  # 強度に応じて調整
                result_alpha[boundary_mask] = (1 - blend_factor) * result_alpha[boundary_mask] + blend_factor * temp_alpha[boundary_mask]
            
            # 結果をクリップして適用
            result_alpha = np.clip(result_alpha, 0, 255).astype(np.uint8)
            
            # 新しい画像を作成
            result_image = image.copy()
            bands = list(result_image.split())
            bands[-1] = Image.fromarray(result_alpha, 'L')  # アルファチャンネル置換
            
            return Image.merge('RGBA', bands)
            
        except Exception as e:
            # エラーの場合は元の画像を返す
            self.status_var.set(f"スムージングエラー: {e}")
            return image
    
    def display_preview(self):
        """プレビュー画像を表示（最適化版）"""
        if self.processed_image:
            cache_key = f"{id(self.processed_image)}_{self.edge_mode.get()}"
            
            # キャッシュチェック
            if cache_key in self.preview_cache:
                photo = self.preview_cache[cache_key]
                self.preview_label.configure(image=photo)
                self.preview_label.image = photo
                return
            
            # 表示用にリサイズ（高速リサンプリング）
            display_img = self.processed_image.copy()
            display_img.thumbnail((300, 300), NEAREST)  # 高速リサンプリング
            
            # 輪郭線オーバーレイを合成
            if self.edge_mode.get() and self.edge_overlay:
                edge_resized = self.edge_overlay.copy()
                edge_resized.thumbnail((300, 300), NEAREST)
                display_img = Image.alpha_composite(display_img, edge_resized)
            
            # チェッカーボード背景（最適化版）
            checker_img = self._create_checker_background_fast(display_img.size)
            checker_img.paste(display_img, (0, 0), display_img)
            
            # Tkinter用に変換してキャッシュ
            photo = ImageTk.PhotoImage(checker_img)
            self.preview_cache[cache_key] = photo
            
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
    
    def _create_checker_background_fast(self, size):
        """高速チェッカーボード背景作成"""
        cache_key = f"checker_{size[0]}_{size[1]}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key].copy()
        
        # numpy配列で高速作成
        checker_size = 20
        width, height = size
        
        # チェッカーパターンをnumpyで生成
        checker_array = np.zeros((height, width, 4), dtype=np.uint8)
        checker_array[:] = [255, 255, 255, 255]  # 白背景
        
        # グレーのチェッカー
        for y in range(0, height, checker_size):
            for x in range(0, width, checker_size):
                if ((x // checker_size) + (y // checker_size)) % 2:
                    y_end = min(y + checker_size, height)
                    x_end = min(x + checker_size, width)
                    checker_array[y:y_end, x:x_end] = [200, 200, 200, 255]
        
        checker_img = Image.fromarray(checker_array, 'RGBA')
        self.image_cache[cache_key] = checker_img
        return checker_img.copy()
    
    # プログレス関連メソッド（軽量化）
    def show_progress(self, text="処理中..."):
        self.progress_label.config(text=text)
        self.progress_label.pack(side=tk.LEFT, padx=(0, 10))
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_bar.start(10)
        self.root.update_idletasks()
    
    def update_progress_text(self, text):
        self.progress_label.config(text=text)
        self.root.update_idletasks()
    
    def hide_progress(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
    
    # 以下、元のメソッドの軽量版を実装
    def display_original(self):
        """オリジナル画像を表示"""
        if self.original_image:
            display_img = self.original_image.copy()
            display_img.thumbnail((300, 300), NEAREST)
            
            checker_img = self._create_checker_background_fast(display_img.size)
            checker_img.paste(display_img, (0, 0), display_img)
            
            photo = ImageTk.PhotoImage(checker_img)
            self.original_label.configure(image=photo)
            self.original_label.image = photo
    
    def pick_color(self):
        """色を選択（元のUIを維持）"""
        if not self.original_image:
            messagebox.showwarning("警告", "まず画像を選択してください")
            return
        
        color_window = tk.Toplevel(self.root)
        color_window.title("透過する色を選択")
        color_window.geometry("500x550")
        
        instruction_label = ttk.Label(color_window, text="透過したい色の部分をクリックしてください", 
                                    font=('Arial', 12))
        instruction_label.pack(pady=10)
        
        display_img = self.original_image.copy()
        display_img.thumbnail((400, 400), LANCZOS)
        photo = ImageTk.PhotoImage(display_img)
        
        canvas = tk.Canvas(color_window, width=display_img.width, height=display_img.height,
                          highlightthickness=1, highlightbackground="gray")
        canvas.pack(pady=10)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo
        
        self.temp_colors = []
        self.temp_points = []
        
        def on_click(event):
            scale_x = self.original_image.width / display_img.width
            scale_y = self.original_image.height / display_img.height
            x = int(event.x * scale_x)
            y = int(event.y * scale_y)
            
            if 0 <= x < self.original_image.width and 0 <= y < self.original_image.height:
                pixel = self.original_image.getpixel((x, y))
                new_color = list(pixel[:3])
                
                if self.color_mode.get() == "single":
                    self.target_colors = [new_color]
                    self.click_points = [(x, y)]
                    color_window.destroy()
                    self.update_color_list_display()
                    self.status_var.set(f"透過色を設定: RGB{tuple(new_color)} - プレビュー更新ボタンを押してください")
                else:
                    if new_color not in self.temp_colors:
                        self.temp_colors.append(new_color)
                        self.temp_points.append((x, y))
                        
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
        
        status_text = ttk.Label(color_window, text="透過したい色の部分をクリックしてください", 
                              font=('Arial', 10))
        status_text.pack(pady=5)
        
        button_frame = ttk.Frame(color_window)
        button_frame.pack(pady=15)
        
        ttk.Button(button_frame, text="✓ 選択完了", command=finish_selection).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="🔄 リセット", command=reset_selection).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="✕ キャンセル", command=color_window.destroy).pack(side=tk.LEFT, padx=10)
        
        if self.color_mode.get() == "multiple":
            mode_text = ttk.Label(color_window, text="複数色モード: 複数の色をクリックして「選択完了」を押してください", 
                                font=('Arial', 9), foreground="blue")
        else:
            mode_text = ttk.Label(color_window, text="単色モード: 1つの色をクリックすると自動で終了します", 
                                font=('Arial', 9), foreground="green")
        mode_text.pack(pady=5)
    
    def update_color_list_display(self):
        """選択した色のリストを表示（軽量版）"""
        for widget in self.color_display_frame.winfo_children():
            widget.destroy()
        
        if not self.target_colors:
            self.color_list_label.config(text="色が選択されていません")
        else:
            for i, color in enumerate(self.target_colors):
                color_frame = ttk.Frame(self.color_display_frame)
                color_frame.pack(side=tk.LEFT, padx=5, pady=2)
                
                color_canvas = tk.Canvas(color_frame, width=40, height=30, 
                                       highlightthickness=1, highlightbackground="black")
                color_canvas.pack()
                
                color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                color_canvas.create_rectangle(0, 0, 40, 30, fill=color_hex, outline="")
                
                color_label = ttk.Label(color_frame, 
                                      text=f"RGB{tuple(color)}", 
                                      font=("Arial", 7))
                color_label.pack()
                
                # 個別閾値スライダー
                color_key = tuple(color)
                if color_key not in self.color_thresholds:
                    self.color_thresholds[color_key] = 10
                
                threshold_var = tk.IntVar(value=self.color_thresholds[color_key])
                
                slider_frame = ttk.Frame(color_frame)
                slider_frame.pack()
                
                def make_threshold_functions(key, var):
                    def decrease():
                        current = var.get()
                        if current > 0:
                            var.set(current - 1)
                            self.color_thresholds[key] = current - 1
                            threshold_label.config(text=f"閾値: {current - 1}")
                    
                    def increase():
                        current = var.get()
                        if current < 50:
                            var.set(current + 1)
                            self.color_thresholds[key] = current + 1
                            threshold_label.config(text=f"閾値: {current + 1}")
                    
                    def update_threshold(value):
                        self.color_thresholds[key] = int(float(value))
                        threshold_label.config(text=f"閾値: {var.get()}")
                    
                    return decrease, increase, update_threshold
                
                decrease_func, increase_func, update_func = make_threshold_functions(color_key, threshold_var)
                
                ttk.Button(slider_frame, text="◀", width=3, command=decrease_func).pack(side=tk.LEFT)
                
                threshold_scale = ttk.Scale(slider_frame, from_=0, to=50, 
                                          variable=threshold_var, orient=tk.HORIZONTAL,
                                          length=120, command=update_func)
                threshold_scale.pack(side=tk.LEFT, padx=2)
                
                ttk.Button(slider_frame, text="▶", width=3, command=increase_func).pack(side=tk.LEFT)
                
                threshold_label = ttk.Label(color_frame, text=f"閾値: {threshold_var.get()}", 
                                          font=("Arial", 7))
                threshold_label.pack()
            
            self.color_list_label.config(text=f"{len(self.target_colors)}色選択中")
            
            self.color_display_frame.update_idletasks()
            self.color_canvas.configure(scrollregion=self.color_canvas.bbox("all"))
    
    def reset_colors(self):
        """色リセット"""
        self.target_colors = [[255, 255, 255]]
        self.click_points = []
        self.color_thresholds = {}
        self.preview_cache.clear()  # キャッシュもクリア
        self.update_color_list_display()
        self.status_var.set("色をリセットしました - プレビュー更新ボタンを押してください")
    
    def set_preset_color(self, color):
        """プリセット色を設定"""
        if self.color_mode.get() == "single":
            self.target_colors = [color]
        else:
            if color not in self.target_colors:
                self.target_colors.append(color)
        
        self.update_color_list_display()
        self.status_var.set(f"透過色を設定: RGB{tuple(color)} - プレビュー更新ボタンを押してください")
    
    def select_outside_edges(self):
        """輪郭の外側を自動選択（簡易版）"""
        if not self.original_image:
            messagebox.showwarning("警告", "まず画像を選択してください")
            return
        
        self.show_progress("輪郭を高速検出中...")
        
        def _detect():
            try:
                import numpy as np
                from PIL import ImageFilter
                
                # 高速エッジ検出
                gray_img = self.original_image.convert('L')
                edges = gray_img.filter(ImageFilter.FIND_EDGES)
                edge_array = np.array(edges)
                edge_binary = edge_array > 20
                
                # 外側領域検出（簡易版）
                height, width = edge_binary.shape
                outside_mask = np.zeros((height, width), dtype=bool)
                
                # 境界からの簡易フラッドフィル
                border_pixels = []
                # 上下端
                for x in range(0, width, 5):
                    border_pixels.extend([(x, 0), (x, height-1)])
                # 左右端
                for y in range(0, height, 5):
                    border_pixels.extend([(0, y), (width-1, y)])
                
                # 各境界ピクセルから外側領域をマーク
                from collections import deque
                visited = np.zeros((height, width), dtype=bool)
                
                for start_x, start_y in border_pixels:
                    if visited[start_y, start_x] or edge_binary[start_y, start_x]:
                        continue
                    
                    queue = deque([(start_x, start_y)])
                    visited[start_y, start_x] = True
                    
                    while queue:
                        x, y = queue.popleft()
                        outside_mask[y, x] = True
                        
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if (0 <= nx < width and 0 <= ny < height and 
                                not visited[ny, nx] and not edge_binary[ny, nx]):
                                visited[ny, nx] = True
                                queue.append((nx, ny))
                
                # 代表色抽出
                img_array = np.array(self.original_image)[:, :, :3]
                outside_pixels = img_array[outside_mask]
                
                if len(outside_pixels) > 10:
                    # 高速色分析
                    unique_colors, counts = np.unique(outside_pixels.view(np.void), return_counts=True, axis=0)
                    most_common_indices = np.argsort(counts)[::-1][:5]
                    
                    colors = []
                    points = []
                    
                    for idx in most_common_indices:
                        color_bytes = unique_colors[idx].view(np.uint8).reshape(-1, 3)[0]
                        color_int = [int(c) for c in color_bytes]
                        colors.append(color_int)
                        
                        mask_indices = np.where(outside_mask)
                        if len(mask_indices[0]) > 0:
                            points.append((mask_indices[1][0], mask_indices[0][0]))
                    
                    return colors, points
                else:
                    return None, None
                    
            except Exception as e:
                return None, str(e)
        
        def _apply_colors(result):
            colors, points = result
            if colors:
                self.target_colors = colors
                self.click_points = points
                self.update_color_list_display()
                self.status_var.set(f"輪郭外の{len(colors)}色を高速選択しました")
            elif points:  # エラーの場合
                messagebox.showerror("エラー", f"輪郭検出エラー: {points}")
            else:
                messagebox.showinfo("情報", "輪郭外の領域が検出できませんでした")
            self.hide_progress()
        
        # 非同期実行
        future = self.executor.submit(_detect)
        
        def check_result():
            if future.done():
                try:
                    result = future.result()
                    _apply_colors(result)
                except Exception as e:
                    messagebox.showerror("エラー", f"処理エラー: {e}")
                    self.hide_progress()
            else:
                self.root.after(100, check_result)
        
        self.root.after(100, check_result)
    
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
                save_image = self.processed_image.copy()
                save_image.save(file_path, "PNG")
                messagebox.showinfo("完了", f"画像を保存しました: {os.path.basename(file_path)}")
                self.status_var.set(f"保存完了: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました: {e}")
    
    def convert_mp4_to_gif(self):
        """MP4をGIFに変換"""
        # MP4ファイル選択
        mp4_path = filedialog.askopenfilename(
            title="MP4ファイルを選択",
            filetypes=[("MP4 files", "*.mp4"), ("All video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        
        if not mp4_path:
            return
        
        # 設定ダイアログ
        self.show_mp4_to_gif_dialog(mp4_path)
    
    def show_mp4_to_gif_dialog(self, mp4_path):
        """MP4→GIF変換設定ダイアログ"""
        dialog = tk.Toplevel(self.root)
        dialog.title("MP4→GIF変換設定")
        dialog.geometry("400x500")
        dialog.resizable(False, False)
        
        # ファイル情報表示
        ttk.Label(dialog, text=f"入力ファイル: {os.path.basename(mp4_path)}", 
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        # 設定フレーム
        settings_frame = ttk.LabelFrame(dialog, text="変換設定")
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 画質設定
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="画質:").pack(side=tk.LEFT)
        quality_var = tk.StringVar(value="middle")
        ttk.Radiobutton(quality_frame, text="高画質", variable=quality_var, value="high").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(quality_frame, text="中画質", variable=quality_var, value="middle").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(quality_frame, text="低画質", variable=quality_var, value="low").pack(side=tk.LEFT, padx=5)
        
        # サイズ設定
        size_frame = ttk.Frame(settings_frame)
        size_frame.pack(fill=tk.X, pady=5)
        ttk.Label(size_frame, text="サイズ:").pack(side=tk.LEFT)
        size_var = tk.StringVar(value="50")
        ttk.Radiobutton(size_frame, text="100%", variable=size_var, value="100").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(size_frame, text="50%", variable=size_var, value="50").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(size_frame, text="25%", variable=size_var, value="25").pack(side=tk.LEFT, padx=5)
        
        # フレームレート設定
        fps_frame = ttk.Frame(settings_frame)
        fps_frame.pack(fill=tk.X, pady=5)
        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT)
        fps_var = tk.IntVar(value=10)
        ttk.Scale(fps_frame, from_=5, to=30, variable=fps_var, orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=5)
        fps_label = ttk.Label(fps_frame, textvariable=fps_var)
        fps_label.pack(side=tk.LEFT)
        
        # 時間範囲設定
        time_frame = ttk.LabelFrame(settings_frame, text="時間範囲（秒）")
        time_frame.pack(fill=tk.X, pady=5)
        
        start_frame = ttk.Frame(time_frame)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="開始:").pack(side=tk.LEFT)
        start_var = tk.DoubleVar(value=0.0)
        ttk.Entry(start_frame, textvariable=start_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(start_frame, text="秒").pack(side=tk.LEFT)
        
        end_frame = ttk.Frame(time_frame)
        end_frame.pack(fill=tk.X, pady=2)
        ttk.Label(end_frame, text="終了:").pack(side=tk.LEFT)
        end_var = tk.DoubleVar(value=0.0)
        end_entry = ttk.Entry(end_frame, textvariable=end_var, width=10)
        end_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(end_frame, text="秒 (0=最後まで)").pack(side=tk.LEFT)
        
        # プレビューエリア
        preview_frame = ttk.LabelFrame(dialog, text="プレビュー")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        preview_label = ttk.Label(preview_frame, text="変換後にプレビューが表示されます")
        preview_label.pack(expand=True)
        
        # ボタンフレーム
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def start_conversion():
            """変換開始"""
            try:
                dialog.config(cursor="wait")
                
                # 設定取得
                quality = quality_var.get()
                size_percent = int(size_var.get())
                fps = fps_var.get()
                start_time = start_var.get()
                end_time = end_var.get() if end_var.get() > 0 else None
                
                # 保存先選択
                output_path = filedialog.asksaveasfilename(
                    title="GIFファイルを保存",
                    defaultextension=".gif",
                    filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
                )
                
                if output_path:
                    self.convert_video_to_gif_threaded(mp4_path, output_path, quality, size_percent, fps, start_time, end_time, dialog, preview_label)
                else:
                    dialog.config(cursor="")
                    
            except Exception as e:
                dialog.config(cursor="")
                messagebox.showerror("エラー", f"変換設定エラー: {e}")
        
        ttk.Button(button_frame, text="変換開始", command=start_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def convert_video_to_gif_threaded(self, input_path, output_path, quality, size_percent, fps, start_time, end_time, dialog, preview_label):
        """動画→GIF変換（スレッド版）"""
        def _convert():
            try:
                # プログレス表示
                dialog.after(0, lambda: preview_label.config(text="変換中... しばらくお待ちください"))
                
                # moviepyを使用した高品質変換
                try:
                    from moviepy.editor import VideoFileClip
                    moviepy_available = True
                except ImportError:
                    moviepy_available = False
                
                if moviepy_available:
                    # moviepy使用（高品質）
                    result = self._convert_with_moviepy(input_path, output_path, quality, size_percent, fps, start_time, end_time)
                else:
                    # PIL使用（軽量版）
                    result = self._convert_with_pil(input_path, output_path, quality, size_percent, fps, start_time, end_time)
                
                if result:
                    # 成功時のプレビュー表示
                    dialog.after(0, lambda: self._show_gif_preview(output_path, preview_label))
                    dialog.after(0, lambda: messagebox.showinfo("完了", f"GIF変換完了!\n{os.path.basename(output_path)}"))
                else:
                    dialog.after(0, lambda: messagebox.showerror("エラー", "変換に失敗しました"))
                
                dialog.after(0, lambda: dialog.config(cursor=""))
                
            except Exception as e:
                dialog.after(0, lambda: messagebox.showerror("エラー", f"変換エラー: {e}"))
                dialog.after(0, lambda: dialog.config(cursor=""))
        
        # バックグラウンドで実行
        self.executor.submit(_convert)
    
    def _convert_with_moviepy(self, input_path, output_path, quality, size_percent, fps, start_time, end_time):
        """moviepyを使用した変換"""
        from moviepy.editor import VideoFileClip
        
        # 動画読み込み
        clip = VideoFileClip(input_path)
        
        # 時間範囲指定
        if start_time > 0 or end_time:
            end = end_time if end_time else clip.duration
            clip = clip.subclip(start_time, end)
        
        # サイズ調整
        if size_percent != 100:
            scale = size_percent / 100.0
            clip = clip.resize(scale)
        
        # 品質設定
        if quality == "high":
            clip = clip.resize(height=min(clip.h, 480))  # 最大480p
        elif quality == "middle":
            clip = clip.resize(height=min(clip.h, 320))  # 最大320p
        else:  # low
            clip = clip.resize(height=min(clip.h, 240))  # 最大240p
        
        # GIF出力
        clip.write_gif(output_path, fps=fps, opt='nq')
        clip.close()
        
        return True
    
    def _convert_with_pil(self, input_path, output_path, quality, size_percent, fps, start_time, end_time):
        """PILを使用した軽量版変換"""
        try:
            import cv2
        except ImportError:
            messagebox.showerror("エラー", "OpenCVがインストールされていません\npip install opencv-python")
            return False
        
        # 動画読み込み
        cap = cv2.VideoCapture(input_path)
        
        if not cap.isOpened():
            return False
        
        # フレーム情報取得
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 開始・終了フレーム計算
        start_frame = int(start_time * video_fps) if start_time > 0 else 0
        end_frame = int(end_time * video_fps) if end_time else total_frames
        
        frames = []
        frame_count = 0
        
        # フレーム間隔計算
        frame_interval = max(1, int(video_fps / fps))
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        while frame_count < (end_frame - start_frame):
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # BGR → RGB変換
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # PIL Imageに変換
                pil_image = Image.fromarray(frame_rgb)
                
                # サイズ調整
                if size_percent != 100:
                    width, height = pil_image.size
                    new_width = int(width * size_percent / 100)
                    new_height = int(height * size_percent / 100)
                    pil_image = pil_image.resize((new_width, new_height), LANCZOS)
                
                # 品質調整
                if quality == "low":
                    # 色数削減
                    pil_image = pil_image.quantize(colors=64)
                    pil_image = pil_image.convert('RGB')
                
                frames.append(pil_image)
            
            frame_count += 1
        
        cap.release()
        
        if frames:
            # GIF保存
            duration = int(1000 / fps)  # ミリ秒
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration,
                loop=0
            )
            return True
        
        return False
    
    def _show_gif_preview(self, gif_path, preview_label):
        """GIFプレビュー表示"""
        try:
            # GIFの最初のフレームを表示
            gif_image = Image.open(gif_path)
            gif_image.thumbnail((200, 200), LANCZOS)
            
            photo = ImageTk.PhotoImage(gif_image)
            preview_label.config(image=photo, text="")
            preview_label.image = photo  # 参照保持
            
        except Exception as e:
            preview_label.config(text=f"プレビューエラー: {e}")
    
    def __del__(self):
        """デストラクタ"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
    
    def run(self):
        """アプリケーション実行"""
        try:
            self.root.mainloop()
        finally:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)

if __name__ == "__main__":
    app = BackgroundRemoverOptimized()
    app.run()