# coding=utf-8
# Modified MIT License

# Software Copyright (c) 2021 Heewon Jeon, Jina AI

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# The above copyright notice and this permission notice need not be included
# with content created by the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import re
import os
from typing import Dict, List, Optional, Tuple
from jina.types.document import DocumentSourceType
from sentence_transformers import SentenceTransformer, util
import numpy as np
import pytorch_lightning as pl
import torch
from jina import Document, DocumentArray, Executor, requests
from jina.logging.logger import JinaLogger
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina_commons.batching import get_docs_batch_generator
from kobart import get_kobart_tokenizer, get_pytorch_kobart_model
from transformers import BartModel, PreTrainedTokenizerFast
from jinahub.indexers.storage.LMDBStorage import LMDBStorage
from jinahub.indexers.searcher.AnnoySearcher.annoy_searcher import AnnoySearcher
from jinahub.indexers.searcher.HnswlibSearcher import HnswlibSearcher
from jinahub.indexers.searcher.FaissSearcher import FaissSearcher
import pandas as pd
import copy
import json
import pickle
import os 
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn as nn
from bm25 import *
## 루트 path를 가져오기 위함
tmp = os.getcwd().split('/')
HOME_PATH = '/'.join(tmp[:tmp.index('CS410_QuestionAnswering')])
## 기존 sentence kobart
TOK_PATH = f'{HOME_PATH}/a2a-engine-qahistory/model/emji_tokenizer/model.json'
KOBART_PATH = f'{HOME_PATH}/a2a-engine-qahistory/model/kobart'
SKOBART_PATH = f'{HOME_PATH}/a2a-engine-qahistory/model/SentenceBERT.bin'
## 새로운 sentence kobart
MORPHS_TOK_PATH = ''
NEW_SKOBART_PATH = ''
HPARAMS_PATH = ''
 
         
def http_find(string):
        # findall() has been used 
        # with valid conditions for urls in string
        string = string.replace(":::", "<TEMPORARY>")
        regex = r"(?i)\b((?:http?|://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»""'']))"
        url = re.findall(regex, string) 
        
        return list(map(lambda x: x[0], url))#url[0][0]
    
def preprocess_url(text, replaced='<URL>'):
    url_list = http_find(text)
    for url in url_list:
        text = text.replace(url, replaced)
    return text, url_list


