# AI 漫剧安全艺术风格手册库

本目录用于管理 AI 漫剧生产中的通用艺术风格。每个风格目录只保留一个主文档 `README.md`，集中包含风格定位、视觉 DNA、角色资产、场景资产、道具资产、分镜视频、质量验收和风险改写规则，避免同一风格信息分散在多个文件中。

## 使用原则

- 只使用通用艺术流派、媒介质感、题材类型、地域文化、时代语汇和镜头语言。
- 不使用具体人名、公司名、品牌名、平台名、作品名、角色名或可识别 IP 标志。
- 若输入含风险名称，先抽象为媒介、色彩、材质、构图、情绪和时代描述，再进入提示词。
- 最多叠加 3 个风格词：主风格 1 个、媒介或质感 1 个、光影或情绪 1 个。

## 目录结构

- 风格目录：60 + 个。
- 每个风格目录：`README.md` 为唯一主文档，`images/` 用于存放后续参考图或样张。
- 根目录保留：`README.md`、`STYLE_TAXONOMY.md`、`SAFETY_NAMING_GUIDE.md`。

## 使用方式

1. 先从下方分类索引选择风格目录。
2. 打开该目录的 `README.md`。
3. 按资产类型复制对应模板：角色、场景、道具、分镜或视频。
4. 替换花括号中的业务变量，并保留风格、材质、光影、色彩和安全约束。
5. 批量生成时固定角色身份、场景结构、道具状态和光源方向。

## 东方与民族

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `ancient_egyptian_mural` | 古埃及壁画风 | ancient Egyptian mural | 古文明、神秘仪式、历史幻想、墓室探险 |
| `byzantine_mosaic` | 拜占庭镶嵌金色风 | Byzantine mosaic | 庄严宫廷、金色圣殿感、历史幻想场景 |
| `folk_papercut` | 民间剪纸动画风 | folk paper-cut | 民俗故事、节庆、寓言、二维短片 |
| `gongbi_heavy_color` | 工笔重彩国风 | meticulous heavy-color Chinese painting | 古风人物、宫廷、花鸟、东方高精细资产 |
| `japanese_ink_wash` | 东方水墨静物风 | eastern ink wash | 静物、山水、茶室、克制日常镜头 |
| `silk_road_mural` | 丝路壁画重彩风 | silk road mural | 古风历史、神话舞乐、宫廷与壁画感镜头 |

## 东方幻想

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `2D_ink_wash_xianxia` | 水墨仙侠动画风 | ink wash xianxia animation | 诗意仙侠、水墨叙事、留白镜头 |
| `3D_chinese_xianxia_donghua` | 3D国漫仙侠风 | Chinese xianxia 3D donghua | 仙侠角色、门派场景、奇幻长剧 |
| `CG_eastern_fantasy` | 东方幻想CG风 | eastern fantasy CG | 宏大奇幻、概念设定、游戏感漫剧 |

## 写实/影视

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `documentary_realism` | 纪录片写实风 | documentary realism | 现实题材、人物访谈感、社会观察短剧 |
| `realpeople_modern_commercial` | 现代写实商业摄影风 | modern commercial realism | 现实人物、都市短剧、商业宣传感资产 |

## 动画/漫画

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `2D_cel_animation` | 二维赛璐璐动画风 | 2D cel animation | 角色设定、动作镜头、清晰商业动画资产 |
| `2D_handpainted_fantasy_anime` | 手绘奇幻动画电影风 | hand-painted fantasy animation | 治愈、童话、小镇冒险、自然奇幻 |
| `2D_hot_blood_action_anime` | 二维热血动作动画风 | hot-blooded action anime | 战斗、训练、竞技、成长型漫剧 |
| `2D_japanese_cinematic_anime` | 现代日系电影动画风 | Japanese cinematic anime | 青春、校园、都市日常、细腻情绪 |
| `2D_korean_webtoon` | 现代韩漫半写实风 | semi-realistic webtoon | 都市爱情、职场、轻奢人物设定 |
| `3D_chibi_cartoon` | 3D卡通Q版风 | 3D chibi cartoon | 可爱角色、轻喜剧、儿童向或治愈短剧 |
| `clay_stopmotion` | 黏土定格动画风 | clay stop-motion | 童话、黑色幽默、手作短剧、角色道具库 |
| `watercolor_animation` | 水彩动画风 | watercolor animation | 温柔日常、回忆、自然场景、儿童故事 |

## 复古/流行

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `retrofuturism_past_future` | 复古未来主义风 | retrofuturism | 过去想象中的未来、复古广告、轻科幻生活 |
| `vaporwave_neon_retro` | 蒸发波霓虹复古风 | vaporwave | 梦幻网络怀旧、音乐视觉、超现实都市片段 |

## 暗黑与奇幻

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `dark_fantasy_shadow` | 黑暗幻想阴影风 | dark fantasy | 悬疑、奇幻危机、古堡、诅咒式世界观 |
| `dreamcore_surreal` | 梦幻核超现实风 | dreamcore | 梦境、童年记忆、不真实空间、心理漫剧 |
| `gothic_romance` | 哥特暗黑浪漫风 | gothic | 悬疑爱情、古堡、夜色肖像、暗黑家族剧 |
| `magic_realism_daily` | 魔幻现实主义日常风 | magic realism | 日常奇迹、城市寓言、温柔奇幻短剧 |
| `weirdcore_glitch` | 怪异核故障空间风 | weirdcore | 悬疑梦境、异常空间、网络怪谈式漫剧 |

