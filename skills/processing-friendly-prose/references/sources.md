# Sources

Citations behind the checklist in `SKILL.md`. Both papers are preprints
and have not been peer reviewed. Read this file when a user asks why a
rule exists, or when a revision needs a citation.

- Clark, T. H., Martin, M. B., & Mahowald, K. (2026). Why is AI-generated
  language so hard to understand? arXiv:2610.29162.
  https://arxiv.org/abs/2610.29162

  This is the main source for the checklist. The authors find that recent
  AI-generated English overuses features that are known to make reading
  harder: rare word pairs, long gaps between related words, stacks of
  nouns, relative clauses that drop "that" or "which", inanimate subjects
  with verbs that usually take a person, and one-off verbs made from
  nouns. They show that these shapes are choices, not just a side effect
  of the topic: a meaning-preserving rewrite uses them less often. They
  also show that a penalty on length during training can push a model
  toward the shorter of two grammatical options, even in patterns it was
  not trained on. The effect is stronger in chat and coding explanations
  than in a single short essay. The study is in English only.

- Cekini, K., Biondi, E., Boldrini, C., Passarella, A., & Conti, M.
  (2026). The Cognitive Cost of LLM Writing: A Reading-Time Comparison
  with Human Text. arXiv:2610.23715. https://arxiv.org/abs/2610.23715

  Optional support for the "brevity is not readability" item. The authors
  compare human articles with rewritten versions and find that the
  rewrites are shorter and can take slightly less total time to read,
  while the predicted time per word is higher. The more a rewrite is
  shortened, the more that per-word cost tends to rise.
