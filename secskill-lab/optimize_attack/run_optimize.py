"""LLM 对抗式优化主循环。

把攻击者 LLM 和裁判串起来，跑 T 轮优化循环。
每一轮：攻击者生成/改进 description → 裁判测被选中率 → 反馈给攻击者。

对应 IPI 论文的 CEM 循环：
  论文：每轮采样 → 打分 → 选精英 → 更新分布
  我们：每轮生成描述 → 测被选中率 → 反馈 → 改进描述

输出：
  1. 实时打印每轮的被选中率（看曲线变化）
  2. 最终输出最佳 description + 完整历史轨迹
  3. 保存结果到 JSON（给导师看/画图用）

用法：
  cd secskill-lab
  .venv/bin/python optimize_attack/run_optimize.py --rounds 5
  .venv/bin/python optimize_attack/run_optimize.py --rounds 5 --quick  # 只用前10个query（省时间）
"""
import os
import sys
import json
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attacker import AttackerLLM                               # noqa: E402
from evaluator import Evaluator, load_benign_descriptions     # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "results"


def get_competitor_descriptions():
    """拿到良性 skill 的描述，作为反馈给攻击者的'竞争对手情报'。"""
    return load_benign_descriptions()


def run_optimization(rounds=5, num_queries=None, verbose=True):
    """跑完整的优化循环。

    Args:
        rounds: 优化轮数
        num_queries: 每轮用多少 query 评估（None=全部20个）
        verbose: 打印详情
    """
    atk = AttackerLLM()
    competitors = get_competitor_descriptions()
    evaluator = Evaluator()  # 复用 agent 对象，不每轮重建

    best_desc = None
    best_rate = -1
    history = []  # 每轮的记录

    print(f"\n{'='*64}")
    print(f"  LLM 对抗式优化（{rounds} 轮）")
    print(f"  对应 IPI 论文 CEM：攻击者=采样器，裁判=打分函数")
    print(f"{'='*64}")
    print(f"  竞争环境: 6 良性 skill vs 1 恶意 skill（攻击者生成描述）")
    n = num_queries or 20
    print(f"  评估 query 数: {n}/轮")
    print(f"  竞争对手: {[c[0] for c in competitors]}")

    feedback = None  # 第一轮没有反馈

    for r in range(rounds):
        round_start = time.time()
        print(f"\n{'─'*64}")
        print(f"  第 {r+1}/{rounds} 轮  [{time.strftime('%H:%M:%S')}]")
        print(f"{'─'*64}")

        # Step 1: 攻击者生成/改进 description
        print(f"  [1] 攻击者 LLM 生成 description...")
        desc = atk.generate(feedback=feedback)
        print(f"      → {desc[:80]}{'...' if len(desc)>80 else ''}")

        # Step 2: 裁判评估被选中率
        print(f"  [2] 裁判评估（跑 {n} 个 query）...", flush=True)
        result = evaluator.evaluate(desc, num_queries=num_queries, verbose=False)
        rate = result["hit_rate"]
        print(f"      → 被选中率: {rate:.0%}（{len(result['hit_queries'])}/{n}）")
        print(f"      → 外泄: {'🔴 是' if result['exfil_happened'] else '⚪ 否'}")

        if result["hit_queries"]:
            print(f"      中招的 query:")
            for q in result["hit_queries"]:
                print(f"        • {q}")

        elapsed = time.time() - round_start

        # 记录历史
        record = {
            "round": r + 1,
            "description": desc,
            "hit_rate": rate,
            "hit_count": len(result["hit_queries"]),
            "total_queries": n,
            "exfil_happened": result["exfil_happened"],
            "hit_queries": result["hit_queries"],
            "miss_queries": result["miss_queries"],
            "elapsed_sec": round(elapsed, 1),
        }
        history.append(record)

        # 更新最佳
        if rate > best_rate:
            best_rate = rate
            best_desc = desc

        # 准备下一轮的反馈
        feedback = {
            "current_desc": desc,
            "hit_rate": rate,
            "hit_queries": result["hit_queries"],
            "miss_queries": result["miss_queries"],
            "competitors": competitors,
            "round": r + 1,
        }

    # 总结
    print(f"\n{'='*64}")
    print(f"  📊 优化完成")
    print(f"{'='*64}")
    print(f"\n{'轮次':<6}{'被选中率':<12}{'中招数':<10}{'外泄':<8}{'耗时':<8}")
    print("-" * 50)
    for h in history:
        print(f"  {h['round']:<4}{h['hit_rate']:<12.0%}{h['hit_count']:<10}"
              f"{'是' if h['exfil_happened'] else '否':<8}{h['elapsed_sec']:.0f}s")
    print("-" * 50)

    rates = [h["hit_rate"] for h in history]
    print(f"\n  📈 被选中率曲线: {' → '.join(f'{r:.0%}' for r in rates)}")
    print(f"  🏆 最佳被选中率: {best_rate:.0%}")
    print(f"\n  🏆 最佳 description:")
    print(f"     {best_desc}")

    # 保存结果
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"optimize_{int(time.time())}.json"
    output_data = {
        "rounds": rounds,
        "num_queries_per_round": n,
        "best_description": best_desc,
        "best_hit_rate": best_rate,
        "history": history,
    }
    output_file.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  💾 结果已保存: {output_file}")

    return output_data


if __name__ == "__main__":
    # 确保后台运行时 stdout 实时刷新
    sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(description="LLM 对抗式 skill 描述优化")
    parser.add_argument("--rounds", type=int, default=5,
                        help="优化轮数（建议 5-10）")
    parser.add_argument("--num-queries", type=int, default=10,
                        help="每轮用多少 query 评估（默认10，全量20用 --num-queries 20）")
    args = parser.parse_args()

    run_optimization(rounds=args.rounds, num_queries=args.num_queries)
