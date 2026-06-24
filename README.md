# VibeCode Translator ✦

**版本：2.0.2** · [下載 .app](https://github.com/louisty2006/VibeCode_Translator/releases) · [更新紀錄](CHANGELOG.md)

**把任何程式碼，翻譯成你聽得懂的語言。**

VibeCode Translator 是一款 macOS 選單列工具。你在任何 App 裡反白一段程式碼，按下快捷鍵，就會在游標旁彈出一個浮動視窗，用自然語言（英文或繁體中文）解釋這段 code 在做什麼、邏輯怎麼運作。

專為 **vibe coder**、非工程師、或正在學程式的人設計——不需要離開你正在用的編輯器或瀏覽器。

---

## 快速開始：我該用哪種安裝方式？

| 你是… | 推薦方式 | 需要做什麼 |
|--------|----------|------------|
| **同事 / 非工程師** | **方式 A：下載 `.app`** | 下載 → 拖到應用程式 → 雙擊 → 開權限 → 填 API Key |
| **會用終端機的開發者** | **方式 B：原始碼** | `git clone` → `./setup.sh` → `./run.sh` |
| **要打包給別人** | **方式 C：自己 build** | `./build_app.sh` → 分享 `dist/` 裡的 `.app` |

> **常見錯誤：** `git clone` 後直接 `python main.py` 會報 `No module named 'rumps'`。一定要先跑 `./setup.sh`（或手動 `pip install`），或改用 `.app` 版本。

---

## 這個 App 解決什麼問題？

用 AI 寫 code 越來越普遍，但很多人看到產出的程式碼時仍然一頭霧水：

- 這段 `async/await` 到底在等什麼？
- `reduce` 和 `map` 有什麼差別？
- 為什麼要 import 這麼多東西？

VibeCode Translator 讓你 **選取 → 解釋**，不用複製貼上到 ChatGPT，也不用切換視窗。解釋會以生活化的比喻呈現，假設你完全沒有程式背景。

---

## 功能一覽

| 功能 | 說明 |
|------|------|
| **全域快捷鍵** | 預設 `Cmd + Control + E`，可在 Settings 自訂，在任何 App 都有效 |
| **右鍵選單** | 右鍵點擊可選擇「✦ Explain Code」 |
| **浮動解釋氣泡** | 解釋視窗出現在游標旁，可拖曳、可捲動 |
| **多 AI 供應商** | Claude、GPT、Gemini、Groq、DeepSeek、Ollama 等 12 種 |
| **雙語解釋** | 英文或繁體中文 |
| **自備 API Key** | 用你的 Key，費用直接付給 AI 供應商 |
| **本機模型** | 支援 Ollama，完全離線、免 API Key |

---

## 系統需求

| 安裝方式 | 需要什麼 |
|----------|----------|
| **方式 A（.app）** | macOS 12+（Sonoma / Sequoia 已測試）、網路（雲端 AI） |
| **方式 B / C（原始碼）** | 以上 + **Python 3.11+**（建議 Homebrew 安裝） |

---

## 安裝與啟動

### 方式 A：下載 `.app`（推薦給同事）⭐

**不需要 Python、venv 或 pip。**

#### 安裝步驟

1. 到 [GitHub Releases](https://github.com/louisty2006/VibeCode_Translator/releases) 下載最新版的 `VibeCode-Translator-*-macOS-arm64.zip`
2. 解壓縮，將 `VibeCode Translator.app` **拖到「應用程式」資料夾**
3. **雙擊開啟**
   - 若 macOS 提示「無法驗證開發者」→ **系統設定 → 隱私權與安全性 → 仍要開啟**
4. **授予輔助使用權限**（必要，否則快捷鍵無效）
   - **系統設定 → 隱私權與安全性 → 輔助使用**
   - 啟用 **VibeCode Translator**（不是 Terminal）
   - 完全退出 App 後重新開啟
5. 選單列右上角出現 **✦** → 點 **⚙️ Settings** → 填入 API Key 與語言

#### 安裝檢查清單

```
□ 已解壓並放到「應用程式」
□ 已雙擊開啟（通過「仍要開啟」）
□ 輔助使用已啟用「VibeCode Translator」
□ 選單列有 ✦ 圖示
□ Settings 已填入 API Key
□ 反白 code 後按 Cmd+Control+E 有氣泡出現
```

---

### 方式 B：從原始碼執行（開發者）

#### 一鍵安裝（推薦）

```bash
git clone https://github.com/louisty2006/VibeCode_Translator.git
cd VibeCode_Translator
./setup.sh      # 建立 venv + 安裝依賴（只需跑一次）
./run.sh        # 啟動 App
```

#### 手動安裝

```bash
git clone https://github.com/louisty2006/VibeCode_Translator.git
cd VibeCode_Translator

python3 -m venv venv
source venv/bin/activate          # 終端機應顯示 (venv)
pip install -r requirements.txt   # 必做！否則會缺 rumps、AppKit
python main.py
```

> **注意：**
> - clone 後**不能**直接 `python main.py`，一定要先 `./setup.sh` 或 `pip install`
> - 每次**新開終端機**要再跑：`cd VibeCode_Translator && ./run.sh`
> - 看到 `(venv)` 代表環境正確；沒有 `(venv)` 就容易裝錯地方

#### 安裝檢查清單

```
□ 已 cd 進 VibeCode_Translator
□ 已跑 ./setup.sh（或 pip install -r requirements.txt）
□ ./run.sh 後選單列有 ✦
□ 輔助使用已啟用 Terminal 或 Python（見下方權限說明）
```

啟動後首次會自動開啟設定視窗。

---

### 方式 C：自己打包 `.app`（開發者）

在 macOS 上執行：

```bash
cd VibeCode_Translator
./build_app.sh
```

完成後產生 `dist/VibeCode Translator.app`，可：

```bash
open "dist/VibeCode Translator.app"
```

將 `.app` 壓縮後分享給同事，或上傳至 GitHub Releases。

**需求：** macOS、Python 3.11+（腳本會自動建立 `.build-venv` 並安裝 py2app）

---

### 發布新版本（維護者）

原始碼與打包版必須同步更新：`dist/` 不進 git，同事從 **GitHub Releases** 下載 `.app`。

**前置條件：** macOS、`gh auth login`、變更已 commit

1. 更新 [`CHANGELOG.md`](CHANGELOG.md)，並撰寫 `RELEASE_NOTES_X.Y.Z.md`
2. 執行一鍵發布（會自動 bump `setup.py` 版本、build、zip、建立 Release）：

```bash
./release.sh X.Y.Z --notes RELEASE_NOTES_X.Y.Z.md
```

3. 到 GitHub Releases 確認 zip 可下載；可本地驗證：

```bash
open "dist/VibeCode Translator.app"
```

發布前建議先用 `./run.sh` 快速驗證原始碼路徑。

---

## 設定說明

點選選單列 **✦ → ⚙️ Settings** 開啟設定視窗。

| 欄位 | 說明 |
|------|------|
| **AI Provider** | 選擇 AI 供應商（見下方列表） |
| **API Key** | 你的 API 金鑰（Ollama 可留空） |
| **Model（選填）** | 覆寫預設模型名稱，留空則用內建預設值 |
| **Explanation Language** | 解釋語言：English 或 繁體中文 |
| **Global Shortcut** | 點 **Record Shortcut** 錄製自訂快捷鍵（預設 `⌘⌃E`） |

設定會儲存至 `~/.vibecode_translator_settings.json`。

若你曾使用舊版 VibeCode Reader，程式會自動讀取 `~/.vibecode_reader_settings.json`，下次儲存時遷移至新路徑。

---

## 支援的 AI 供應商

| Provider | 預設模型 | API Key 取得 |
|----------|----------|--------------|
| Claude (Anthropic) | claude-sonnet-4-6 | [console.anthropic.com](https://console.anthropic.com) |
| GPT (OpenAI) | gpt-4o | [platform.openai.com](https://platform.openai.com) |
| OpenRouter | anthropic/claude-sonnet-4 | [openrouter.ai](https://openrouter.ai) |
| Gemini (Google) | gemini-2.0-flash | [aistudio.google.com](https://aistudio.google.com) |
| Groq | llama-3.3-70b-versatile | [console.groq.com](https://console.groq.com) |
| Mistral AI | mistral-large-latest | [console.mistral.ai](https://console.mistral.ai) |
| DeepSeek | deepseek-chat | [platform.deepseek.com](https://platform.deepseek.com) |
| Cohere | command-r-plus-08-2024 | [dashboard.cohere.com](https://dashboard.cohere.com) |
| Together AI | Meta-Llama-3.1-70B | [api.together.xyz](https://api.together.xyz) |
| Grok (xAI) | grok-2-latest | [console.x.ai](https://console.x.ai) |
| Fireworks AI | llama-v3p1-70b-instruct | [fireworks.ai](https://fireworks.ai) |
| **Ollama（本機）** | llama3.2 | 不需 Key，需先安裝 [Ollama](https://ollama.com) |

### 使用 Ollama（本機、免費）

```bash
# 安裝 Ollama 後拉取模型
ollama pull llama3.2

# 確認服務運行中
ollama serve
```

在設定中選擇 **Ollama (Local)**，API Key 留空即可。

---

## macOS 權限設定

App 需要權限才能監聽快捷鍵、讀取反白文字。

### 輔助使用（Accessibility）— 必要

| 你用的安裝方式 | 在輔助使用清單中啟用 |
|----------------|----------------------|
| **方式 A（.app）** | **VibeCode Translator** |
| **方式 B（終端機）** | **Terminal**，以及 **Python** / **Python.app**（Homebrew） |

**設定步驟：**

1. **系統設定 → 隱私權與安全性 → 輔助使用**
2. 依上表啟用對應項目；清單中沒有就點 **+** 手動加入
3. 用終端機啟動時，可查 Python 路徑：

```bash
which python    # 在 venv 啟用後執行
```

4. **完全退出並重新啟動** App

也可透過選單列 **✦ → 🔓 Enable Shortcut** 開啟引導。

### 輸入監控（Input Monitoring）— 建議

部分 macOS 版本需額外開啟：**系統設定 → 隱私權與安全性 → 輸入監控**（同樣啟用 VibeCode Translator 或 Terminal）。

---

## 使用方式

1. 在任何 App 中 **反白一段程式碼**
2. 按 **`Cmd + Control + E`**（或你在 Settings 設定的快捷鍵）
   - 或右鍵 → **✦ Explain Code**
3. 等待氣泡出現（顯示「⏳ Analyzing...」）
4. 閱讀解釋，點 **✕** 關閉氣泡

### 解釋內容包含

- **一句話總結**：這段 code 在做什麼
- **步驟說明**：邏輯如何運作
- **生活化比喻**：關鍵概念用日常例子解釋

### 選單列功能

| 選項 | 功能 |
|------|------|
| ⚙️ Settings | 開啟設定視窗 |
| 🔓 Enable Shortcut | 輔助使用權限引導 |
| 📖 Help | 快速使用說明 |
| Quit VibeCode Translator | 退出 App |

---

## 專案結構

```
VibeCode_Translator/
├── main.py                 # 入口：選單列 App、快捷鍵、設定視窗
├── explainer.py            # LLM 呼叫與解釋 prompt
├── bubble.py               # 浮動解釋氣泡 UI
├── providers.py            # AI 供應商設定
├── hotkey.py               # 快捷鍵解析、顯示與比對
├── ui_theme.py             # Glassmorphism 共用視覺樣式
├── settings.py             # 讀寫使用者設定
├── setup.py                # py2app 打包設定
├── setup.sh                # 一鍵安裝（原始碼方式）
├── run.sh                  # 一鍵啟動（原始碼方式）
├── build_app.sh            # 一鍵打包 .app
├── release.sh              # 一鍵發布（build + zip + GitHub Release）
├── requirements.txt        # 執行時依賴
├── requirements-build.txt  # 打包時依賴（含 py2app）
└── CHANGELOG.md            # 版本更新紀錄
```

---

## 常見問題

**Q: `No module named 'rumps'` 或 `AppKit`？**  
從原始碼執行時，先啟用 venv 並執行 `pip install -r requirements.txt`。或改用 `.app` 版本，無需手動安裝。

**Q: macOS 說「無法驗證開發者」？**  
未簽名的 `.app` 會出現此提示。到 **系統設定 → 隱私權與安全性** 點「仍要開啟」。

**Q: 按快捷鍵沒反應？**  
確認已授予輔助使用權限，並重新啟動 App。選單列點 **🔓 Enable Shortcut** 檢查。

**Q: 顯示「Please highlight some code first」？**  
請先反白文字再按快捷鍵。App 透過模擬複製讀取選取內容。

**Q: 顯示「Please enter your API Key」？**  
開啟 **⚙️ Settings** 填入 API Key（Ollama 除外）。

**Q: `python3 main.py` 找不到檔案？**  
你目前不在專案目錄。先執行 `cd` 進入資料夾再啟動。

**Q: API 錯誤？**  
檢查 Key 是否正確、帳戶是否有餘額、模型名稱是否有效。

---

## 貢獻

歡迎 Pull Request 與 Issue！

## 授權

MIT License
