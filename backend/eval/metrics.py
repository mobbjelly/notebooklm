"""
RAG 评测指标

keyword_recall 提取逻辑（优先级依次降低）：
  1. 数字（整数/小数）—— 财务文档最可靠的锚点
  2. 引号内内容（中英文引号）
  3. 顿号分隔的列表项（"A、B、C等"）
  4. 动词短语（"提及/判断为/回答为" 后首 4 个汉字）
  5. 无法提取 → 跳过该条，不计入分母

每条 eval_criteria = 一次检验，所有提取片段必须同时出现在答案中才算通过。
返回 (通过数 / 可评数)，并附 breakdown 供调试。
"""
import re


def _criterion_passes(answer: str, criterion: str) -> bool | None:
    # 1. 数字（含小数）
    numbers = re.findall(r'\d+(?:\.\d+)?', criterion)
    if numbers:
        return all(n in answer for n in numbers)

    # 2. 引号内内容
    quoted = re.findall(r'["""\'](.*?)["""\']', criterion)
    if quoted:
        return all(q in answer for q in quoted)

    # 3. 顿号列表或"等"前的词组
    dun_items = re.findall(r'([一-鿿]{2,8})(?:、|(?=等))', criterion)
    if dun_items:
        return all(item in answer for item in dun_items)

    # 4. 动词后短语（取前 4 汉字作锚点）
    for verb in ['提及', '判断为', '回答为', '区分']:
        m = re.search(rf'(?<={verb})([一-鿿]{{2,}})', criterion)
        if m:
            anchor = m.group(1)[:4]
            return anchor in answer

    return None  # 无法提取，跳过


def keyword_recall(answer: str, criteria: list[str]) -> tuple[float, list[dict]]:
    if not criteria:
        return -1.0, []
    breakdown = [
        {"criterion": c, "passed": _criterion_passes(answer, c)}
        for c in criteria
    ]
    scorable = [b for b in breakdown if b["passed"] is not None]
    if not scorable:
        return -1.0, breakdown
    score = round(sum(b["passed"] for b in scorable) / len(scorable), 4)
    return score, breakdown


def rouge_l(answer: str, reference: str) -> float:
    """字符级 ROUGE-L F1（适合中文，无需分词）。"""
    if not reference or not answer:
        return -1.0
    a, r = list(answer), list(reference)
    m, n = len(a), len(r)
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            curr[j] = prev[j - 1] + 1 if a[i-1] == r[j-1] else max(prev[j], curr[j-1])
        prev = curr
    lcs = prev[n]
    p, r_ = lcs / m, lcs / n
    if p + r_ == 0:
        return 0.0
    return round(2 * p * r_ / (p + r_), 4)


def citation_stats(answer: str) -> dict:
    refs = re.findall(r'\[\d+\]', answer)
    return {"has_citation": len(refs) > 0, "citation_count": len(refs)}


def retrieval_scores(citations: list[dict]) -> dict:
    scores = [c["score"] for c in citations if "score" in c]
    if not scores:
        return {"retrieval_top1": -1.0, "retrieval_avg": -1.0}
    return {
        "retrieval_top1": round(scores[0], 4),
        "retrieval_avg": round(sum(scores) / len(scores), 4),
    }


_REFUSAL = ["文档中未提及", "未找到相关内容", "文档中没有", "无法从文档中"]


def faithfulness(answer: str) -> bool:
    return not any(p in answer for p in _REFUSAL)


def compute(
    answer: str,
    citations: list[dict],
    reference: str,
    eval_criteria: list[str],
) -> dict:
    kr_score, kr_breakdown = keyword_recall(answer, eval_criteria)
    return {
        "answer_length": len(answer),
        "keyword_recall": kr_score,
        "criteria_breakdown": kr_breakdown,
        "rouge_l": rouge_l(answer, reference),
        "faithfulness": faithfulness(answer),
        **citation_stats(answer),
        **retrieval_scores(citations),
    }