class Preprocess(Executor):
    def __init__(self, default_traversal_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_traversal_path = default_traversal_path or ['r']

#     @requests(on=['/index'])
#     def preprocess(self, docs: DocumentArray, parameters: Dict, **kwargs):
#         traversal_path = parameters.get('traversal_paths',
#                                         self.default_traversal_path)
#         f_docs = docs.traverse_flat(traversal_path)
#         for doc in f_docs:
#             try:
#                 doc.text = doc.tags__title + '/n' + doc.tags__question
#             except:
#                 print('except')
#                 pass
    @requests(on=['/search'])
    def preprocess(self, docs: DocumentArray, parameters: Dict, **kwargs):
        traversal_path = parameters.get('traversal_paths',
                                        self.default_traversal_path)
        f_docs = docs.traverse_flat(traversal_path)
        for doc in f_docs:
            print(doc.text)

class SentenceBERT(Executor):
    def __init__(
        self,
        pretrained_model_path: str = '/home/x1112373z/CS410_QuestionAnswering/sentence-transformers/all-mpnet-base-v2/',
        max_length: int = 128,
        device: str = 'cuda',
        default_traversal_paths: Optional[List[str]] = None,
        default_batch_size: int = 32,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if default_traversal_paths is not None:
            self.default_traversal_paths = default_traversal_paths
        else:
            self.default_traversal_paths = ['r']
        self.max_length = max_length
        self.pretrained_model_path = pretrained_model_path
        self.default_batch_size = default_batch_size
        self.logger = JinaLogger(self.__class__.__name__)
        if not device in ['cpu', 'cuda']:
            self.logger.error(
                'Torch device not supported. Must be cpu or cuda!')
            raise RuntimeError(
                'Torch device not supported. Must be cpu or cuda!')
        if device == 'cuda' and not torch.cuda.is_available():
            self.logger.warning(
                'You tried to use GPU but torch did not detect your'
                'GPU correctly. Defaulting to CPU. Check your CUDA installation!'
            )
        self.device = device
        try:
            self.model = SentenceTransformer('/home/x1112373z/CS410_QuestionAnswering/sentence-transformers/all-mpnet-base-v2/')
        except:
            # wget https://public.ukp.informatik.tu-darmstadt.de/reimers/sentence-transformers/v0.2/all-mpnet-base-v2.zip
            # unzip if not possible to to this
            self.model = SentenceTransformer(self.pretrained_model_)
        self.tokenizer = self.model.tokenizer

        self.model.eval()
        self.model.to(torch.device(device))

    @requests
    def encode(self, docs: Optional[DocumentArray], parameters: Dict,
               **kwargs):
        """
        Encode text data into a ndarray of `D` as dimension, and fill the embedding of each Document.
        :param docs: DocumentArray containing text
        :param parameters: dictionary to define the `traversal_paths` and the `batch_size`. For example,
               `parameters={'traversal_paths': ['r'], 'batch_size': 10}`.
        :param kwargs: Additional key value arguments.
        """
        def mean_pooling(model_output, attention_mask):
            token_embeddings = model_output['token_embeddings'] #First element of model_output contains all token embeddings
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            token_embeddings = token_embeddings.cuda()
            input_mask_expanded = input_mask_expanded.cuda()
            return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

        for batch in get_docs_batch_generator(
                docs,
                traversal_path=parameters.get('traversal_paths',
                                              self.default_traversal_paths),
                batch_size=parameters.get('batch_size',
                                          self.default_batch_size),
                needs_attr='text',
        ):
            texts = batch.get_attributes('text')
            processed_content = []
            for cont in texts:
                processed_content.append(self.tokenizer.bos_token + cont + self.tokenizer.eos_token)
            
            print(processed_content)
            encoded_input = self.tokenizer(list(processed_content),
                                            return_tensors='pt',
                                            max_length=self.max_length,
                                            padding=True, truncation=True)

            with torch.no_grad():
                model_output = self.model({'input_ids': torch.tensor(encoded_input['input_ids']).clone().detach().cuda(), 'attention_mask': torch.tensor(encoded_input['attention_mask']).clone().detach().cuda()} )
                if self.device == 'cuda':
                    embedding = mean_pooling(model_output, encoded_input['attention_mask'])
                    
                elif self.device == 'cpu':
                    embedding = mean_pooling(model_output, encoded_input['attention_mask'])
                else:
                    assert False
            
            for doc, embed in zip(batch, embedding):
                doc.embedding = embed.cpu().detach().numpy()


class Segmenter(Executor):
    def __init__(self,
                 min_sent_len: int = 1,
                 max_sent_len: int = 512,
                 punct_chars: Optional[List[str]] = None,
                 uniform_weight: bool = True,
                 default_traversal_path: Optional[List[str]] = None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.min_sent_len = min_sent_len
        self.max_sent_len = max_sent_len
        self.punct_chars = punct_chars
        self.uniform_weight = uniform_weight
        self.logger = JinaLogger(self.__class__.__name__)
        self.default_traversal_path = default_traversal_path or ['r']
        if not punct_chars:
            self.punct_chars = [
                '!', '.', '?', '։', '؟', '۔', '܀', '܁', '܂', '‼', '‽', '⁇',
                '⁈', '⁉', '⸮', '﹖', '﹗', '！', '．', '？', '｡', '。', '\n'
            ]
        if self.min_sent_len > self.max_sent_len:
            self.logger.warning(
                'the min_sent_len (={}) should be smaller or equal to the max_sent_len (={})'
                .format(self.min_sent_len, self.max_sent_len))
        self._slit_pat = re.compile('\s*([^{0}]+)(?<!\s)[{0}]*'.format(''.join(
            set(self.punct_chars))))

    def _split(self, text: str) -> List:
        results = []
        ret = [(m.group(0), m.start(), m.end())
               for m in re.finditer(self._slit_pat, text)]
        if not ret:
            ret = [(text, 0, len(text))]
        for ci, (r, s, e) in enumerate(ret):
            f = re.sub('\n+', ' ', r).strip()
            f = f[:self.max_sent_len]
            if len(f) > self.min_sent_len:
                results.append(
                    dict(text=f,
                         offset=ci,
                         weight=1.0 if self.uniform_weight else len(f) /
                         len(text),
                         location=[s, e]))
        return results

#     @requests(on=['/index', '/search'])
#     def segment(self, docs: DocumentArray, parameters: Dict, **kwargs):
#         traversal_path = parameters.get('traversal_paths',
#                                         self.default_traversal_path)
#         f_docs = docs.traverse_flat(traversal_path)
#         for doc in f_docs:
#             chunks = self._split(doc.text)
#             for c in chunks:
#                 doc.chunks += [(Document(**c, mime_type='text/plain'))]
            


class DocVectorIndexer(Executor):
    def __init__(self, index_file_name: str, aggr_chunks: str, **kwargs):
        super().__init__(**kwargs)
        self.aggr_chunks = aggr_chunks.lower()
        self._docs = DocumentArrayMemmap(self.workspace + f'/{index_file_name}')
        self.db_embeddings = torch.tensor(self._docs.get_attributes('embedding'))
        self.db_len = int(self.db_embeddings.shape[0])
        self.cos_sim = nn.CosineSimilarity(dim=1)
        self.tokenizer = Mecab()
        self.tokenized_corpus = []  
        self.bm25 = None

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on=['/search'])
    def search(self, docs: DocumentArray, parameters: Dict, **kwargs):
        print('search from DocVectorIndexer')
        top_k = int(parameters['top_k'])
        if docs is None:
            return
        if self.bm25 is None:
            self.tokenized_corpus = [self.tokenizer.morphs(doc.text.lower()) for doc in self._docs]
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        a = np.stack(docs.get_attributes('embedding'))
        q_emb = _ext_A(_norm(a))
        # get chunk embeddings and 'min' aggr
        new_docs = []
        origin_answer_list = []
        for doc in docs:

            filtered_len = len(self._docs)
            q_embedding = torch.tensor(doc.get_attributes('embedding')).repeat(filtered_len, 1)
            dists = self.cos_sim(q_embedding, self.db_embeddings)
            sorted_ = torch.sort(dists, descending=True)
            q_tokenized = self.tokenizer.morphs(doc.text.lower())
            
            text_list = []
            for _id, _dist in zip(sorted_.indices[:top_k], sorted_.values[:top_k]):
                ii = int(_id.detach().numpy())
                print('-------answer candidate------')
                print(self._docs[ii].tags)
                print(self._docs[ii].text)
                print('------------------')


                if 0.5 <= float(_dist):
                    d = Document(text=doc.text)
                    db_tokenized = self.tokenized_corpus[ii]
                    print(db_tokenized)
                    bm_score  = round(self.bm25.get_scores(q_tokenized, db_tokenized), 3)
                    d.scores['cosine'] = round(float(_dist), 3)
                    d.tags['question'] = self._docs[ii].text
                    d.scores['bm'] = bm_score
                    d.tags['answer'] = self._docs[ii].tags__answer
                    #d.tags['id'] = self._docs[ii].tags__id
                    print('-------answer------')
                    print(d)
                    print('------------------')
                    new_docs.append(d) 
        return DocumentArray(new_docs)



class KeyValueIndexer(Executor):
    def __init__(self, aggr_chunks: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aggr_chunks = aggr_chunks.lower()
        self._docs = DocumentArrayMemmap(self.workspace + '/kv-idx')

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def query(self, docs: DocumentArray, **kwargs):
        if self.aggr_chunks == 'none':
            for doc in docs:
                for match in doc.matches:
                    extracted_doc = self._docs[match.parent_id]
                    match.update(extracted_doc)



class FilterBy(Executor):
    def __init__(self, cutoff: float = -1.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cutoff = cutoff

    @requests
    def query(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            filtered_matches = DocumentArray()
            for match in doc.matches:
                if match.scores__cosine__value >= self.cutoff:
                    filtered_matches.append(match)
            doc.matches = filtered_matches


class FaissFastSearcher(FaissSearcher):
    def __init__(self, index_file_name: str, buffer_k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.buffer_k = buffer_k
        self.logger.info(self.workspace + f'/{index_file_name}')
        self._docs = DocumentArray(
            DocumentArrayMemmap(self.workspace + f'/{index_file_name}'))
        self._docs_flat = self._docs.traverse_flat(
            self.default_traversal_paths)

    @requests(on=['/search'])
    def search(self,
               docs: DocumentArray,
               parameters: Optional[Dict] = None,
               *args,
               **kwargs):
        print('search from FaissFastSearcher')
        """Find the top-k vectors with smallest ``metric`` and return their ids in ascending order.
        :param docs: the DocumentArray containing the documents to search with
        :param parameters: the parameters for the request
        """
        if not hasattr(self, 'index'):
            self.logger.warning('Querying against an empty Index')
            return

        if parameters is None:
            parameters = {}

        top_k = parameters.get('top_k', self.default_top_k)
        traversal_paths = parameters.get('traversal_paths',
                                         self.default_traversal_paths)

        query_docs = docs.traverse_flat(traversal_paths)
        vecs = np.array(query_docs.get_attributes('embedding'))

        if self.normalize:
            from faiss import normalize_L2
            normalize_L2(vecs)
        dists, ids = self.index.search(vecs, int(top_k * self.buffer_k))
        id_score = {}
        if self.metric == 'inner_product':
            dists = 1 - dists
        for doc_idx, dist in enumerate(zip(ids, dists)):
            for m_info in zip(*dist):
                idx, distance = m_info
                idx_id = str(self._ids[int(idx)])
                p_id = self._docs_flat[idx_id].parent_id if self._docs_flat[
                    idx_id].parent_id != '' else int(idx)
                
                match = Document(self._docs[p_id], copy=True)
                match.embedding = self._vecs[int(idx)]
                if self.is_distance:
                    match.scores[self.metric] = distance
                else:
                    if self.metric == 'inner_product':
                        match.scores[self.metric] = 1 - distance
                    else:
                        match.scores[self.metric] = 1 / (1 + distance)

                if p_id not in id_score:
                    id_score[p_id] = True
                    query_docs[doc_idx].matches.append(match)
                    if len(query_docs[doc_idx].matches) >= top_k:
                        break
            if len(query_docs[doc_idx].matches) < top_k:
                self.logger.warning("Please increase 'buffer_k'")
        
def _get_ones(x, y):
    return np.ones((x, y))


def _ext_A(A):
    nA, dim = A.shape
    A_ext = _get_ones(nA, dim * 3)
    A_ext[:, dim:2 * dim] = A
    A_ext[:, 2 * dim:] = A**2
    return A_ext


def _ext_B(B):
    nB, dim = B.shape
    B_ext = _get_ones(dim * 3, nB)
    B_ext[:dim] = (B**2).T
    B_ext[dim:2 * dim] = -2.0 * B.T
    del B
    return B_ext


def _euclidean(A_ext, B_ext):
    sqdist = A_ext.dot(B_ext).clip(min=0)
    return np.sqrt(sqdist)


def _norm(A):
    return A / np.linalg.norm(A, ord=2, axis=1, keepdims=True)


def _cosine(A_norm_ext, B_norm_ext):
    return A_norm_ext.dot(B_norm_ext).clip(min=0) / 2