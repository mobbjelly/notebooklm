"""
KnowBase RAG 评测脚本

用法：
    # 在 backend/ 目录下，激活虚拟环境后运行
    python -m eval.evaluate \
        --cases eval/test_cases.json \
        --notebook_id 1 \
        --base_url http://localhost:8000 \
        --client_id <your-client-id> \
        [--doc_ids 1 2 3] \
        [--output eval/results.json] \
        [--concurrency 3]

输出：
    - 终端打印每条用例得分和汇总表
    - JSON 文件（--output 指定路径）保存完整结果
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

# 将 backend/ 加入 sys.path，使 eval.metrics 可被直接导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval.metrics import compute  # noqa: E402


# ── SSE 流式请求，收集完整回答和 citations ────────────────────────────────────

async def call_rag(
    client: httpx.AsyncClient,
    base_url: str,
    client_id: str,
    notebook_id: int,
    question: str,
    doc_ids: Optional[list[int]],
) -> tuple[str, list[dict], float]:
    """
    返回 (answer_text, citations, latency_seconds)
    """
    url = f"{base_url}/api/notebooks/{notebook_id}/chat"
    payload = {"question": question, "doc_ids": doc_ids}
    headers = {"X-Client-ID": client_id, "Accept": "text/event-stream"}

    answer_parts: list[str] = []
    citations: list[dict] = []
    t0 = time.perf_counter()

    async with client.stream("POST", url, json=payload, headers=headers, timeout=120) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            data = json.loads(line[5:].strip())
            if "text" in data:
                answer_parts.append(data["text"])
            if data.get("done") and "citations" in data:
                citations = data["citations"]

    latency = time.perf_counter() - t0
    return "".join(answer_parts), citations, round(latency, 3)


# ── 单条用例评测 ──────────────────────────────────────────────────────────────

async def eval_case(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    base_url: str,
    client_id: str,
    notebook_id: int,
    default_doc_ids: Optional[list[int]],
    case: dict,
) -> dict:
    doc_ids = case.get("doc_ids") or default_doc_ids
    async with sem:
        try:
            answer, citations, latency = await call_rag(
                client, base_url, client_id, notebook_id,
                case["question"], doc_ids,
            )
            error = None
        except Exception as e:
            answer, citations, latency, error = "", [], 0.0, str(e)

    scores = compute(
        answer=answer,
        citations=citations,
        reference=case.get("answer", ""),
        eval_criteria=case.get("eval_criteria", []),
    )

    return {
        "id": case["id"],
        "category": case.get("category", ""),
        "question": case["question"],
        "reference_answer": case.get("answer", ""),
        "model_answer": answer,
        "citations": citations,
        "latency_s": latency,
        "error": error,
        "scores": scores,
    }


# ── 汇总统计 ──────────────────────────────────────────────────────────────────

def summarize(results: list[dict]) -> dict:
    valid = [r for r in results if r["error"] is None]
    if not valid:
        return {"error": "all cases failed"}

    def avg(key):
        vals = [r["scores"][key] for r in valid if r["scores"].get(key, -1) >= 0]
        return round(sum(vals) / len(vals), 4) if vals else -1.0

    def pct(key):
        vals = [r["scores"][key] for r in valid]
        return round(sum(vals) / len(vals), 4) if vals else -1.0

    # 按分类聚合 keyword_recall
    by_cat: dict[str, list[float]] = {}
    for r in valid:
        cat = r["category"]
        kr = r["scores"].get("keyword_recall", -1)
        if kr >= 0:
            by_cat.setdefault(cat, []).append(kr)
    category_recall = {
        cat: round(sum(vals) / len(vals), 4)
        for cat, vals in by_cat.items()
    }

    return {
        "total": len(results),
        "success": len(valid),
        "failed": len(results) - len(valid),
        "avg_latency_s": round(sum(r["latency_s"] for r in valid) / len(valid), 3),
        "avg_keyword_recall": avg("keyword_recall"),
        "avg_rouge_l": avg("rouge_l"),
        "citation_rate": pct("has_citation"),
        "avg_citation_count": round(sum(r["scores"]["citation_count"] for r in valid) / len(valid), 2),
        "faithfulness_rate": pct("faithfulness"),
        "avg_retrieval_top1": avg("retrieval_top1"),
        "avg_retrieval_avg": avg("retrieval_avg"),
        "keyword_recall_by_category": category_recall,
    }


# ── 终端打印 ──────────────────────────────────────────────────────────────────

def print_results(results: list[dict], summary: dict):
    sep = "-" * 100
    print(f"\n{'=' * 100}")
    print(f"  KnowBase RAG 评测报告  |  共 {summary['total']} 条，成功 {summary['success']} 条，失败 {summary['failed']} 条")
    print(f"{'=' * 100}")

    for r in results:
        s = r["scores"]
        status = "✗ ERROR" if r["error"] else "✓"
        print(f"\n[{status}] #{r['id']} [{r['category']}]  耗时 {r['latency_s']}s")
        print(f"  问题  : {r['question']}")
        if r["error"]:
            print(f"  错误  : {r['error']}")
            continue
        print(f"  回答  : {r['model_answer'][:120]}{'...' if len(r['model_answer']) > 120 else ''}")
        print(f"  得分  | keyword_recall={s['keyword_recall']:>6}  rouge_l={s['rouge_l']:>6}  "
              f"citations={s['citation_count']}  retrieval_top1={s['retrieval_top1']:>6}  faithful={s['faithfulness']}")
        for b in s.get("criteria_breakdown", []):
            mark = "✓" if b["passed"] else ("?" if b["passed"] is None else "✗")
            print(f"    [{mark}] {b['criterion']}")
        print(sep)

    print(f"\n{'=' * 100}")
    print("  汇总")
    print(f"{'=' * 100}")
    print(f"  平均关键词召回    : {summary['avg_keyword_recall']}")
    print(f"  平均 ROUGE-L      : {summary['avg_rouge_l']}")
    print(f"  引用覆盖率        : {summary['citation_rate']}")
    print(f"  平均引用数        : {summary['avg_citation_count']}")
    print(f"  忠实性（不拒答）  : {summary['faithfulness_rate']}")
    print(f"  平均检索相关性    : top1={summary['avg_retrieval_top1']}  avg={summary['avg_retrieval_avg']}")
    print(f"  平均响应延迟      : {summary['avg_latency_s']}s")
    print("\n  各类别关键词召回：")
    for cat, score in summary["keyword_recall_by_category"].items():
        print(f"    {cat:<35}: {score}")
    print()


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="KnowBase RAG 评测")
    parser.add_argument("--cases",       default="eval/test_cases.json", help="测试用例 JSON 路径")
    parser.add_argument("--notebook_id", type=int, required=True,        help="目标 Notebook ID")
    parser.add_argument("--base_url",    default="http://localhost:8000", help="后端服务地址")
    parser.add_argument("--client_id",   required=True,                  help="X-Client-ID（浏览器 localStorage 中的 UUID）")
    parser.add_argument("--doc_ids",     type=int, nargs="*",            help="限定检索的文档 ID（不填则检索全部）")
    parser.add_argument("--output",      default=None,                   help="结果 JSON 输出路径")
    parser.add_argument("--concurrency", type=int, default=3,            help="并发请求数（默认 3）")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    if not cases_path.exists():
        print(f"[ERROR] 找不到测试用例文件: {cases_path}", file=sys.stderr)
        sys.exit(1)

    dataset = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = dataset.get("test_cases", dataset) if isinstance(dataset, dict) else dataset
    print(f"加载测试集：{dataset.get('dataset_name', cases_path.name)}，共 {len(cases)} 条用例")

    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [
            eval_case(sem, client, args.base_url, args.client_id,
                      args.notebook_id, args.doc_ids, case)
            for case in cases
        ]
        results = await asyncio.gather(*tasks)

    results = sorted(results, key=lambda r: r["id"])
    summary = summarize(results)
    print_results(results, summary)

    output_path = Path(args.output) if args.output else None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"结果已保存至 {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
