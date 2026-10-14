# Strata Custom Skills

把六個自訂 Codex skill 接到本機 Strata 的離線 MCP 套件。保留原始
SKILL.md、references、scripts、schemas 與測試；另加 Strata 能力適配層。

| Skill | Strata 可用功能 |
| --- | --- |
| architecture-visualizer | 讀取完整規格；執行原附架構分析程式，輸出 SVG 和可追溯 JSON |
| codex-model-router | 執行原附評分政策，提供分類建議；由目前本機模型繼續工作 |
| presentation-design-pro | 簡報敘事、逐頁藍圖、視覺設計與檢查流程；既有 workspace 工具可產生基本 PPTX |
| project-architecture-workflow | 架構設計、實作切片、驗收與狀態管理；附驗證程式 |
| surgical-coding-debug | 有限範圍除錯、修改與驗證流程；附驗證程式 |
| ui-ux-design-pro | 介面設計、研究參考與檢查流程，可透過 workspace 工具寫入程式 |

## 安裝到既有 Docker Strata

前提：已有 Linux Strata Docker 映像、Python 3.10+、已設定的模型和 workspace
MCP。預設父映像為 `strata:local-rtx4070-tools`。此套件不下載模型、不重建 GPU 引擎。

```powershell
git clone https://github.com/Funji713/strata-custom-skills.git
docker build -t strata:local-custom-skills ./strata-custom-skills
python ./strata-custom-skills/install.py --config ./docker-local/strata-iq2_xs.json
```

在既有 compose 的 Strata service 將 `image` 改為 `strata:local-custom-skills`，
`build.context` 指向 `./strata-custom-skills`，`build.dockerfile` 改為 `Dockerfile`。
保留原模型、`/workspace`、設定檔掛載和 localhost port binding。

```powershell
docker compose -f compose.local.yaml up -d --no-build
Invoke-RestMethod http://127.0.0.1:8080/mcp
```

`/mcp` 應顯示 `skills` ready，並列出四個工具。安裝程式只增加
`mcp_servers.skills`，首次變更會備份設定為 `.before-custom-skills`。
自訂父映像可加 `--build-arg STRATA_TOOLS_IMAGE=your-image`。
如用其他 Python、套件路徑或 workspace，使用 install.py 的對應參數。

## 在網頁聊天使用

開啟 Strata 網頁的 **Tools / MCP**，在新聊天明確指定 skill，例如：

- 「請先載入 surgical-coding-debug，再修正 workspace 裡的 app.py。」
- 「用 presentation-design-pro 規劃五頁繁體中文簡報，先儲存逐頁藍圖，再產出 PPTX。」
- 「用 architecture-visualizer 分析 app.py 和 service.py，產生架構 SVG。」
- 「載入 ui-ux-design-pro 和它的設計原則參考，設計我的登入頁。」
- 「使用 project-architecture-workflow 幫我規劃這個專案的架構與驗收。」
- 「使用 codex-model-router 分類這個修改的複雜度，然後用本機模型完成。」

API 需在 `/v1/chat/completions` 請求加 `"strata_mcp": true`。
模型會看見 `skills__read_skill` 等工具；讀取有分頁，需接續 next_line。
所有 skill 在工具目錄可發現，模型是否自動挑對取決於模型；明確指名最可靠。
檔案操作只限 `/workspace`。架構圖輸出在 `architectures/<唯一編號>/`。

## 能力邊界

這是工作流程與可執行資源移植，不會讓 Qwen 變成 Codex。沒有 Codex 子代理、
GPT 模型切換、任意 shell、網路瀏覽、imagegen 或完整投影片渲染。
router 明確改為建議模式。原文提到的外部製作 skill 並未包含。
PPTX 產生器只支援基本標題和條列；複雜版面、圖片、講者備註與逐頁渲染驗證
需另接製作工具。不可把未做的測試、網路查證或視覺驗證回報為完成。

原始來源完全保留於 `skills/`，Strata 適配規則在 `runtime/skills_mcp.py`，
每次讀取 skill 都會附上，原始文字無須改寫。可重用原附 Python CLI；
MCP 僅開放固定工具，不執行使用者輸入的程式碼。

## 驗證和移除

```sh
python -m unittest discover -s tests -v
python skills/codex-model-router/scripts/route_task.py --self-test
python -m unittest discover -s skills/project-architecture-workflow/tests -v
python -m unittest discover -s skills/surgical-coding-debug/tests -v
python -m unittest discover -s skills/architecture-visualizer/package/tests -v
```

整合測試須在 Linux（Docker）執行，因安全檔案工具使用 O_NOFOLLOW/dir_fd。
實測結果見 [docs/VALIDATION.md](docs/VALIDATION.md)。來源與使用權說明見
[NOTICE.md](NOTICE.md)。

移除：用同樣參數執行 `install.py --remove`，compose 改回先前映像和 build
設定，再重新建立容器。原始 skills、模型、workspace 檔案不會被刪除。
