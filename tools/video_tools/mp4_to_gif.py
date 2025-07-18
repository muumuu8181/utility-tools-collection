#!/usr/bin/env python3

import sys
import os
from PIL import Image
import cv2
import numpy as np
from pathlib import Path

def get_video_folders():
    """よく使うビデオフォルダのリストを返す"""
    folders = [
        Path.home() / "work" / "90_mp4",  # 追加
        Path.home() / "Videos",
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Pictures",
        Path.cwd(),  # 現在のディレクトリ
    ]
    
    # 存在するフォルダのみフィルタリング
    existing_folders = []
    for folder in folders:
        if folder.exists():
            existing_folders.append(folder)
    
    return existing_folders

def find_mp4_files(directory):
    """指定ディレクトリ内のMP4ファイルを検索"""
    mp4_files = []
    path = Path(directory)
    
    # 現在のディレクトリ内のMP4ファイルを検索（非再帰）
    for file in path.glob("*.mp4"):
        mp4_files.append(file)
    
    # 大文字拡張子も検索
    for file in path.glob("*.MP4"):
        if file not in mp4_files:
            mp4_files.append(file)
    
    # サブディレクトリも含める場合はrglobを使用
    # for file in path.rglob("*.mp4"):
    #     mp4_files.append(file)
    
    return sorted(mp4_files)

def mp4_to_gif(mp4_path, output_path=None, fps=10, scale=1.0, optimize=True):
    """
    MP4ファイルをGIFに変換
    
    Args:
        mp4_path: 入力MP4ファイルのパス
        output_path: 出力GIFファイルのパス（省略時は同じ場所に.gif拡張子で保存）
        fps: GIFのフレームレート（デフォルト10fps）
        scale: スケール（0.5で半分のサイズ、1.0で元のサイズ）
        optimize: GIFの最適化を行うか
    """
    
    # 入力ファイルの確認
    if not os.path.exists(mp4_path):
        print(f"エラー: ファイルが見つかりません: {mp4_path}")
        return False
    
    # 出力パスの設定
    if output_path is None:
        output_path = Path(mp4_path).with_suffix('.gif')
    
    print(f"MP4からGIFへの変換を開始します...")
    print(f"入力: {mp4_path}")
    print(f"出力: {output_path}")
    
    # ビデオキャプチャを開く
    cap = cv2.VideoCapture(str(mp4_path))
    
    if not cap.isOpened():
        print("エラー: MP4ファイルを開けませんでした")
        return False
    
    # ビデオ情報の取得
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"ビデオ情報: {video_fps:.1f}fps, {total_frames}フレーム")
    
    # フレームスキップの計算
    frame_skip = int(video_fps / fps)
    if frame_skip < 1:
        frame_skip = 1
    
    frames = []
    frame_count = 0
    processed_count = 0
    
    print(f"フレームを読み込み中... (スキップ間隔: {frame_skip})")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # フレームスキップ
        if frame_count % frame_skip == 0:
            # BGRからRGBに変換
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # PIL Imageに変換
            pil_img = Image.fromarray(frame_rgb)
            
            # リサイズ（必要な場合）
            if scale != 1.0:
                new_width = int(pil_img.width * scale)
                new_height = int(pil_img.height * scale)
                pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            frames.append(pil_img)
            processed_count += 1
            
            # 進捗表示
            if processed_count % 10 == 0:
                print(f"  {processed_count}フレーム処理済み...")
        
        frame_count += 1
    
    cap.release()
    
    if not frames:
        print("エラー: フレームを取得できませんでした")
        return False
    
    print(f"\n{len(frames)}フレームを処理しました")
    print("GIFを保存中...")
    
    # GIFとして保存
    duration = int(1000 / fps)  # ミリ秒
    
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=optimize
    )
    
    # ファイルサイズの確認
    file_size = os.path.getsize(output_path) / 1024 / 1024  # MB
    print(f"\n変換完了！")
    print(f"出力ファイル: {output_path}")
    print(f"ファイルサイズ: {file_size:.1f}MB")
    print(f"フレーム数: {len(frames)}")
    
    return True

