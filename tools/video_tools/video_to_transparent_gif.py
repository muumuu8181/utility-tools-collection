#!/usr/bin/env python3

import cv2
import numpy as np
from PIL import Image
import os
from pathlib import Path
import sys

def detect_background_color(frame):
    """動画の背景色を自動検出（フレームの端の最頻値色）"""
    h, w = frame.shape[:2]
    
    # 端の領域を取得
    border_pixels = []
    border_pixels.extend(frame[0, :].reshape(-1, 3))  # 上端
    border_pixels.extend(frame[-1, :].reshape(-1, 3))  # 下端
    border_pixels.extend(frame[:, 0].reshape(-1, 3))  # 左端
    border_pixels.extend(frame[:, -1].reshape(-1, 3))  # 右端
    
    border_pixels = np.array(border_pixels)
    
    # 最頻値の色を見つける
    unique_colors, counts = np.unique(border_pixels.reshape(-1, 3), axis=0, return_counts=True)
    bg_color = unique_colors[np.argmax(counts)]
    
    print(f"検出された背景色: BGR{tuple(bg_color)}")
    return bg_color

def remove_background_from_video(video_path, output_dir="transparent_frames", bg_color=None):
    """
    動画から背景を除去して透過PNG連番を作成
    
    Args:
        video_path: 入力動画ファイル
        output_dir: 出力ディレクトリ
        bg_color: 削除する背景色 [B,G,R] (Noneの場合は緑背景を自動検出)
    """
    
    # 出力ディレクトリ作成
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"エラー: 動画を開けません: {video_path}")
        return False
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"動画情報: {fps:.1f}fps, {total_frames}フレーム")
    print("背景除去処理を開始...")
    
    frame_count = 0
    saved_count = 0
    
    # フレームスキップ設定（30fps→10fpsなど）
    target_fps = 10
    frame_skip = max(1, int(fps / target_fps))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 最初のフレームで自動検出
        if frame_count == 0 and bg_color == "auto":
            bg_color = detect_background_color(frame)
            
        # フレームスキップ
        if frame_count % frame_skip == 0:
            # 背景除去処理
            if bg_color is None:
                # 緑背景（クロマキー）を想定
                result = remove_green_background(frame, preview=(saved_count == 0))
            elif isinstance(bg_color, str) and bg_color == "auto":
                # 自動検出された色を除去
                continue  # 既に検出済み
            else:
                # 指定色を除去
                result = remove_specific_color(frame, bg_color, threshold=50)
            
            # 透過PNG保存
            output_file = output_path / f"frame_{saved_count:04d}.png"
            cv2.imwrite(str(output_file), result)
            saved_count += 1
            
            if saved_count % 10 == 0:
                print(f"  {saved_count}フレーム処理済み...")
        
        frame_count += 1
    
    cap.release()
    
    print(f"\n完了！ {saved_count}枚の透過PNGを作成しました")
    print(f"出力先: {output_path}")
    
    # GIF変換オプション
    create_gif = input("\nGIFアニメーションを作成しますか？ (y/n) [y]: ").lower() or "y"
    if create_gif == "y":
        create_transparent_gif(output_path, fps=target_fps)
    
    return True

def remove_green_background(frame, preview=False):
    """緑背景を透過にする（クロマキー）"""
    # BGRからHSVに変換
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 緑色の範囲を定義（より広い範囲に調整）
    lower_green = np.array([35, 30, 30])    # より低い閾値
    upper_green = np.array([85, 255, 255])  # より高い閾値
    
    # マスク作成
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # ノイズ除去
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # プレビュー表示（デバッグ用）
    if preview:
        cv2.imshow("Original", cv2.resize(frame, (400, 300)))
        cv2.imshow("Mask", cv2.resize(mask, (400, 300)))
        cv2.waitKey(1)
    
    # マスクを反転（緑以外を残す）
    mask_inv = cv2.bitwise_not(mask)
    
    # アルファチャンネル付きの画像作成
    b, g, r = cv2.split(frame)
    rgba = cv2.merge([b, g, r, mask_inv])
    
    return rgba

def remove_specific_color(frame, bg_color, threshold=30):
    """特定の色を透過にする"""
    # 色の差分を計算
    diff = cv2.absdiff(frame, bg_color)
    
    # 閾値以下の領域をマスク
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    # アルファチャンネル付きの画像作成
    b, g, r = cv2.split(frame)
    rgba = cv2.merge([b, g, r, mask])
    
    return rgba

def create_transparent_gif(frames_dir, output_name="animated_character.gif", fps=10):
    """透過PNGからGIFアニメーションを作成"""
    frames_path = Path(frames_dir)
    
    # PNG画像を読み込み
    images = []
    for png_file in sorted(frames_path.glob("*.png")):
        img = Image.open(png_file)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        images.append(img)
    
    if not images:
        print("画像が見つかりません")
        return
    
    print(f"\n{len(images)}枚の画像からGIFを作成中...")
    
    # GIF保存
    duration = int(1000 / fps)  # ミリ秒
    
    images[0].save(
        output_name,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        disposal=2,  # 前のフレームをクリア
        optimize=True
    )
    
    file_size = os.path.getsize(output_name) / 1024 / 1024
    print(f"GIF作成完了: {output_name} ({file_size:.1f}MB)")

