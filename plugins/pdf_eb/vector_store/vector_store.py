# -*- encoding: utf-8 -*-
# @Author: SWHL
# @Contact: liekkaskono@163.com
import io
import sqlite3
import time
from typing import Dict, List, Optional

import faiss
import numpy as np


def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())


def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out, allow_pickle=True)


sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("array", convert_array)


class DBUtils:
    def __init__(
        self,
        db_path: str,
    ) -> None:
        self.db_path = db_path

        self.table_name = "embedding_texts"
        self.vector_nums = 0

        self.max_prompt_length = 4096

        self.connect_db()

    def connect_db(
        self,
    ):
        con = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute(
            f"create table if not exists {self.table_name} (id integer primary key autoincrement, file_name TEXT, embeddings array UNIQUE, texts TEXT, uids TEXT)"
        )
        print(f"create table if not exists {self.table_name} (id integer primary key autoincrement, file_name TEXT, embeddings array UNIQUE, texts TEXT, uids TEXT)")
        return cur, con

    def load_vectors(
        self, uid: Optional[str] = None
    ):
        cur, _ = self.connect_db()

        search_sql = f'select file_name, embeddings, texts from {self.table_name}'
        if uid:
            search_sql = f'select file_name, embeddings, texts from {self.table_name} where uids="{uid}"'

        cur.execute(search_sql)
        all_vectors = cur.fetchall()
        print("search_sql =", search_sql, " all_vectors=", all_vectors)

        self.file_names = np.vstack([v[0] for v in all_vectors]).squeeze()
        all_embeddings = np.vstack([v[1] for v in all_vectors])
        print("all_embeddings.shape = ", all_embeddings.shape)
        self.all_texts = np.vstack([v[2] for v in all_vectors]).squeeze()
        print("self.all_texts.shape = ", self.all_texts.shape)

        self.search_index = faiss.IndexFlatL2(all_embeddings.shape[1])
        self.search_index.add(all_embeddings)
        self.vector_nums = len(all_vectors)

    def count_vectors(
        self,
    ):
        cur, _ = self.connect_db()

        cur.execute(f"select file_name from {self.table_name}")
        all_vectors = cur.fetchall()
        return len(all_vectors)

    def search_local(
        self,
        embedding_query: np.ndarray,
        top_k: int = 5,
        uid: Optional[str] = None,
    ) -> Optional[Dict[str, List[str]]]:
        s = time.perf_counter()

        cur_vector_nums = self.count_vectors()
        if cur_vector_nums <= 1:
            return None, 0

        if cur_vector_nums != self.vector_nums:
            self.load_vectors(uid)

        _, I = self.search_index.search(embedding_query, top_k)
        top_index = I.squeeze().tolist()
        search_contents = self.all_texts[top_index]
        file_names = [self.file_names[idx] for idx in top_index]
        dup_file_names = list(set(file_names))
        dup_file_names.sort(key=file_names.index)

        search_res = {v: [] for v in dup_file_names}
        # {"1.pdf": [], "2.pdf": []}
        for file_name, content in zip(file_names, search_contents):
            search_res[file_name].append(content)
        # {"1.pdf": [1, 2,3 ], "2.pdf": [4, 5]}

        elapse = time.perf_counter() - s
        return search_res, elapse

    def insert(self, file_name: str, embeddings: np.ndarray, texts: List[str], uid: str):
        cur, con = self.connect_db()

        file_names = [file_name] * len(embeddings)
        uids = [uid] * len(embeddings)
        t1 = time.perf_counter()
        insert_sql = f"insert or ignore into {self.table_name} (file_name, embeddings, texts, uids) values (?, ?, ?, ?)"
        cur.executemany(insert_sql, list(zip(file_names, embeddings, texts, uids)))
        con.commit()
        elapse = time.perf_counter() - t1
        print(
            f"Insert {len(embeddings)} data, total is {len(embeddings)}, cost: {elapse:4f}s"
        )

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.cur.close()
        self.con.close()