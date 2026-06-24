# Changelog

## 2.0.1 — 2026-06-24

- Glassmorphism UI：設定視窗與解釋氣泡視覺風格統一
- 新增共用 `ui_theme.py` 模組
- 解釋氣泡尺寸與標題列優化
- 新增 `release.sh` 一鍵發布腳本（build + zip + GitHub Release）

## MVP2 — 2026-06-24

**主打：免裝 Python，下載即用**

- 打包成獨立 macOS `.app`（py2app）
- 新增 `build_app.sh` 一鍵打包腳本
- 新增 `setup.sh` / `run.sh` 簡化原始碼安裝
- README 重寫：三種安裝路徑、常見錯誤對照表
- 專案更名為 **VibeCode Translator**（原 VibeCode Reader）
- 開源至 GitHub
- 預設快捷鍵改為 `Cmd+Control+E`（避免與 Cursor / VS Code 衝突）
- Settings 支援錄製自訂全域快捷鍵

## MVP1 — 2026-06-23

- 選單列 App + 全域快捷鍵 `Cmd+Shift+E`
- 浮動解釋氣泡（中 / 英）
- 12 個 AI Provider（含 Ollama 本機）
- Settings 視窗、Accessibility 引導
