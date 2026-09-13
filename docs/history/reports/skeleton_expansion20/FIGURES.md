# 20图探索性统计图

图中的supported均指视觉模型标签，未经独立人工确认。详见[结果解释及限制](RESULTS.md)。

## 长度变化与事实保留

![长度与事实保留](./outputs/skeleton_expansion20/analysis/01_length_and_retention.png)

[SVG](analysis/01_length_and_retention.svg) · [每图源数据](analysis/plot_pair_data.csv)

## 属性删除原因

![属性删除原因](./outputs/skeleton_expansion20/analysis/02_attribute_removal_reasons.png)

[SVG](analysis/02_attribute_removal_reasons.svg) · [逐事实源数据](analysis/fact_ledger.csv)

## POS与首次原词位置

![POS与位置](./outputs/skeleton_expansion20/analysis/03_pos_and_position.png)

[SVG](analysis/03_pos_and_position.svg) · [逐事实源数据](analysis/fact_ledger.csv)

最后两个位置区间与部分POS的分母较小。上述图形是开发样本中的描述性分布，不能直接解释为EOS提前、注意力衰减或某类词性导致删除。
