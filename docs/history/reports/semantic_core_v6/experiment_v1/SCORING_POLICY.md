# 冻结评分口径

Assistant-authored synthetic acceptance references, frozen before predictions; NOT independently reviewed human gold

Manual semantic matching against frozen propositions, one-to-one. Preserve referent, quantity/unit, negation, modality; fine-label differences within same coarse type do not penalize meaning. Main precision includes every predicted main fact, including duplicates. Wrongly routed other loses main recall. No changes to references after predictions. Source problems reported separately. Compound facts cannot earn multiple atomic TPs. Real captions have no gold accuracy claim. Strict normalized text repeat F1 is wording agreement, not semantic accuracy.

c0 may scopes both sleeping and under-table proposition. Paragraph-scope accepted; synonymous complete facts accepted. Reviewer must explain unmatched/partial facts. No numerical confidence threshold is claimed.
