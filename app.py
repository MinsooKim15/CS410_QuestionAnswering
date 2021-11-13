import os
import json

import click
from jina import Flow, Document
import pandas as pd
import numpy as np
import json
import pickle
import copy
import requests
import time
import jina
from jina import Document, DocumentArray
## 루트 path를 가져오기 위함
tmp = os.getcwd().split('/')
HOME_PATH = '/'.join(tmp[:tmp.index('CS410_QuestionAnswering')])

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)
    
    
def config(workspace):
    os.environ["JINA_DATA_FILE"] = os.environ.get(
        "JINA_DATA_FILE", "data/crawling/example.json"
    )
    os.environ["JINA_WORKSPACE"] =  os.environ.get("JINA_WORKSPACE", workspace)

    os.environ["JINA_PORT"] = os.environ.get("JINA_PORT", str(1234))
    
        
def print_topk(resp, sentence):
    final_result = list()
    for d in resp.data.docs:
        print(f"Ta-DahðŸ”®, here are what we found for: {sentence}")
        while len(final_result) < 10:   
            for idx, match in enumerate(d.matches):
                answer_list = match.tags['answer'].split('\t')
                if len(answer_list) > 0:
                    for ans in answer_list:
                        score = match.scores['cosine'].value # rerankí• ë•Œë§Œ #faiss
                        final_result.append((idx, score, match.text, ans))
                        #print(f'> {idx:>2d}({score:.2f}). {match.text} : {ans}')
                else:
                    final_result.append((idx, score, match.text, answer_list[0]))
        print(len(final_result))
        for idx, score, text, ans in final_result[:5]:
            print(f'> {idx:>2d}({score:.2f}). {text} : {ans}')
            


def _pre_processing(data_path):
    print('start of pre-processing')
    results = []
    f = open(data_path, 'rt')
    documents = json.load(f)
    for doc in documents:
        try:
            d = {'id': doc['id'], 'title': doc['title'], 'question':  doc['content'], 'answer': list(map(lambda x: x['content'], doc['replyList']))[0]}

        except:
            d = {'id': doc['id'], 'title': doc['title'], 'question':  doc['content'], 'answer': ''}
        results.append(Document(json.dumps(d, ensure_ascii=False)))
    return results

def index():
    f = Flow().load_config("flows/index.yml").plot(output='index.svg')
    work_place = os.path.join(os.path.dirname(__file__),
                              os.environ.get('JINA_WORKSPACE', None))

    with f:
        data_path = os.path.join(os.path.dirname(__file__),
                                 os.environ.get('JINA_DATA_FILE', None))
        f.post('/index',
               _pre_processing(data_path),
               show_progress=True,
               parameters={'traversal_paths': ['r', 'c']})
        f.post('/dump',
               target_peapod='KeyValIndexer',
               parameters={
                   'dump_path': os.path.join(work_place, 'dumps/'),
                   'shards': 1,
                   'timeout': -1
               })

            
def query(top_k, query_flow):
    f = Flow().load_config(query_flow).plot(
        output='query.svg')
    with f:
        #f.post('/load', parameters={'model_path': 'model/bert-v1'})
        while True:
            text = input("Please type a sentence: ")
            if not text:
                break

            def ppr(x):
                print_topk(x, text)

            f.search(Document(text=text),
                     parameters={
                         'top_k': top_k
                         #'model_path': 'model/bert-v1'
                     },
                     on_done=ppr)

def train():
    f = Flow().load_config("flows/train.yml").plot(output='train.svg')
    with f:
        data_path = os.path.join(os.path.dirname(__file__), os.environ.get('JINA_DATA_FILE', None))
        f.post('/train', _pre_processing(data_path), show_progress=True, parameters={'traversal_paths': ['r', 'c']}, request_size=0)


        
def query_restful(query_flow):
    f = jina.Flow().load_config(query_flow,
                           override_with={
                               'protocol': 'http',
                               'port_expose': int(os.environ["JINA_PORT"])
                           })
    with f:
        f.post('/load', parameters={'model_path': f'{HOME_PATH}/CS410_QuestionAnswering/model/kobert-v2/'})
        f.block()
     

def dryrun():
    f = Flow().load_config("flows/index.yml")
    with f:
        f.dry_run()

def dump():
    f = Flow().add(uses='pods/keyval_lmdb.yml').plot(output='dump.svg')
    with f:
        f.post('/dump',
               parameters={
                   'dump_path': 'dumps/',
                   'shards': 1,
                   'timeout': -1
               })

@click.command()
@click.option(
    "--task",
    "-t",
    type=click.Choice(
        ["index", "query", "query_restful", "dryrun", "dump", "train"], case_sensitive=False
    ),
)
@click.option("--top_k", "-k", default=5)
@click.option('--query_flow', type=click.Path(exists=True), default='flows/query.yml')
@click.option("--workspace", "-w", default="workspace")
def main(task, top_k, query_flow, workspace):
    config(workspace)
    workspace = os.environ["JINA_WORKSPACE"]
    print(os.environ["JINA_DATA_FILE"])
    if task == "index":
        if os.path.exists(workspace):
            print(f'\n +----------------------------------------------------------------------------------+ \
                    \n |                                   ðŸ¤–ðŸ¤–ðŸ¤–                                         | \
                    \n | The directory {workspace} already exists. Please remove it before indexing again.  | \
                    \n |                                   ðŸ¤–ðŸ¤–ðŸ¤–                                         | \
                    \n +----------------------------------------------------------------------------------+')
        index()
    if task == "query":
        if not os.path.exists(workspace):
            print(f"The directory {workspace} does not exist. Please index first via `python app.py -t index`")
        query(top_k, query_flow)
    if task == "query_restful":
        if not os.path.exists(workspace):
            print(f"The directory {workspace} does not exist. Please index first via `python app.py -t index`")
        query_restful(query_flow)
    if task == "dryrun":
        dryrun()
    if task == "dump":
        dump()
    if task == "train":
        train()

if __name__ == "__main__":
    main()
    from jina.logging.logger import JinaLogger
    from jina.parsers import set_gateway_parser
    