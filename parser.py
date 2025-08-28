import re
import plotly.graph_objects as go

class WebPage:

    current_pageID = -1

    @classmethod
    def gen_id(cls):
        cls.current_pageID = cls.current_pageID + 1
        return cls.current_pageID
    
    @classmethod
    def add_page(cls, name, level, website, metadata):
        # breakpoint()
        page = website.get_page(name=name)
        if page == None:
            page = WebPage(name, level, website, metadata)
            website.add_page(page)
        else:
            page.add_attributes(level, metadata)
        return page


    def __init__(self, name, level, website, metadata):
        self.name = name
        self.pageID = WebPage.gen_id()
        self.website = website
        self.metadata = metadata
        self.children = []
        self.levels = [level]
        self.parents = []
        self.visits = 0
        # print(f"Page **{self.name}** created")


    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)
            child._add_parent(self)
        else:
            print(f"Child {child} already children of {self.name}")

    def add_attributes(self, level, metadata):
        # if level not in self.levels:
        #     self.levels.append(level)
        # else:
        #     print(f"Level {level} already in {self.name}")
        self.levels.append(level)
        for key,value in metadata.items():
            if key not in self.metadata:
                self.metadata[key] = value
            elif self.metadata[key] != value:
                raise Exception(f"Node {self.name} has already a metadata entry for key {key} but a different value: {self.metadata[key]} != {value}")
            else:
                raise Exception(f"Node {self.name} has already a metadata entry for key: {key}, value: {value}")


    def _add_parent(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)
        else:
            print(f"Parent {parent} already parent of {self.name}")

class Website:
    
    def __init__(self, name):
        self.name = name
        self.root = None
        self.page_list = {}
        self.page_ids = {}

    def _set_root(self, page):
        if self.root != None:
            raise Exception(f"Root {self.root.name} already exists but requested to add root {page.name}")
        else:
            self.root = page
            

    def get_page(self, page=None, name=None):
        if page == None and name == None:
            raise Exception(f"No page nor name provided to retrieve page")
        if page != None and name != None:
            raise Exception(f"Both page and name provided to retrieve page")
        
        if page != None:
            page_name = page.name
        else:
            page_name = name

        if page_name in self.page_list:
            print(f"Page {page_name} already exist in website {self.name}")
            return self.page_list[f"{page_name}"]
        
        return None


    def add_page(self, page):
        if self.get_page(page=page) == None:
            if page.levels[0] == 0:
                self._set_root(page)
            self.page_list[f"{page.name}"] = page
            self.page_ids[f"{page.pageID}"] = page
        else:
            print(f"Page {page.name} not added")


class Parser:
    # https://github.com/ikatyang/emoji-cheat-sheet
    START_COMMENT = "<!--"
    END_COMMENT = "-->"
    START_METADATA = r":id:"
    END_METADATA = r":id:"
    SEP_METADATA = ','
    SEP_METADATAITEM = ':'
    LISTSIGN = "- "
    MAX_IND = 20

    @classmethod
    def _process_name(cls, line, idx_listsign):
        # breakpoint()
        metadata = {}
        name = line[idx_listsign+len(cls.LISTSIGN):]
        my_regex = cls.START_COMMENT + r".*" +  cls.END_COMMENT
        name = re.sub(my_regex, '', name)
        my_regex = cls.START_METADATA + r"(.*)" +  cls.END_METADATA
        p = re.compile(my_regex)
        m = p.search(name)
        if m != None:
            name = re.sub(my_regex, '', name)
            records = m.group(1).split(cls.SEP_METADATA)
            for record in records:
                [key,value] = record.split(cls.SEP_METADATAITEM)
                metadata[f"{key.strip()}"] = value.strip()
            # breakpoint()

        name = name.rstrip()
        return name, metadata

        

    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        with open(self.filename, 'r') as f:
            lines = [line.rstrip() for line in f]
        
        ws = Website("Dafne")
        parents = [None for i in range(Parser.MAX_IND)]
        cur_ind_level = 0

        for i,line in enumerate(lines):
            if len(line) == 0:
                # Skip empty lines 
                continue
            if not line.strip().startswith(Parser.START_COMMENT):
                if '\t' in line:
                    raise Exception(f"Tab found at line {i}, bailing out")
                idx_listsign = line.find(Parser.LISTSIGN)
                
                if idx_listsign == -1:
                    raise Exception(f"No indentation found at line {i}, bailing out")
                
                if idx_listsign%2 != 0:
                    # breakpoint()
                    raise Exception(f"Line {i} has wrong indentation")

                ind_level = int(idx_listsign/2)
                # print(f"Indirection is {ind_level}")

                if ind_level > cur_ind_level + 1:
                    # breakpoint()
                    raise Exception(f"Line {i} has gap in indentation")

                cur_ind_level = ind_level
                
                page_name, metadata = Parser._process_name(line, idx_listsign)
                page = WebPage.add_page(page_name,ind_level,ws, metadata)
                # breakpoint()
                               
                parents[ind_level] = page

                if ind_level > 0:
                    parent = parents[ind_level-1]
                    if parent == None:
                        raise Exception(f"Page {page.name} at level {ind_level} has no parent")
                    parent.add_child(page)

        return ws


