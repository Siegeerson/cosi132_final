# TODO: add your code for evaluation
"""
Create a command line interface in evaluate.py that runs 3 forms of each TREC query
    (title, description, narrative) against each of these retrieval options, returning the top 20 matches:
        BM25 + default analyzer
        BM25 + custom analyzer
        Reranking with fastText embeddings + default analyzer
        Reranking with sentence BERT embeddings + default analyzer
You will need to implement everything needed for evaluate.py
        (search, evaluation, command line arguments, etc) all by yourself.
The command in the script.sh is the expected form of your command line arguments,
        and you should implement the evaluate.py that can be executed using that command.
Evaluate the performance of the first 5 TREC queries from pa5_data/topics2018.xml using NDCG@20
        (implemented in metrics.py).
For each query, you should produce a 4x3 table with 1 row per search type and 1 column per query type. The value of each cell is the NDCG@20 value.
Include your results tables along with a paragraph of analysis of each table in the report.
"""
import argparse
from utils import parse_wapo_topics
from metrics import ndcg
import pprint
from elasticsearch_dsl import Search, analyzer, tokenizer
try:
    from elasticsearch_dsl.query import Match, ScriptScore, Query, MatchAll,Ids
except ImportError as e:
    print("-----Make sure ScriptScore is enabled-----")
    raise e
from elasticsearch_dsl.connections import connections
from embedding_service.client import EmbeddingClient
T_MAP = {"title":0,"description":1,"narration":2}               # Map from type of query to index of topic list
TOPIC_DICT = parse_wapo_topics("./pa5_data/topics2018.xml")     # TODO: Make os agnostic
def search(index_name,query,top_k):
    """
    Helper function to impliment search of the index
    """
    s = Search(using="default", index=index_name).query(query)[
        :top_k
    ]  # initialize a query and return top five results
    response = s.execute()
    return response

def make_vector_query(vector_name,query_text):
    """
    Helper function ot
    """
    encoder = EmbeddingClient(host="localhost",embedding_type=vector_name)
    q_encoding = encoder.encode([query_text],pooling="mean").tolist()[0]
    doc_vname = "ft_vector" if vector_name == "fasttext" else "sbert_vector"
    q_script = ScriptScore(
        query={"match": {"content":query_text}},  # use a match-all query
        script={  # script your scoring function
            "source": f"cosineSimilarity(params.query_vector, '{doc_vname}') + 2.0",
            # add 1.0 to avoid negative score
            "params": {"query_vector": q_encoding},
        },
    )
    return q_script


def run_query(index_name,topic_id,query_type,vector_name=None,top_k=20,analyzer="standard",debug=True,make_table=None):
    # debug=True
    try:
        connections.create_connection(hosts=["localhost"],alias="default")
    except Exception as e:
        print(f"encountered exception {e}")
        print("please make sure the elasticsearch server and any required embeddings servers are running")
    topic = TOPIC_DICT[str(topic_id)]  #get topic contents
    query_text = topic[T_MAP[query_type]]     #get text from topic
    print(query_text) if debug else None
    #   For text queries
    if vector_name:
        print("HERE WE GO") if debug else None
        query = make_vector_query(vector_name,query_text)
    #   For vector queries
    else:
        query = Match(content={ "query":query_text,"analyzer":analyzer})
    resp = search(index_name,query,top_k)
    scores = []
    for hit in resp:
        if debug:
            print(
                hit.meta.id, hit.meta.score, hit.annotation,hit.title, sep="\t"
                )
        scores.append(int(hit.annotation[-1]) if hit.annotation and hit.annotation[0:3]==str(topic_id) else 0)
    result_score = ndcg(scores)
    print(result_score) if debug else None
    return round(result_score,5)


def calc_table(index_name,topic_id):
    """
    Does calculation and printing of scores of various search methods
    """
    scores_list = {"BM25":[],"BM25_custom":[],"fastText":[],"Bert":[]}
    header = [f"Topic_{topic_id}"]
    for type in T_MAP:
        header.append(type)
        scores_list["BM25"].append(run_query(index_name,topic_id,type,debug=False))
        scores_list["BM25_custom"].append(run_query(index_name,topic_id,type, analyzer=get_custom_a(), debug=False))
        scores_list["fastText"].append(run_query(index_name,topic_id,type,vector_name='fasttext',debug=False))
        scores_list["Bert"].append(run_query(index_name,topic_id,type,vector_name='sbert',debug=False))


    return scores_list, header




def get_custom_a():
    custom_analyzer = analyzer(
        "custom_analyzer_mark1",
        tokenizer=tokenizer("standard"),
        filter=['snowball','lowercase','asciifolding'],
        required=False
    )
    return custom_analyzer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index_name",
        required=True,
        type=str,
        help="Name of index queried",
    )
    parser.add_argument(
        "--topic_id",
        required=True,
        type=int,
        help="Id of topic to use in query"
    )
    parser.add_argument(
        "--query_type",
        choices=['title','narration','description'],
        default='title',
        help="What to use as query"
    )
    parser.add_argument(
        "-u",
        required=False,
        action="store_true",
        help="set flag to use custom analyzer"
    )
    parser.add_argument(
        "--vector_name",
        required=False,
        choices=['sbert','fasttext'],
        help="Choose which embedding service to use for the vector search"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        required=False
    )
    parser.add_argument(
        "-make_table",
        action="store_true",
        required=False,
        help="use to generate NDCG table for a given id"
    )

    args = parser.parse_args()
    args_dict = vars(args)
    if args_dict['u']:
        args_dict["analyzer"] = get_custom_a() # TODO: Add custom
    del args_dict['u']
    if args_dict['make_table']:
        table,header = calc_table(args.index_name,args.topic_id)
        row_format ="{!s:20}" * 4
        print(row_format.format(*header))
        for x in table:
            print(row_format.format(x,*table[x]))
    else:
        run_query(**vars(args)) #convert to dict and then use star to auto assign

if __name__ == "__main__":
    main()
