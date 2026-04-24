"""
对比 SQLite 与 ChromaDB，删除孤儿向量（ChromaDB 中有记录，但 SQLite documents 表中已不存在对应 doc_id）。
用法：在 backend/ 目录下执行
    python scripts/cleanup_orphan_vectors.py
加 --dry-run 只打印不删除。
"""
import argparse
import sqlite3
import sys
from pathlib import Path

# 确保能 import 项目模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chromadb import PersistentClient
from core.config import settings


def get_valid_doc_ids() -> set[int]:
    db_path = settings.DATABASE_URL.split("///")[-1]
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id FROM documents").fetchall()
    conn.close()
    return {row[0] for row in rows}


def cleanup(dry_run: bool):
    valid_ids = get_valid_doc_ids()
    print(f"SQLite 中有效 doc_id 数量: {len(valid_ids)}")

    client = PersistentClient(path=str(settings.CHROMA_DIR))
    collections = client.list_collections()

    total_deleted = 0
    for col in collections:
        collection = client.get_collection(col.name)
        result = collection.get(include=["metadatas"])
        ids = result["ids"]
        metadatas = result["metadatas"]

        orphan_ids = [
            vec_id
            for vec_id, meta in zip(ids, metadatas)
            if meta is None or int(meta.get("doc_id", -1)) not in valid_ids
        ]

        if not orphan_ids:
            print(f"[{col.name}] 无孤儿向量")
            continue

        print(f"[{col.name}] 发现 {len(orphan_ids)} 个孤儿向量", end="")
        if dry_run:
            orphan_doc_ids = {
                meta.get("doc_id") for meta in metadatas
                if meta and int(meta.get("doc_id", -1)) not in valid_ids
            }
            print(f"（dry-run，跳过删除）。孤儿 doc_id: {orphan_doc_ids}")
        else:
            collection.delete(ids=orphan_ids)
            total_deleted += len(orphan_ids)
            print(f"，已删除。")

    if not dry_run:
        print(f"\n共删除 {total_deleted} 个孤儿向量。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只打印，不实际删除")
    args = parser.parse_args()
    cleanup(dry_run=args.dry_run)