class SankeyGraph:
    # #7f7f7f from d3 color scheme Category10
    # #bcbd22 from d3 color scheme Category10
    # #17becf from d3 color scheme Category10
    # #1f77b4 from d3 color scheme Category10
    # #ff7f0e from d3 color scheme Category10
    # #2ca02c from d3 color scheme Category10
    # #d62728 from d3 color scheme Category10
    # #9467bd from d3 color scheme Category10
    # #8c564b from d3 color scheme Category10
    # #e377c2 from d3 color scheme Category10

    # green red purple
    # ['#1b9e77','#d95f02','#7570b3']
    DB_NODE_COLOR = '#b2182b'
    DB_LINK_COLOR = '#e0e0e0'
    
    MATOMO_NODE_COLOR = '#1b9e77'
    MATOMO_LINK_COLOR = '#e0e0e0'

    NODE_COLOR = '#999999'
    LINK_COLOR = '#e0e0e0'

    
    def make_values(self, page):
        '''
            Recursive. Recreate a equally distributed flow
            assuming all leaf nodes get one visit, by assigning
            values to nodes and links.
        '''
        for child in page.children:
            # print(f"Following connection from {page.name} to {child.name}")
            self.make_values(child)
            
            if child.pageID not in self.known_nodes:
                if len(child.children) == 0:
                    # This is a leaf node.
                    # print(f"Initializing visits to 1 for {child.name}")
                    child.visits = 1
            
                # Calculate contribution to each parent
                contrib = child.visits/len(child.parents)
                # Divide flow among parents
                for parent in child.parents:
                    # print(f"Bubbling {contrib} visits from {child.name} to {parent.name}")
                    parent.visits = parent.visits + contrib
                    # Define the weight of the link (a link cannot happen twice between the same nodes)
                    if f"{parent.pageID} - {child.pageID}" in self.known_links:
                        raise Exception(f"Link {parent.name} - {child.name} already encountered")
                    self.known_links[f"{parent.pageID} - {child.pageID}"] = contrib
                self.known_nodes.append(child.pageID)



    def make_links(self,page):
        '''
            Recursive. Create the links between the nodes.child
            Assign also color to nodes and links.
        '''
        # breakpoint()
        
        for child in page.children:
            # print(f"Add connection from {page.name} to {child.name}")
            self.sources.append(page.pageID)
            self.targets.append(child.pageID)
            value = self.known_links[f"{page.pageID} - {child.pageID}"]
            self.values.append(value)
                        
            if child.pageID not in self.known_nodes:
                self.make_links(child)
                self.known_nodes.append(child.pageID)
            
        return


    def make_node_labels(self, ws):
        self.labels = [None for i in range(len(ws.page_list))]
        for page_name in ws.page_list:
            page = ws.page_list[page_name]
            # print(f"{page.name} : {page.pageID}")
            self.labels[page.pageID] = page.name

    def make_node_colors(self, ws):
        self.color_nodes = [None for i in range(len(ws.page_list))]
        for page_name in ws.page_list:
            page = ws.page_list[page_name]
            if 'source' in page.metadata:
                # breakpoint()
                if page.metadata['source'] == 'db':
                    self.color_nodes[page.pageID] = SankeyGraph.DB_NODE_COLOR
                elif page.metadata['source'] == 'matomo':
                    self.color_nodes[page.pageID] = SankeyGraph.MATOMO_NODE_COLOR
                else:
                    raise Exception(f"Unknown source: {page.metadata['source']}")
            else:
                self.color_nodes[page.pageID] = SankeyGraph.NODE_COLOR

    def make_link_colors(self, ws):
        self.color_links = []
        # breakpoint()
        for i in range(len(self.sources)):
            sr = self.sources[i]
            tg = self.targets[i]

            sr_page = ws.page_ids[f"{sr}"]
            tg_page = ws.page_ids[f"{tg}"]

            if 'source' in tg_page.metadata:
                # breakpoint()
                if tg_page.metadata['source'] == 'db':
                    self.color_links.append(SankeyGraph.DB_LINK_COLOR)
                elif tg_page.metadata['source'] == 'matomo':
                    self.color_links.append(SankeyGraph.MATOMO_LINK_COLOR)
                else:
                    raise Exception(f"Unknown source: {tg_page.metadata['source']}")
            else:
                self.color_links.append(SankeyGraph.LINK_COLOR)



    def __init__(self, ws):
        
        self.values = []
        self.known_nodes = []
        self.known_links = {}
        self.make_values(ws.root)
        # breakpoint()

        
        self.sources = []
        self.targets = []
        self.known_nodes = []
    
        self.make_links(ws.root)
        self.make_node_labels(ws)
        self.make_node_colors(ws)
        self.make_link_colors(ws)

        # print(sources)
        # print(targets)
        # print(labels)
        
    def print_graph(self):
        link = dict(source = self.sources, target = self.targets, value = self.values, color=self.color_links)
        node = dict(label = self.labels, pad=15, thickness=5, color=self.color_nodes)
        
        data = go.Sankey(link = link, node=node)
        # plot
        fig = go.Figure(data)
        fig.show()

    

def main(filename, print):
    p = Parser(filename)
    # p = Parser("./test.md")
    ws = p.parse()

    # breakpoint()
    gr = SankeyGraph(ws)
    # breakpoint()
    if print:
        gr.print_graph()
    


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '-f', '--filename',
        dest='filename',
        action='store',
        required=True,
        help='specifies the name of the sitemap file',
    )
    parser.add_argument(
        '-p', '--print',
        dest='print',
        action='store_true',
        default=False,
        help='specifies whether to print the graph',
    )

    args, unknown = parser.parse_known_args()

    if len(unknown) > 0:
        print(f'Unknown options {unknown}')
        parser.print_help()
        exit(-1)

    main(args.filename, args.print)
