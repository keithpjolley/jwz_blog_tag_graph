#! /usr/bin/env python
# -*- coding: UTF8 -*-

import community  # pip install python-louvain
import json
import networkx as nx
import re
import requests
from bs4 import BeautifulSoup
from sklearn.preprocessing import minmax_scale
from scipy.stats import rankdata

def makegraph(data):
    ''' Given node/edge data run some maths to create and return
        a graph with some stats embedded. Graph is d3 ready.
    '''
    # Make a plain edge list with labels, 'values' -> weight
    nodes = {node['id']: node['label'] for node in data['nodes']}
    # This was for when jwz took out nodes but not the corresponding edges
    for edge in data['edges']:
        if edge['from'] not in nodes:
            nodes[edge['from']] = 'TAG "{}" REDACTED'.format(edge['from'])
        if edge['to'] not in nodes:
            nodes[edge['to']] = 'TAG {} REDACTED'.format(edge['to'])
    edges = [(nodes[edge['from']], nodes[edge['to']], {'weight': edge['value']})
                for edge in data['edges']]
    G = nx.Graph()
    G.add_edges_from(edges)
    # Find communities, pagerank, and eigenvector centrality.
    # for nodes, betweenness for edges.
    partition = community.best_partition(G)
    nx.set_node_attributes(G, partition, 'community') 
    pr = nx.pagerank_scipy(G, weight='weight')
    nx.set_node_attributes(G, pr, 'pagerank')
    def rankit(d):
        '''
        Given dict with numerical values returns a dict with same keys
        but with an ordinal ranking (lowest to highest).
        Extra nonsense to get low to high rank and to get the rank as
        an int instead of a numpy.int64 because json.dump barfs instead
        of dumps when it gets an int64
        '''
        return dict(zip(d.keys(),
            [int(j) for j in rankdata([-i for i in d.values()], method='max')]
          ))
    nx.set_node_attributes(G, rankit(pr), 'pagerank_rank')
    eic = nx.eigenvector_centrality_numpy(G)
    nx.set_node_attributes(G, eic, 'eic') 
    nx.set_node_attributes(G, rankit(eic), 'eic_rank')
    bb = nx.edge_betweenness_centrality(G, weight='weight', normalized=False)
    nx.set_edge_attributes(G, bb, 'betweenness') 
    nx.set_edge_attributes(G, rankit(bb), 'betweenness_rank')
    # Don't look at this.
    nx.set_edge_attributes(G,
        rankit({(s,t):list(w.values())[0] for s,t,w in edges}), 'weight_rank')
    return nx.node_link_data(G)

def getdata(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # brittle
    jscript = soup.findAll('script')[2].get_text()
    def str2json(gp, text):
        # Get the assignment we want
        # jwz is actively updating the source site. :/
        #s = re.sub(r'^.* var ' + gp + r' = new vis.DataSet \(\[([^\]]*),\s*\]\).*',
        #            r'{' + gp + r': [\1]}', text, flags=re.DOTALL)
        # Not my best regex. Should do look aheads to make sure there's not any
        # embedded matches in the data.  v2.
        s = re.sub(r'^.*\s+var\s+' + gp + '\s=\s(\[\s*{[^\]]*},?\s*\]).*',
                        r'\1', text, flags=re.DOTALL)
        # put keys in quotes
        s = re.sub(r'(\w*):', r'"\1":', s)
        # delete that last ','
        s = re.sub(r'},\s*]$', r'}]', s, flags=re.DOTALL)
        return json.loads('{"' + gp + '":' + s + '}')
    data = str2json('nodes', jscript)
    data.update(str2json('edges', jscript))
    return data

def writegraph(graph, output):
    with open(output, 'w') as f:
        f.write(json.dumps(graph))

if __name__ == "__main__":
    input = 'https://www.jwz.org/blog/tag/graph/'
    output = 'graph.json'
    data = getdata(input)
    graph = makegraph(data)
    writegraph(graph, output)
    # check with jq . output
