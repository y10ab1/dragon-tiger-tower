# 龍虎塔：虎口入（Dragon Tiger Tower: Enter the Tiger）

以高雄蓮池潭「龍虎塔」為主題的第一人稱 3D 恐怖遊戲。
所有 3D 模型由 Blender Python 腳本程序化生成，遊戲以 Godot 4 製作，
音效亦為程序化生成；介面使用隨遊戲附帶的開源繁體字型「霞鶩文楷 TC」。

## 線上遊玩

**https://y10ab1.github.io/dragon-tiger-tower/**

使用電腦搭配鍵盤、滑鼠，建議 Chrome／Edge／Firefox。按「踏入虎口」下載遊戲，
載入後點一下遊戲畫面鎖定滑鼠。首次鎖定前，角色與鬼魂不會開始移動。
瀏覽器按 Esc 會釋放滑鼠，點畫面可重新鎖定；目前沒有手機觸控操作。

### 編譯網頁版

使用 **Godot 4.6.1**，並安裝相同版本的 Web 匯出範本
（`web_nothreads_release.zip` 放在 Godot 的 `export_templates/4.6.1.stable/`）。

在儲存庫根目錄執行：

```bash
bash scripts/export-web.sh
python3 -m http.server 8765 --directory build/web
```

開啟 http://localhost:8765/ 測試；不能直接以 `file://` 開啟 HTML。
輸出為 `build/web/`，包含 HTML、WebAssembly、遊戲素材與字型授權。

- Web 使用 **WebGL 2 Compatibility** 與**單執行緒**，不需要跨來源隔離標頭。
- 桌面版保留 Forward+；網頁版停用體積霧與 Glow，保留一般霧與實際燈光。
- `.github/workflows/pages.yml` 在 `main` 的遊戲／匯出設定更新時自動編譯並部署。
  也可到 GitHub Actions 手動執行 **Build and deploy web game**。
- GitHub Settings → Pages 的來源為 **GitHub Actions**。

## 故事

龍虎塔的習俗是「龍口進、虎口出」，可消災解厄。
深夜，你卻從「虎口」走了進來——犯了大忌。
被困在異界化的蓮池潭中，你必須收集散落在九曲橋與雙塔七層樓的
**七張符咒**，再從「龍口」離開，方可化解厄運。
虎靈怨魂在橋上與塔間遊蕩……

## 玩法

| 按鍵 | 動作 |
|---|---|
| WASD | 移動 |
| 滑鼠 | 視角 |
| Shift | 衝刺（有體力限制，下方綠條） |
| F | 手電筒開關 |
| 空白鍵 | 跳躍 |
| R | 重新開始 |
| Esc | 釋放滑鼠 |
| 滑鼠左鍵 | 滑鼠釋放後，點畫面重新鎖定視角 |

- 虎靈看見你會追擊，被抓到即死亡。
- 用**手電筒直射**虎靈約 1.5 秒可將其驅退。
- 手電筒跟隨畫面中央準星；有效照中時準星變金色，圓弧顯示驅退進度。
- 切出視窗會釋放滑鼠，回到遊戲後點畫面即可繼續轉向。
- 掉進蓮池潭也會死。
- 集滿 7 張符咒後走進**龍口**即獲勝。

## 執行

```bash
cd game
godot          # 或用 Godot 4.6+ 編輯器開啟 project.godot
```

## 重新生成素材

3D 模型（Blender 5.x）：

```bash
blender -b -P blender/gen_island.py    # 島嶼＋雙塔＋龍虎雕像
blender -b -P blender/gen_bridge.py    # 九曲橋＋涼亭
blender -b -P blender/gen_ghost.py     # 鬼魂＋符咒
blender -b -P blender/preview.py       # 渲染預覽圖（/tmp/opencode/*.png）
```

音效：

```bash
python3 blender/gen_audio.py
```

生成後需重新匯入：`cd game && godot --headless --import`

## 自動化測試

