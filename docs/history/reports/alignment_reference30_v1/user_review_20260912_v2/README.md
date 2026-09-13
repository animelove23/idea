# 根据完整原句修正 added / ambiguous 边界

本版继承 user_review_20260912 的参考标注，保留旧版与旧实验指标。新增 API 请求 0 次，未重算指标。此版仍为助手参考标注，不能整体称为人工金标准；下述数量拆分是根据用户反馈、由助手核对完整原句后的裁定。

## 264423：戴眼镜是新增，人物身份可以另行不确定

Vanilla 提到 “a woman and a child”，全文没有眼镜或戴眼镜。
Steer 写道 “One person is wearing glasses”。

- ∅ → steer f6 “One person wears glasses.”：added。
- ∅ → steer f7 “Glasses are present.”：added。
- 戴眼镜的是 woman 还是 child 可以在实体对应中保留不确定，但不影响戴眼镜这条信息的新增判定。
- 不是 modified：原文没有相同人物、相同眼镜属性或关系的旧值可供修改。

以上两条在旧参考中已经是 added。本次纠正的是上一条回复的示例呈现，不是声称模型已经正确预测；该样本旧运行未获得 Fact Alignment 模型响应。

## 341389：总人数与滑雪人数不能仅按数字配对

Vanilla：“a group of people skiing and snowboarding down the hill”及“There are at least 13 people visible in the scene”。
Steer：“There are at least 12 people skiing down the slope”。

- ∅ → steer f5 “At least 12 people are skiing down the slope.”：added。至少13名参与两种活动的人，并不蕴含至少12人在 skiing。
- original f6 “At least 13 people are visible.” → ∅：removed。Steer 的至少12人不保留至少13人的下界。
- 原有 skiing 行为单独与 Steer 的 skiing 行为 retained；数量新增不意味着行为也新增。

把旧参考 f6 ↔ f5 的 ambiguous 拆成上述两条。没有改写原 facts。

## 当前执行边界

活动提示词已取消“计数范围不同一律 partial_overlap”的要求，改为核对对侧完整 caption 后分别判断新增/删除。没有把这两条测试原句加入 few-shot。

程序仍会对模型强行提出的跨计数范围 modified 配对给出 count_scope_changed 审查标记；该标记只表示此配对不安全，不能作为正确答案必为 ambiguous 的依据。程序接受模型提出的合规 added / removed，无需靠关键词自动编造拆分。

新提示词尚未进行在线重测，旧 v1.2 离线回放及指标保持原样。