## 朋克/亚文化

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `2D_cyberpunk_anime` | 动漫赛博朋克风 | anime cyberpunk | 二次元科幻、都市战斗、未来机能时装 |
| `astropunk_space_adventure` | 星系朋克太空冒险风 | astropunk | 星际探索、宇宙冒险、太空船队、外星港口 |
| `atompunk_retro_future` | 原子朋克复古未来风 | atompunk | 复古未来、太空乐观主义、家庭科幻喜剧 |
| `biopunk_organic_tech` | 生物朋克有机科技风 | biopunk | 基因实验、有机科技、生态惊悚、医疗科幻 |
| `cyberpunk_photoreal` | 超写实赛博朋克风 | photoreal cyberpunk | 未来都市、侦探、科技悬疑、雨夜动作 |
| `dieselpunk_retro_industrial` | 柴油朋克复古工业风 | dieselpunk | 复古工业、装甲载具、旧时代都市动作 |
| `lunarpunk_mystic_night` | 月亮朋克神秘夜色风 | lunarpunk | 夜色奇幻、月光仪式、神秘生态科幻 |
| `solarpunk_ecological_future` | 太阳朋克生态未来风 | solarpunk | 生态未来、绿色城市、治愈科幻、乌托邦社区 |
| `steampunk_mechanical` | 蒸汽朋克机械风 | steampunk | 复古机械、冒险、工业城市、飞艇时代 |

## 漫画/影视

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `2D_superhero_comic` | 美式超级英雄漫画风 | superhero comic | 原创都市英雄、动作漫画、强节奏分镜 |
| `noir_detective_comic` | 黑色侦探漫画风 | noir detective comic | 侦探、悬疑、都市犯罪、雨夜独白 |

## 现代/流行

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `3D_stylized_render` | 风格化3D渲染风 | stylized 3D render | 动画角色、产品级道具、轻奇幻世界 |
| `colored_pencil_illustration` | 彩铅插画动画风 | colored pencil illustration | 温暖人物设定、轻绘本、生活片段 |
| `digital_painting_modern` | 现代电绘概念风 | modern digital painting | 概念角色、海报、游戏感角色与场景 |
| `flat_design_animation` | 扁平化动画设计风 | flat design animation | 解释型漫剧、轻喜剧、信息可视化叙事 |
| `kawaii_watercolor` | 可爱水彩治愈风 | kawaii watercolor | 治愈日常、萌系动物、儿童向片段 |
| `low_poly_geometric` | 低多边形几何风 | low-poly | 简洁3D场景、幻想地图、轻量动画资产 |
| `pixel_art_animation` | 像素艺术动画风 | pixel art | 复古游戏感漫剧、轻量资产、可爱冒险 |
| `sketch_line_art` | 素描线稿动画风 | sketch line art | 概念草图、分镜预演、黑白情绪短片 |

## 经典艺术

| 目录 | 中文风格 | 英文通用词 | 适用漫剧 |
|---|---|---|---|
| `art_deco_luxury` | 装饰艺术奢华风 | art deco | 爵士年代、豪华酒店、都市权谋、复古宴会 |
| `art_nouveau_botanical` | 新艺术植物曲线风 | art nouveau | 优雅女性、花园、幻想装饰、片头海报 |
| `baroque_theatrical` | 巴洛克戏剧光影风 | baroque | 权谋、舞台感、强情绪历史片段 |
| `bauhaus_geometric` | 包豪斯几何设计风 | bauhaus | 现代建筑、设计感片头、几何角色与空间 |
| `constructivism_poster` | 建构主义海报风 | constructivism | 群像宣传视觉、强图形分镜、行动叙事 |
| `cubism_geometric` | 立体主义几何重构风 | cubism | 实验叙事、心理拆解、抽象角色海报 |
| `expressionism_emotional` | 表现主义情绪风 | expressionism | 心理戏、悬疑、焦虑或强烈内心戏 |
| `impressionism_light` | 印象主义光影风 | impressionism | 自然光、日常风景、情绪氛围漫剧 |
| `minimalism_clean` | 极简主义留白风 | minimalism | 情绪留白、高级海报、静态短剧、概念片头 |
| `oil_painting_animation` | 油画质感动画风 | oil painting animation | 历史叙事、厚重情绪、贵族或史诗片段 |
| `pointillism_optical` | 点彩光学色点风 | pointillism | 梦幻自然、实验视觉、光学质感场景 |
| `pop_art_graphic` | 波普图形漫画风 | pop art | 喜剧、广告感、强视觉冲击、漫画转场 |
| `post_impressionism_expressive` | 后印象主义表现色彩风 | post-impressionism | 强情绪人物、色彩叙事、心理化场景 |
| `renaissance_classical` | 文艺复兴古典风 | renaissance | 历史人物、古典构图、庄重叙事 |
| `rococo_delicate` | 洛可可精致宫廷风 | rococo | 轻喜剧宫廷、甜美贵族、精致室内 |
| `surrealism_dream` | 超现实梦境风 | surrealism | 梦境、意识流、奇异转场、寓言漫剧 |
