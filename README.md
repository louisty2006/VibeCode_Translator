# VibeCode Translator ✦

**把任何程式碼，翻譯成你聽得懂的語言。**

VibeCode Translator 是一款 macOS 選單列工具。你在任何 App 裡反白一段程式碼，按下快捷鍵，就會在游標旁彈出一個浮動視窗，用自然語言（英文或繁體中文）解釋這段 code 在做什麼、邏輯怎麼運作。

專為 **vibe coder**、非工程師、或正在學程式的人設計——不需要離開你正在用的編輯器或瀏覽器。

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
| **全域快捷鍵** | `Cmd + Shift + E`，在任何 App 都有效 |
| **右鍵選單** | 右鍵點擊可選擇「✦ Explain Code」 |
| **浮動解釋氣泡** | 解釋視窗出現在游標旁，可拖曳、可捲動 |
| **多 AI 供應商** | Claude、GPT、Gemini、Groq、DeepSeek、Ollama 等 12 種 |
| **雙語解釋** | 英文或繁體中文 |
| **自備 API Key** | 用你的 Key，費用直接付給 AI 供應商 |
| **本機模型** | 支援 Ollama，完全離線、免 API Key |

---

## 系統需求

- **macOS**（已測試 Sonoma / Sequoia）
- **Python 3.11+**（建議用 Homebrew 安裝）
- 網路連線（使用雲端 AI 時；Ollama 除外）

---

## 安裝與啟動

### 方式 A：下載 `.app`（推薦給同事）

1. 從 [GitHub Releases](https://github.com/louisty2006/VibeCode_Translator/releases) 下載 `VibeCode Translator.app`（或向開發者索取 `dist/VibeCode Translator.app`）
2. 拖到「應用程式」資料夾
3. 雙擊開啟（首次可能需在 **系統設定 → 隱私權與安全性** 點「仍要開啟」）
4. 授予 **輔助使用** 權限（見下方「macOS 權限設定」）
5. 選單列出現 **✦** 後，開啟 **⚙️ Settings** 填入 API Key

> 不需要安裝 Python、venv 或 `pip`。

---

### 方式 B：從原始碼執行（開發者）

#### 1. 下載專案

```bash
git clone https://github.com/louisty2006/VibeCode_Translator.git
cd VibeCode_Translator
```

#### 2. 建立虛擬環境並安裝依賴

```bash
python3 -m venv venv
source venv/bin/activate          # 終端機應顯示 (venv)
pip install -r requirements.txt     # 必做！否則會缺 rumps、AppKit
```

#### 3. 啟動 App

```bash
python main.py
```

> **注意：** clone 下來不能直接 `python main.py`，一定要先 `pip install -r requirements.txt`。

啟動後，選單列出現 **✦** 圖示，代表 App 已在背景執行。首次啟動會自動開啟設定視窗。

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

## 設定說明

點選選單列 **✦ → ⚙️ Settings** 開啟設定視窗。

| 欄位 | 說明 |
|------|------|
| **AI Provider** | 選擇 AI 供應商（見下方列表） |
| **API Key** | 你的 API 金鑰（Ollama 可留空） |
| **Model（選填）** | 覆寫預設模型名稱，留空則用內建預設值 |
| **Explanation Language** | 解釋語言：English 或 繁體中文 |

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

App 需要以下權限才能正常運作：

### 輔助使用（Accessibility）— 必要

用於：
- 監聽全域快捷鍵 `Cmd + Shift + E`
- 模擬 `Cmd + C` 讀取你反白的文字

**設定步驟：**

1. 開啟 **系統設定 → 隱私權與安全性 → 輔助使用**
2. 啟用你執行 App 的程式，通常是：
   - **Terminal**（若用終端機啟動）
   - **Python** 或 **Python.app**（Homebrew 路徑）
3. 若清單中沒有，點 **+** 手動加入你的 Python 路徑：

```bash
# 查看你正在使用的 Python 路徑
which python3
```

4. **完全退出並重新啟動** App

也可透過選單列 **✦ → 🔓 Enable Shortcut** 開啟引導提示。

### 輸入監控（Input Monitoring）— 建議

部分 macOS 版本需要額外授予輸入監控權限，路徑同上：**系統設定 → 隱私權與安全性 → 輸入監控**。

---

## 使用方式

1. 在任何 App 中 **反白一段程式碼**
2. 按 **`Cmd + Shift + E`**
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
├── settings.py             # 讀寫使用者設定
├── setup.py                # py2app 打包設定
├── build_app.sh            # 一鍵打包腳本
├── requirements.txt        # 執行時依賴
└── requirements-build.txt  # 打包時依賴（含 py2app）
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
