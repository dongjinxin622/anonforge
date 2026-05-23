# 热血动作 · 导演叙事手法技能包

## 简介

本技能包为 **热血动作** 类型故事提供商用级导演叙事手法参考，覆盖从宏观导演规划到微观分镜表执行的生产流程。它只处理故事讲述、信息组织、人物调度、节奏、声音和镜头策略，适用于任何视觉风格，可与 `data/skills/art_list` 中的美术风格独立组合。

## 核心理念

| 维度 | 要求 |
|---|---|
| 类型核心 | 目标清晰、动作因果、升级节拍、信念爆发 |
| 离场感受 | 振奋、痛快、相信角色配得上胜利或失败后的再起 |
| 规划重点 | 主题、人物缺口、段落节奏、典型场景、声音方向、构图景别和镜头运动 |
| 分镜重点 | 观众信息、角色信息、景别/运镜、时长、人物行动、台词留白、声音和转场 |

## 文件结构

```text
Hot_blooded_action/
├── README.md
├── images/
│   ├── concept_image_prompt.md
│   └── director_concept.png
└── director_manual/
    ├── director_planning_narrative.md
    └── director_storyboard_table_narrative.md
```

## 技能文件说明

### 1. 叙事规划手法 (`director_manual/director_planning_narrative.md`)

用于导演规划阶段，定义 **热血动作** 在主题内核、人物动机、结构节奏、典型场景、声音音乐、构图景别、镜头运动、失败模式和商用验收上的执行标准。

### 2. 分镜表叙事手法 (`director_manual/director_storyboard_table_narrative.md`)

用于分镜表制作阶段，将 **热血动作** 的叙事策略落到镜头字段、观众信息、角色信息、景别机位、运镜起止、时长、人物行为、台词留白、声音进入和转场方式。

## 使用方式

1. 先选择故事类型技能包，例如 `Hot_blooded_action`。
2. 读取 `director_planning_narrative.md`，确定主题、段落、场景、声音和镜头策略。
3. 读取 `director_storyboard_table_narrative.md`，把规划拆为可执行分镜表。
4. 再叠加 `data/skills/art_list` 中任意艺术风格，生成具体视觉资产或视频提示词。

## 商用边界

- 不引用具体导演、画师、演员、公司、品牌、平台、作品、角色或可识别 IP。
- 不复制外部项目文本，只吸收通用叙事组织方法和生产验收标准。
- 不把美术风格当成导演风格；导演手册负责叙事，艺术手册负责视觉。
- 恐怖、动作、后末日等类型只写叙事技法，不写露骨暴力、现实伤害教学或可操作危险步骤。