```bash
cd game
# 資產匯入
godot --headless --import
# 物理落點測試（樓板、坡道、橋面、隧道）
godot --headless res://scenes/debug_stairs.tscn --quit-after 3000
# 爬塔機器人（用真實輸入從 1F 走樓梯到 7F）
godot --headless res://scenes/debug_climb.tscn --quit-after 40000
# 龍虎入口往返測試（從廣場穿過獸口，走到塔內門廳再返回）
godot --headless res://scenes/debug_entrances.tscn
# 雙塔六段樓梯、三條行走路徑的上樓／下樓往返
godot --headless --fixed-fps 60 --script res://scripts/debug_tower_walk.gd
# 窗洞防卡、貼牆退回、樓板邊緣與樓梯側面碰撞
godot --headless --script res://scripts/debug_tower_edges.gd
# WebGL 相容模式的近距離陰影比較圖（需要顯示器）
godot --rendering-method gl_compatibility --script res://scripts/debug_shadows.gd
# 玩法整合測試（追擊致死／手電筒驅退／勝利條件）
godot --headless res://scenes/debug_gameplay.tscn --quit-after 30000
# 視角、滑鼠鎖定、手電筒遮擋與 HUD 測試（需要顯示器，不能用 --headless）
godot --script res://scripts/debug_controls.gd
# 同時輸出 1280×720／960×540 介面、滑鼠釋放與死亡畫面
godot --script res://scripts/debug_controls.gd -- --screenshots
# 視覺巡覽（需要 GPU，輸出 PNG 序列）
godot res://scenes/debug_tour.tscn --write-movie /tmp/tour/f.png --fixed-fps 10
```

## 專案結構

```
blender/            # 程序化生成腳本（bpy）
  common.py         # 共用：材質、幾何、匯出 glTF
  gen_island.py     # 石平台、雙七層八角塔（含樓梯）、龍虎入口雕像、燈籠
  statues.py        # 曲面龍虎雕像、彩繪紋路與獨立通道碰撞
  gen_bridge.py     # 九曲橋、涼亭
  gen_ghost.py      # 虎靈怨魂、符咒
  gen_audio.py      # 程序化音效（風、心跳、呻吟、鑼聲…）
  preview.py        # EEVEE 預覽渲染
game/               # Godot 4 專案
  scenes/           # main / player / ghost / talisman / debug_*
  scripts/          # 遊戲邏輯（GDScript）
  shaders/          # 水面 shader
  assets/models/    # 生成的 .glb
  assets/audio/     # 生成的 .wav
  assets/fonts/     # 霞鶩文楷 TC、SIL OFL 授權與介面 Theme
```

## 技術備註

- 建築外觀參照[左營龍虎塔實景](https://commons.wikimedia.org/wiki/File:Dragon_and_Tiger_Pagodas_02.jpg)：
  黃牆、朱柱、白色外廊欄杆、橘瓦綠邊翹簷與多節塔剎；雕像採曲面與立體彩繪細節。
  仍是程序化遊戲模型，並非測繪級重建；塔距、樓高、樓梯與九曲橋路線保留遊戲配置。
- `preview.py` 輸出日光全景、雙獸入口與龍／虎近照到 `/tmp/opencode/preview_*.png`，
  自動排除隱形碰撞網格。預覽的水面與日光不會改變遊戲夜景。

- glTF 節點命名後綴 `-col`（三角網格碰撞）與 `-colonly`（隱形碰撞，
  用於樓梯坡道與樓梯口銜接平台），由 Godot 匯入時自動建立 StaticBody。
- 塔內樓梯每層旋轉 -90°，樓板開口為走廊型並附防護欄杆，
  淨空經過爬塔機器人驗證。
- 塔內採用連續牆面碰撞、接牆八角樓板與實心斜坡碰撞，避免鑽進窗洞或樓梯底部。
  梯頂縮短樓板開口、加寬轉身空間；窗戶保留可見外觀，但不作通行入口。
- 九曲橋橋面由平面聯集生成，轉角不再疊放共面方塊。手電筒使用較高精度的
  陰影深度與偏移設定，減少 WebGL 近距離斜紋。
- 鬼魂 AI：遊蕩（路徑點）→ 追擊（視線＋距離）→ 被手電筒驅退，
  三態狀態機。
