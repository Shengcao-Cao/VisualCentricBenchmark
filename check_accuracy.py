from json_repair import repair_json
import json

base = '/Users/shengcao/Downloads/formalized_datasets/coreset/'

models = [
    ('gpt-5.4', 'filtered_data_with_solution_hard_gpt_5_4.json', 'gpt-5.4'),
    ('gemini-3.1-pro', 'filtered_data_with_solution_hard_gemini_3_1_pro_preview.json', 'gemini-3.1-pro-preview'),
    ('gemma-4-31b', 'filtered_data_with_solution_hard_gemma_4_31b.json', 'gemma-4-31b-it'),
    ('claude-opus-4.6', 'filtered_data_with_solution_hard_claude_opus_4_6.json', 'us.anthropic.claude-opus-4-6-v1'),
    ('claude-sonnet-4.6', 'filtered_data_with_solution_hard_claude_sonnet_4_6.json', 'us.anthropic.claude-sonnet-4-6'),
    ('gemini-3.1-flash-lite', 'filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview.json', 'gemini-3.1-flash-lite-preview'),
    ('gpt-5.4-mini', 'filtered_data_with_solution_hard_gpt_5_4_mini.json', 'gpt-5.4-mini'),
    ('kimi-k2.5', 'filtered_data_with_solution_hard_kimi_k2_5.json', 'moonshotai.kimi-k2.5'),
    ('qwen3-vl-235b', 'filtered_data_with_solution_hard_qwen3_vl_235b_a22b.json', 'qwen.qwen3-vl-235b-a22b'),
    ('qwen3.5-397b', 'filtered_data_with_solution_hard_open_router_qwen3_5_397b_a17b.json', 'qwen/qwen3.5-397b-a17b'),
    ('nova-2-lite', 'filtered_data_with_solution_hard_nova_2_lite.json', 'us.amazon.nova-2-lite-v1:0'),
]

results = []
for label, fname, mk in models:
    with open(base + fname) as f:
        data = json.load(f)

    total = len(data)
    initially_parsed = 0
    initially_correct = 0
    repair_recovered = 0
    repair_correct = 0
    unparsed = 0

    for d in data:
        if not isinstance(d, dict):
            continue
        entry = (d.get('model') or {}).get(mk)
        if not isinstance(entry, dict):
            continue
        judge = entry.get('judge')
        if not isinstance(judge, dict):
            continue

        reasoning = judge.get('reasoning', '')
        if 'Parse error' not in reasoning:
            initially_parsed += 1
            if judge.get('correct') is True:
                initially_correct += 1
        else:
            raw = reasoning[len('Parse error: '):]
            try:
                fixed = repair_json(raw, return_objects=True)
                if isinstance(fixed, dict) and 'correct' in fixed:
                    repair_recovered += 1
                    if fixed['correct'] is True:
                        repair_correct += 1
                else:
                    unparsed += 1
            except Exception:
                unparsed += 1

    total_correct = initially_correct + repair_correct
    acc = total_correct / total * 100
    results.append((label, total, initially_parsed, initially_correct, repair_recovered, repair_correct, unparsed, total_correct, acc))

results.sort(key=lambda x: -x[8])

hdr = f"{'Model':<22} {'Total':>5} {'Init.Parsed':>11} {'Init.Corr':>10} {'Repaired':>9} {'Rep.Corr':>9} {'Unparsed':>9} {'TotalCorr':>10} {'Acc':>7}"
print(hdr)
print('-' * len(hdr))
for label, total, ip, ic, rr, rc, up, tc, acc in results:
    print(f'{label:<22} {total:>5} {ip:>11} {ic:>10} {rr:>9} {rc:>9} {up:>9} {tc:>10} {acc:>6.1f}%')
