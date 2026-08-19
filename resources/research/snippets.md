## Dataset Generation

```bash
~/Projects/rag-techniques/project   rag-techniques-benchmark    phase4-dataset-generation                                                                                 142ms  ojaswi  zsh(venv) 
❯ uv run python -m dataset_generation.run_dataset_generation

None of PyTorch, TensorFlow >= 2.0, or Flax have been found. Models won't be available and only tokenizers, configuration and file/data utilities can be used.
13:33:19 [INFO] [Q1_Direct_Text/queries] AAPL_2023 attempt 1/3: REJECTED (citation mismatch: the Critic's independently-found node_ids ['AAPL_2023_n0280', 'AAPL_2023_n0439'] did not overlap the proposed gt_citations ['AAPL_2023_n0081']) -- 3/140 accepted
21:09:55 [INFO] [Q1_Direct_Text/queries] AAPL_2023 attempt 2/3: ACCEPTED -- 4/140 accepted
21:10:32 [INFO] [Q1_Direct_Text/queries] MSFT_2023 attempt 1/3: REJECTED (citation mismatch: the Critic's independently-found node_ids ['MSFT_2023_n0285'] did not overlap the proposed gt_citations ['MSFT_2023_n0283']) -- 4/140 accepted
21:11:27 [INFO] [Q1_Direct_Text/queries] MSFT_2023 attempt 2/3: REJECTED (citation mismatch: the Critic's independently-found node_ids ['MSFT_2023_n0290'] did not overlap the proposed gt_citations ['MSFT_2023_n0285']) -- 4/140 accepted
21:13:11 [INFO] [Q1_Direct_Text/queries] MSFT_2023 attempt 3/3: REJECTED (value mismatch: the Critic independently computed 'Our operations and financial results are subject to various risks and uncertainties that could adversely affect our business, financial condition, results of operations, cash flows, and the trading price of our common stock.', which does not match the proposed ground_truth_answer 'our business, financial condition, results of operations, cash flows, and the trading price of our common stock') -- 4/140 accepted
21:14:17 [INFO] [Q1_Direct_Text/queries] TSLA_2023 attempt 1/3: REJECTED (citation mismatch: the Critic's independently-found node_ids [] did not overlap the proposed gt_citations ['TSLA_2023_n0115']) -- 4/140 accepted
21:16:42 [INFO] [Q1_Direct_Text/queries] TSLA_2023 attempt 2/3: REJECTED (citation mismatch: the Critic's independently-found node_ids ['TSLA_2023_n0069'] did not overlap the proposed gt_citations ['TSLA_2023_n0071']) -- 4/140 accepted
```