# 龍虎塔：虎口入（Dragon Tiger Tower: Enter the Tiger）

以高雄蓮池潭「龍虎塔」為主題的第一人稱 3D 恐怖遊戲。
所有 3D 模型由 Blender Python 腳本程序化生成，遊戲以 Godot 4 製作，
音效亦為程序化生成，無任何外部素材。

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

- 虎靈看見你會追擊，被抓到即死亡。
- 用**手電筒直射**虎靈約 1.5 秒可將其驅退。
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
# 玩法整合測試（追擊致死／手電筒驅退／勝利條件）
godot --headless res://scenes/debug_gameplay.tscn --quit-after 30000
# 視覺巡覽（需要 GPU，輸出 PNG 序列）
godot res://scenes/debug_tour.tscn --write-movie /tmp/tour/f.png --fixed-fps 10
```

## 專案結構

```
blender/            # 程序化生成腳本（bpy）
  common.py         # 共用：材質、幾何、匯出 glTF
  gen_island.py     # 石平台、雙七層八角塔（含樓梯）、龍虎入口雕像、燈籠
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
```

## 技術備註

- glTF 節點命名後綴 `-col`（三角網格碰撞）與 `-colonly`（隱形碰撞，
  用於樓梯坡道與樓梯口銜接平台），由 Godot 匯入時自動建立 StaticBody。
- 塔內樓梯每層旋轉 -90°，樓板開口為走廊型並附防護欄杆，
  淨空經過爬塔機器人驗證。
- 鬼魂 AI：遊蕩（路徑點）→ 追擊（視線＋距離）→ 被手電筒驅退，
  三態狀態機。