def batch_mode():
    """バッチ変換モード"""
    print("=== MP4→GIF バッチ変換モード ===\n")
    
    # フォルダ選択
    folders = get_video_folders()
    
    print("📁 フォルダを選択してください:")
    for i, folder in enumerate(folders, 1):
        # find_mp4_files関数を使用して正確にカウント
        mp4_files = find_mp4_files(folder)
        mp4_count = len(mp4_files)
        print(f"{i}. {folder} ({mp4_count}個のMP4)")
    
    print(f"{len(folders) + 1}. カスタムフォルダを指定")
    print("0. 終了")
    
    while True:
        try:
            choice = int(input("\n番号を入力: "))
            if choice == 0:
                print("終了します")
                return
            elif 1 <= choice <= len(folders):
                selected_folder = folders[choice - 1]
                break
            elif choice == len(folders) + 1:
                custom_path = input("フォルダパスを入力: ").strip()
                selected_folder = Path(custom_path)
                if not selected_folder.exists():
                    print("❌ フォルダが存在しません")
                    continue
                break
            else:
                print("❌ 無効な番号です")
        except ValueError:
            print("❌ 数字を入力してください")
    
    # MP4ファイル検索
    print(f"\n🔍 {selected_folder} を検索中...")
    mp4_files = find_mp4_files(selected_folder)
    
    if not mp4_files:
        print("❌ MP4ファイルが見つかりませんでした")
        return
    
    print(f"\n✅ {len(mp4_files)}個のMP4ファイルが見つかりました:")
    for i, file in enumerate(mp4_files[:10], 1):
        size_mb = file.stat().st_size / 1024 / 1024
        print(f"  {i}. {file.name} ({size_mb:.1f}MB)")
    
    if len(mp4_files) > 10:
        print(f"  ... 他{len(mp4_files) - 10}個")
    
    # 変換設定
    print("\n⚙️  変換設定:")
    print("1. 高速・低画質 (FPS:10, サイズ:25%)")
    print("2. 標準 (FPS:10, サイズ:50%)")
    print("3. 高画質 (FPS:15, サイズ:75%)")
    print("4. カスタム設定")
    
    while True:
        try:
            preset = int(input("\n番号を入力 [2]: ") or "2")
            if preset == 1:
                fps, scale = 10, 0.25
                break
            elif preset == 2:
                fps, scale = 10, 0.5
                break
            elif preset == 3:
                fps, scale = 15, 0.75
                break
            elif preset == 4:
                fps = int(input("FPS (5-30) [10]: ") or "10")
                scale = float(input("スケール (0.1-1.0) [0.5]: ") or "0.5")
                fps = max(5, min(30, fps))
                scale = max(0.1, min(1.0, scale))
                break
            else:
                print("❌ 無効な番号です")
        except ValueError:
            print("❌ 数字を入力してください")
    
    # 変換実行確認
    print(f"\n📋 変換内容:")
    print(f"  ファイル数: {len(mp4_files)}個")
    print(f"  FPS: {fps}")
    print(f"  スケール: {scale * 100}%")
    
    confirm = input("\n変換を開始しますか？ (y/n) [y]: ").lower() or "y"
    if confirm != "y":
        print("キャンセルしました")
        return
    
    # 変換実行
    print("\n🚀 変換を開始します...\n")
    
    success_count = 0
    failed_files = []
    
    for i, mp4_file in enumerate(mp4_files, 1):
        print(f"\n[{i}/{len(mp4_files)}] {mp4_file.name}")
        
        try:
            success = mp4_to_gif(str(mp4_file), None, fps, scale)
            if success:
                success_count += 1
            else:
                failed_files.append(mp4_file.name)
        except Exception as e:
            print(f"❌ エラー: {e}")
            failed_files.append(mp4_file.name)
    
    # 結果表示
    print(f"\n🎉 変換完了!")
    print(f"  成功: {success_count}個")
    print(f"  失敗: {len(failed_files)}個")
    
    if failed_files:
        print("\n❌ 失敗したファイル:")
        for name in failed_files:
            print(f"  - {name}")

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        # 引数なしの場合はバッチモード
        batch_mode()
    else:
        # 引数ありの場合は従来の単一ファイルモード
        mp4_path = sys.argv[1]
        output_path = None
        fps = 10
        scale = 1.0
        optimize = True
        
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            
            if arg in ['--output', '-o'] and i + 1 < len(sys.argv):
                output_path = sys.argv[i + 1]
                i += 2
            elif arg in ['--fps', '-f'] and i + 1 < len(sys.argv):
                fps = int(sys.argv[i + 1])
                i += 2
            elif arg in ['--scale', '-s'] and i + 1 < len(sys.argv):
                scale = float(sys.argv[i + 1])
                i += 2
            elif arg == '--no-optimize':
                optimize = False
                i += 1
            else:
                print(f"警告: 不明なオプション: {arg}")
                i += 1
        
        # 変換実行
        success = mp4_to_gif(mp4_path, output_path, fps, scale, optimize)
        
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()