def create_character_animation():
    """画像素材からキャラクターアニメーションを作成"""
    print("=== キャラクターアニメーション作成 ===")
    print("\n準備するもの:")
    print("1. キャラクターの連番画像（透過PNG推奨）")
    print("2. または、キャラクターのポーズ違い画像")
    print("3. または、パーツ画像（目、口、体など）")
    
    choice = input("\nどの方法で作成しますか？\n1. 連番画像から\n2. ポーズ画像から\n3. パーツ合成\n選択 [1]: ") or "1"
    
    if choice == "1":
        # 連番画像からGIF作成
        frames_dir = input("画像フォルダのパス: ").strip()
        if os.path.exists(frames_dir):
            create_transparent_gif(frames_dir)
    
    elif choice == "2":
        # ポーズ画像からアニメーション
        print("\n実装予定: 各ポーズを順番に表示してアニメーション化")
        
    elif choice == "3":
        # パーツ合成アニメーション
        print("\n実装予定: 目パチ、口パクなどを合成してアニメーション化")

def get_video_folders():
    """よく使うフォルダのリスト"""
    folders = [
        Path.home() / "work" / "90_mp4",
        Path.home() / "Videos",
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path.cwd(),
    ]
    return [f for f in folders if f.exists()]

def select_video_file():
    """フォルダと動画ファイルを選択"""
    print("=== 動画→透過GIF変換ツール ===\n")
    
    # フォルダ選択
    folders = get_video_folders()
    print("📁 フォルダを選択:")
    for i, folder in enumerate(folders, 1):
        video_count = len(list(folder.glob("*.mp4")) + list(folder.glob("*.MP4")) + 
                         list(folder.glob("*.avi")) + list(folder.glob("*.mov")))
        print(f"{i}. {folder} ({video_count}個の動画)")
    
    print(f"{len(folders) + 1}. カスタムフォルダ")
    print("0. 終了")
    
    while True:
        try:
            choice = int(input("\n番号を入力: "))
            if choice == 0:
                return None, None
            elif 1 <= choice <= len(folders):
                selected_folder = folders[choice - 1]
                break
            elif choice == len(folders) + 1:
                custom = input("フォルダパス: ").strip()
                selected_folder = Path(custom)
                if not selected_folder.exists():
                    print("❌ フォルダが存在しません")
                    continue
                break
        except ValueError:
            print("❌ 数字を入力してください")
    
    # 動画ファイル一覧
    videos = []
    for ext in ["*.mp4", "*.MP4", "*.avi", "*.mov", "*.mkv"]:
        videos.extend(selected_folder.glob(ext))
    
    if not videos:
        print("❌ 動画ファイルが見つかりません")
        return None, None
    
    print(f"\n📹 動画ファイルを選択:")
    for i, video in enumerate(sorted(videos), 1):
        size_mb = video.stat().st_size / 1024 / 1024
        print(f"{i}. {video.name} ({size_mb:.1f}MB)")
    
    while True:
        try:
            choice = int(input("\n番号を入力: "))
            if 1 <= choice <= len(videos):
                return sorted(videos)[choice - 1], selected_folder
        except ValueError:
            print("❌ 数字を入力してください")

def select_background_mode():
    """背景除去モードを選択"""
    print("\n🎨 背景除去モード:")
    print("1. 自動検出（背景色を自動判定）")
    print("2. 緑背景（クロマキー）")
    print("3. 白背景")
    print("4. 黒背景")
    print("5. カスタム色指定")
    
    while True:
        try:
            choice = int(input("\n番号を入力 [1]: ") or "1")
            if choice == 1:
                return "auto"  # 自動検出
            elif choice == 2:
                return None  # 緑背景
            elif choice == 3:
                return [255, 255, 255]  # 白
            elif choice == 4:
                return [0, 0, 0]  # 黒
            elif choice == 5:
                rgb = input("RGB値をカンマ区切りで入力 (例: 255,0,0): ")
                colors = rgb.split(",")
                return [int(colors[2]), int(colors[1]), int(colors[0])]  # RGB→BGR
        except:
            print("❌ 正しく入力してください")

def main():
    if len(sys.argv) > 1:
        # コマンドライン引数がある場合は従来の動作
        if sys.argv[1] == "--create":
            create_character_animation()
        else:
            video_path = sys.argv[1]
            bg_color = None
            if len(sys.argv) > 3 and sys.argv[2] == "--bg":
                try:
                    colors = sys.argv[3].split(",")
                    bg_color = [int(colors[2]), int(colors[1]), int(colors[0])]
                except:
                    print("背景色の指定が正しくありません")
            remove_background_from_video(video_path, bg_color=bg_color)
    else:
        # 引数なしの場合は対話モード
        print("1. 動画から透過GIF作成")
        print("2. 画像からアニメーション作成")
        
        mode = input("\n選択 [1]: ") or "1"
        
        if mode == "2":
            create_character_animation()
        else:
            # 動画選択
            video_path, folder = select_video_file()
            if not video_path:
                return
            
            # 背景モード選択
            bg_color = select_background_mode()
            
            # 出力先
            output_dir = folder / "transparent_frames"
            
            # 変換実行
            remove_background_from_video(str(video_path), str(output_dir), bg_color)

if __name__ == "__main__":
    main()