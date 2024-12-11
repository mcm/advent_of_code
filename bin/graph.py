#!/usr/bin/env python

import json
import sys
from functools import lru_cache

import networkx as nx
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration


@Configuration()
class GraphCommand(StreamingCommand):
    """ Wraps networkx graph functions in a search command """

    def cmd_init(self, G: nx.Graph, record):
        if len(self.fieldnames) == 0:
            graph_key_field = None
        elif len(self.fieldnames) == 1:
            graph_key_field = self.fieldnames[0]
        else:
            raise ValueError(f"Usage: `graph init [graph_key]`")
        
        if graph_key_field and graph_key_field in record:
            graph_key = record[graph_key_field]
        else:
            graph_key = graph_key_field or ""

        graph, graph_ref = self.load_graph_by_key(graph_key)
        if graph_ref is None:
            record["_graph_ref"] = self.save_graph(nx.DiGraph(), graph_key)
        else:
            record["_graph_ref"] = graph_ref
        return record

    def cmd_load(self, G: nx.Graph, record):
        if len(self.fieldnames) == 0:
            graph_key_field = None
        elif len(self.fieldnames) == 1:
            graph_key_field = self.fieldnames[0]
        else:
            raise ValueError(f"Usage: `graph load [graph_key]`")
        
        if graph_key_field and graph_key_field in record:
            graph_key = record[graph_key_field]
        else:
            graph_key = graph_key_field or ""

        graph_ref = self.get_graph_ref_by_key(graph_key)
        # graph, graph_ref = self.load_graph_by_key(graph_key)
        if graph_ref is not None:
            record["_graph_ref"] = graph_ref
        return record

    def cmd_copy(self, G: nx.Graph, record):
        if len(self.fieldnames) == 1:
            graph_key_field = self.fieldnames[0]
        else:
            raise ValueError(f"Usage: `graph copy graph_key`")
        
        if "_graph_ref" not in record:
            return record

        if graph_key_field and graph_key_field in record:
            graph_key = record[graph_key_field]
        else:
            graph_key = graph_key_field

        res = self._load_graph_by_key(graph_key, fields="_key")

        record.update({
            "_graph_ref": res["_key"]
        })

        return record

    def cmd_cleanup(self, G: nx.Graph, record):
        if "_graph_ref" in record:
            del record["_graph_ref"]
        return record

    def cmd_reset(self, G: nx.Graph, record):
        if "_graph_ref" in record:
            del record["_graph_ref"]
        return record

    def cmd_add_edge(self, G: nx.Graph, record):
        if len(self.fieldnames) == 1:
            u_fieldname = self.fieldnames[0]
            v_fieldname = None
        elif len(self.fieldnames) == 2:
            u_fieldname, v_fieldname = self.fieldnames
        else:
            raise ValueError(f"Usage: `graph add_edge node_pair_field` or `graph add_edge node1_field node2_field`")

        if u_fieldname and v_fieldname:
            u_of_edge = record[u_fieldname]
            v_of_edge = record[v_fieldname]
        else:
            value = record[u_fieldname]
            if not isinstance(value, list):
                value = json.loads(value)
            u_of_edge, v_of_edge = value

        G.add_nodes_from([u_of_edge, v_of_edge])
        G.add_edge(u_of_edge, v_of_edge)

        return record
    
    def cmd_add_edges(self, G: nx.Graph, record):
        if len(self.fieldnames) == 1:
            u_fieldname = self.fieldnames[0]
        else:
            raise ValueError(f"Usage: `graph add_edge node_pair_field`")

        value = record[u_fieldname]
        if not isinstance(value, list):
            value = json.loads(value)
        
        for edge in value:
            if not isinstance(edge, list):
                edge = json.loads(edge)
            u_of_edge, v_of_edge = edge

            G.add_nodes_from([u_of_edge, v_of_edge])
            G.add_edge(u_of_edge, v_of_edge)

        return record
    
    def cmd_count_edges(self, G: nx.Graph, record):
        if len(self.fieldnames) == 0:
            output_field = "count"
        elif len(self.fieldnames) == 1:
            output_field = self.fieldnames[0]
        else:
            raise ValueError(f"Usage: `graph count_edges [output_field]`")
        
        record[output_field] = len(G.edges)
        return record
    
    def cmd_count_nodes(self, G: nx.Graph, record):
        if len(self.fieldnames) == 0:
            output_field = "count"
        elif len(self.fieldnames) == 1:
            output_field = self.fieldnames[0]
        else:
            raise ValueError(f"Usage: `graph count_nodes [output_field]`")
        
        record[output_field] = len(G.nodes)
        return record
    
    def cmd_find_cycles(self, G: nx.Graph, record):
        if len(self.fieldnames) == 1:
            source_field = self.fieldnames[0]
            output_field = "cycle"
        elif len(self.fieldnames) == 2:
            source_field, output_field = self.fieldnames
        else:
            raise ValueError(f"Usage: `graph find_cycle source_field [output_field]`")
        
        if source_field in G:
            source = source_field
        elif source_field in record:
            source = record[source_field]
        else:
            record[output_field] = None
            return record

        try:
            record[output_field] = nx.find_cycle(G, source)
        except nx.NetworkXNoCycle:
            record[output_field] = None
        return record
    
    def cmd_get_edges(self, G: nx.Graph, record):
        if len(self.fieldnames) == 0:
            source_field = target_field = "-"
            output_field = "edges"
        elif len(self.fieldnames) == 1:
            source_field = target_field = "-"
            output_field = self.fieldnames[0]
        elif len(self.fieldnames) == 2:
            source_field, target_field = self.fieldnames
            output_field = "edges"
        elif len(self.fieldnames) == 3:
            source_field, target_field, output_field = self.fieldnames
        else:
            raise ValueError(f"Usage: `graph get_edges node1_field node2_field [output_field]`")
        
        if source_field == "-" or source_field in G:
            source = source_field
        elif source_field in record:
            source = record[source_field]
        else:
            record[output_field] = None
            return record

        if target_field == "-" or target_field in G:
            target = target_field
        elif target_field in record:
            target = record[target_field]
        else:
            record[output_field] = None
            return record

        edges = []
        for edge in G.edges:
            if not source in ("-", edge[0]):
                continue
            if not target in ("-", edge[1]):
                continue
            edges.append(json.dumps(edge))

        record[output_field] = edges
        return record
    
    def cmd_get_paths(self, G: nx.Graph, record):
        if len(self.fieldnames) == 1:
            pair_field = self.fieldnames[0]
            source_field = target_field = None
            output_field = "path"
        elif len(self.fieldnames) == 2:
            pair_field = None
            source_field, target_field = self.fieldnames
            output_field = "path"
        elif len(self.fieldnames) == 3:
            pair_field = None
            source_field, target_field, output_field = self.fieldnames
        else:
            raise ValueError(f"Usage: `graph get_paths [pairs_field]` or `graph get_paths source_field_or_node target_field_or_node [output_field]")
        
        if pair_field:
            if pair_field not in record:
                record[output_field] = None
                return record
            if isinstance(record[pair_field], list):
                pairs = record[pair_field]
            else:
                pairs = [record[pair_field]]
        else:
            if source_field in G:
                source = source_field
            elif source_field in record:
                source = record[source_field]
            else:
                record[output_field] = None
                return record

            if target_field in G:
                target = target_field
            elif target_field in record:
                target = record[target_field]
            else:
                record[output_field] = None
                return record
            
            pairs = [[source, target]]

        record[output_field] = []
        for pair in pairs:
            if isinstance(pair, list):
                source, target = pair
            else:
                source, target = json.loads(pair)

            try:
                paths = [";".join(p) for p in nx.all_shortest_paths(G, source, target)]
            except nx.NetworkXNoPath:
                continue

            record[output_field].extend(paths)
        return record

    def cmd_get_shortest_path(self, G: nx.Graph, record):
        if len(self.fieldnames) == 2:
            source_field, target_field = self.fieldnames
            output_field = "path"
        elif len(self.fieldnames) == 3:
            source_field, target_field, output_field = self.fieldnames
        else:
            raise ValueError(f"Usage: `graph get_shortest_path source_field_or_node target_field_or_node [output_field]`")

        if source_field in G:
            source = source_field
        elif source_field in record:
            source = record[source_field]
        else:
            record[output_field] = None
            return record

        if target_field in G:
            target = target_field
        elif target_field in record:
            target = record[target_field]
        else:
            record[output_field] = None
            return record

        record[output_field] = nx.shortest_path(G, source, target)
        return record
    
    def cmd_remove_edge(self, G: nx.DiGraph, record):
        if len(self.fieldnames) == 1:
            u_fieldname = self.fieldnames[0]
            v_fieldname = None
        elif len(self.fieldnames) == 2:
            u_fieldname, v_fieldname = self.fieldnames
        else:
            raise ValueError(f"Usage: `graph remove_edge node_pair_field` or `graph add_edge node1_field node2_field")

        if u_fieldname and v_fieldname:
            u_of_edge = record[u_fieldname]
            v_of_edge = record[v_fieldname]
        else:
            value = record[u_fieldname]
            if not isinstance(value, list):
                value = json.loads(value)
            u_of_edge, v_of_edge = value

        G.remove_edge(u_of_edge, v_of_edge)

        return record
    
    def _decode_graph(self, graph):
        clsname = graph.get("class", "DiGraph")
        if not hasattr(nx, clsname):
            raise ValueError(clsname)
        cls = getattr(nx, clsname)
        if not issubclass(cls, nx.Graph):
            raise ValueError(clsname)

        G = cls()
        G.add_nodes_from(graph["nodes"])
        G.add_edges_from(graph["edges"])
        return G
    
    def _encode_graph(self, G: nx.Graph):
        return {
            "class": G.__class__.__name__,
            "nodes": list(G.nodes),
            "edges": list(G.edges),
        }
    
    @lru_cache()
    def get_graph_ref_by_key(self, graph_key):
        _, graph_ref = self.load_graph_by_key(graph_key)
        return graph_ref

    # @lru_cache()
    def _load_graph_by_key(self, graph_key, fields=None):
        kw = {
            "query": {
                "$and": [
                    {"sid": self.metadata.searchinfo.sid},
                    {"graph_key": graph_key}
                ]
            }
        }
        if fields:
            kw["fields"] = fields
        res = self.service.kvstore["advent_of_code_graph_storage"].data.query(**kw)
        if not res:
            raise KeyError(graph_key)
        return res[0]

    def load_graph_by_key(self, graph_key):
        try:
            res = self._load_graph_by_key(graph_key)
        except KeyError:
            return None, None
        return self._decode_graph(res["graph"]), res["_key"]
    
    # @lru_cache()
    def _load_graph_by_ref(self, graph_ref):
        return self.service.kvstore["advent_of_code_graph_storage"].data.query_by_id(graph_ref)

    def load_graph_by_ref(self, graph_ref):
        res = self._load_graph_by_ref(graph_ref)
        return self._decode_graph(res["graph"])
        
    def save_graph(self, G, graph_key):
        res = self.service.kvstore["advent_of_code_graph_storage"].data.insert(json.dumps({
            "sid": self.metadata.searchinfo.sid,
            "graph_key": graph_key,
            "graph": self._encode_graph(G)
        }))
        return res["_key"]
    
    def update_graph(self, G, graph_ref):
        data = self._load_graph_by_ref(graph_ref)
        data.update({
            "graph": self._encode_graph(G)
        })

        return self.service.kvstore["advent_of_code_graph_storage"].data.update(graph_ref, data)
    
    def preop_copy(self, records):
        if len(self.fieldnames) == 1:
            graph_key_field = self.fieldnames[0]
        else:
            raise ValueError(f"Usage: `graph copy graph_key`")
        
        ret = []
        batch = []
        for record in records:
            if "_graph_ref" not in record:
                ret.append(record)
                continue

            if graph_key_field and graph_key_field in record:
                graph_key = record[graph_key_field]
            else:
                graph_key = graph_key_field

            data = self._load_graph_by_ref(record["_graph_ref"]).copy()
            if "_key" in data:
                del data["_key"]
            data.update({"graph_key": graph_key})

            record.update({"_graph_ref": None})
            
            batch.append(data)
            ret.append(record)

        self.service.kvstore["advent_of_code_graph_storage"].data.batch_save(*batch)

        return ret

    def preop_cleanup(self, records):
        self.service.kvstore["advent_of_code_graph_storage"].data.delete(query=json.dumps({
            "sid": self.metadata.searchinfo.sid
        }))
        return records

    def preop_reset(self, records):
        self.service.kvstore["advent_of_code_graph_storage"].data.delete()
        return records

    def stream(self, records):
        cmd, self.fieldnames = self.fieldnames[0], self.fieldnames[1:]

        f = getattr(self, f"cmd_{cmd}", None)
        if not callable(f):
            raise ValueError(f"{cmd} is not a valid graph subcommand")
        
        preop = getattr(self, f"preop_{cmd}", None)
        if callable(preop):
            records = preop(records)
        
        for record in records:
            if "_graph_ref" in record and record["_graph_ref"] is not None:
                G = self.load_graph_by_ref(record["_graph_ref"])
            else:
                G = None

            yield f(G, record)

            if G is not None:
                self.update_graph(G, record["_graph_ref"])


dispatch(GraphCommand, sys.argv, sys.stdin, sys.stdout, __name__)
