## VibeCode Translator 2.0.2 — 修復 .app 無法啟動

### 修復
- 修正打包版啟動時的 PyObjC 錯誤（`record:shortcut:` 方法簽名問題）
- v2.0.1 的 `.app` 若雙擊出現 Launch error，請改下載此版本

### 安裝（同事推薦）
1. 下載下方 `VibeCode-Translator-2.0.2-macOS-arm64.zip`
2. 解壓 → 拖到「應用程式」→ 雙擊
3. 若提示「無法驗證開發者」→ 系統設定 → 隱私權與安全性 → **仍要開啟**
4. 系統設定 → 輔助使用 → 啟用 **VibeCode Translator**
5. 選單列 ✦ → Settings → 填 API Key
6. 反白 code → `Cmd + Control + E`（或自訂快捷鍵）

### 開發者
```bash
git clone https://github.com/louisty2006/VibeCode_Translator.git
cd VibeCode_Translator
./setup.sh
./run.sh
```
