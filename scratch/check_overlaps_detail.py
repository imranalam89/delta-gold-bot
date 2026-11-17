import json

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

trades = d['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']['trades']

print("Checking overlaps in detail:")
for i in range(1, len(trades)):
    prev_t = trades[i-1]
    curr_t = trades[i]
    if curr_t['entry_idx'] <= prev_t['exit_idx']:
        print(f"\nTrade #{prev_t['id']} -> #{curr_t['id']}:")
        print(f"  Prev: #{prev_t['id']} [{prev_t['direction']}] Entry: {prev_t['entry_time']} (idx {prev_t['entry_idx']}) -> Exit: {prev_t['exit_time']} (idx {prev_t['exit_idx']})")
        print(f"  Curr: #{curr_t['id']} [{curr_t['direction']}] Entry: {curr_t['entry_time']} (idx {curr_t['entry_idx']}) -> Exit: {curr_t['exit_time']} (idx {curr_t['exit_idx']})")
        diff_mins = prev_t['exit_idx'] - curr_t['entry_idx']
        print(f"  Overlap: {diff_mins} minutes ({diff_mins/60:.2f} hours)")
