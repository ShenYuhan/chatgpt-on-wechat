import threading

import numpy as np
from .utils.utils import make_prompt
from .file_loader.file_loader import FileLoader
from .embedding.EB_embed_v1 import ErnieEncodeText
from .vector_store.vector_store import DBUtils
from .config import config


class ErnieBotPdfQA(object):
    __instance = None
    __first_init = True
    def __new__(cls, *args, **kwargs):
        if cls.__instance == None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        if self.__first_init:
            print("只初始化一次")
            self.config = config
            self.loader = FileLoader()
            self.embedding_extract = ErnieEncodeText()
            self.db_tools = DBUtils(self.config.get("db_path", "DefaultVector.db"))
            self.__class__.__first_init = False
    def retrieve(self, query, prompt=""):
        if prompt == "":
            prompt = "请根据以下内容，来回答该问题$query, 内容为：$context\n如果文中没有答案，请回答“没找到答案”\n"
        
        query_embedding = self.embedding_extract(query)
        search_top = 5
        search_res, search_elapse = self.db_tools.search_local(query_embedding, top_k=search_top)
        if search_res is None:
            context = "未搜索到相关信息，请结合你自己的认知回答"
        else:
            for file, content in search_res.items():
                content = "\n".join(content)
            context = "\n".join(sum(search_res.values(), []))
        prompt_msg = make_prompt(query, context, prompt)
        response = self.embedding_extract.chat_completions(prompt_msg, history=None)
        
        if not response:
            response = "Sorry, I didn't answer the question correctly."
        return response
    
    def persist(self, filepath):
        all_doc_content = self.loader(filepath)
        batch_size = self.config.get("encoder_batch_size", 32)
        max_content_len = self.config.get("max_content_len", 300)
        all_embeddings = []
        for file_name, file_content in all_doc_content.items():
            content_nums = len(file_content)
            for i in range(0, content_nums, batch_size):
                start_idx = i
                end_idx = start_idx + batch_size
                end_idx = content_nums if end_idx > content_nums else end_idx

                cur_contents = file_content[start_idx:end_idx]
                for one_content in cur_contents:
                    len_content = len(one_content)

                    if len_content <= max_content_len:
                        embeddings = self.embedding_extract(one_content)
                        # TODO: 这里永远执行不到
                        if embeddings is None or embeddings.shape != (1, 384) or embeddings.size == 0:
                            continue
                        all_embeddings.append(embeddings)
                    else:
                        for j in range(0, len_content, max_content_len):
                            s_content = j
                            e_content = s_content + max_content_len
                            e_content = (
                                len_content if e_content > len_content else e_content
                            )

                            part_content = one_content[s_content:e_content]
                            embeddings = self.embedding_extract(part_content)
                            if embeddings is None or embeddings.shape != (1, 384) or embeddings.size == 0:
                                continue
                            all_embeddings.append(embeddings)
            if all_embeddings:
                all_embeddings = np.vstack(all_embeddings)
                self.db_tools.insert(file_name, all_embeddings, file_content, "")