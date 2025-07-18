# ファイル整理基準ガイド

## 整理日: 2025-07-17

## 整理の基本方針

1. **フォルダ構成が重要なアプリケーションは触らない**
   - 既存のフォルダ（romaji_converter/, tetris/, todo_app/, work/）はそのまま維持
   - これらは内部構成が動作に必要なため移動しない

2. **散らばっている単体ファイルを機能別に整理**
   - ルートディレクトリに散在するファイルのみを対象とする
   - 機能が似ているものをグループ化

## フォルダ構成と分類基準

### desktop_apps/ - デスクトップアプリケーション
GUI要素を持ち、デスクトップ上で動作するアプリケーション

#### desktop_pet/ - デスクトップペット系
- **分類基準**: デスクトップ上を動き回るマスコット・ペットアプリ
- **含まれるファイル**:
  - desktop_pet.py - 機能充実版（右クリックメニュー、サイズ変更機能付き）
  - transparent_pet.py - 透過対応版（GIFアニメーション対応）
  - desktop_pet_wandering.py - Windows専用高機能版（ウィンドウ認識機能付き）

#### image_animator/ - 画像アニメーター系
- **分類基準**: 静止画像をアニメーション表示するツール
- **含まれるファイル**:
  - image_animator.py - 基本版
  - image_animator_debug.py - デバッグ機能付き版
  - image_animator_v0.2.py - 品質改善版

### tools/ - ユーティリティツール
特定の処理を行うためのツール群

#### background_remover/ - 背景除去ツール
- **分類基準**: 画像から背景を除去・透過処理を行うツール
- **含まれるファイル**:
  - background_remover.py - 最新版（GUI付き）
  - background_remover_optimized.py - 高速化版
  - background_remover_v1_backup.py - バックアップ版

#### video_tools/ - 動画処理ツール
- **分類基準**: 動画ファイルの変換・処理を行うツール
- **含まれるファイル**:
  - mp4_to_gif.py - MP4→GIF変換ツール
  - video_to_transparent_gif.py - 動画→透過GIF変換ツール

### test/ - テスト・サンプルファイル
- **分類基準**: テスト用コード、サンプルデータ生成スクリプト
- **含まれるファイル**:
  - hello.py - 最小限のテストスクリプト
  - create_test_gif.py - テスト用GIF生成
  - create_test_mp4.py - テスト用MP4フレーム生成
  - test_*.gif, test_*.png - 生成されたテストファイル

## バージョン管理の方針

1. **最新版のファイル名はシンプルに**
   - 例: background_remover.py（最新版）

2. **古いバージョンは明示的に表記**
   - 例: background_remover_v1_backup.py（バックアップ）
   - 例: background_remover_optimized.py（特別版）

3. **デバッグ版は_debugを付ける**
   - 例: image_animator_debug.py

## 今後のファイル追加時の指針

1. **新しいデスクトップアプリ** → desktop_apps/の下に新規フォルダ
2. **新しいツール** → tools/の下に機能別フォルダ
3. **テストコード** → test/に配置
4. **フォルダ構成が必要なアプリ** → ルートに独立したフォルダとして作成

## 注意事項

- node_modules/を含むプロジェクトは移動時に注意（サイズが大きい）
- .db（データベース）ファイルは関連ファイルと一緒に移動
- dict/のような辞書フォルダは必ず維持する