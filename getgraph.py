#! /usr/bin/env python
# -*- coding: UTF8 -*-

#import colorsys
import community  # pip install python-louvain
import json
import networkx as nx
import re
import requests
from bs4 import BeautifulSoup
from sklearn.preprocessing import minmax_scale

min_r, max_r = 6, 20   # min/max radius of nodes
min_w, max_w = 0.5, 2  # min/max width of edges

def makegraph(data):
    # The worst place to do this. Done in <strike>d3</strike> css.
    #color = lambda c,n : "#%02x%02x%02x" % tuple(int(255*c)
    #        for c in colorsys.hsv_to_rgb(c/(n+1),1,1))
    # make a plain edge list with labels, 'values' -> weight
    nodes = {node['id']: node['label'] for node in data['nodes']}
    for edge in data['edges']:
        if edge['from'] not in nodes:
            nodes[edge['from']] = 'TAG "{}" REDACTED FOR YOUR SAFETY'.format(edge['from'])
        if edge['to'] not in nodes:
            nodes[edge['to']] = 'TAG {} REDACTED FOR YOUR SECURITY'.format(edge['to'])
    edges = [(nodes[edge['from']], nodes[edge['to']], {'weight': edge['value']})
                for edge in data['edges']]
    #G = nx.DiGraph()  # not a directed graph
    G = nx.Graph()
    G.add_edges_from(edges)
    # Find communities, pagerank, and eigenvector centrality.
    # for nodes, betweenness for edges.
    #partition = community.best_partition(nx.Graph(G))
    partition = community.best_partition(G)
    nx.set_node_attributes(G, partition, 'community') 
    pagerank = nx.pagerank_scipy(G, weight='weight')
    nx.set_node_attributes(G, pagerank, 'pagerank') 
    eic = nx.eigenvector_centrality_numpy(G)
    nx.set_node_attributes(G, eic, 'eic') 
    bb = nx.edge_betweenness_centrality(G, weight='weight', normalized=False)
    nx.set_edge_attributes(G, bb, 'betweenness') 
    # node color <- community  (do in javascript?)
    #nx.set_node_attributes(G,
    #    {k:color(v, max(partition.values())) for k,v in partition.items()},
    #    'color') 
    return nx.node_link_data(G)

def getdata(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # brittle
    jscript = soup.findAll('script')[2].get_text()
    def str2json(gp, text):
        # get the assignment we want
        s = re.sub(r'^.* var ' + gp + r' = new vis.DataSet \(\[([^\]]*),\s*\]\).*',
                    r'{' + gp + r': [\1]}', text, flags=re.DOTALL)
        # put keys in quotes
        s = re.sub(r'(\w*):', r'"\1":', s)
        return json.loads(s)
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
    # check with jq .< output
