import re
import plotly.graph_objects as go

class WebPage:

    current_pageID = -1

    @classmethod
    def gen_id(cls):
        cls.current_pageID = cls.current_pageID + 1
        return cls.current_pageID
    
    @classmethod
    def add_page(cls, name, level, website):
        # breakpoint()
        page = website.get_page(name=name)
        if page == None:
            page = WebPage(name, WebPage.current_pageID, level, website)
            website.add_page(page)
        else:
            page.add_level(level)
        return page


    def __init__(self, name, id, level, website):
        self.name = name
        self.pageID = WebPage.gen_id()
        self.website = website
        self.children = []
        self.levels = [level]
        self.parent = None
        # print(f"Page **{self.name}** created")


    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)
            # child._add_parent(self)
        else:
            print(f"Child {child} already children of {self.name}")

    def add_level(self, level):
        # if level not in self.levels:
        #     self.levels.append(level)
        # else:
        #     print(f"Level {level} already in {self.name}")
        self.levels.append(level)


    def _add_parent(self, parent):
        if self.parent == None:
            self.parent = parent
        else:
            print(f"Parent {parent} already parent of {self.name}")

class Website:
    
    def __init__(self, name):
        self.name = name
        self.root = None
        self.page_list = {}

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
        else:
            print(f"Page {page.name} not added")


class Parser:
    
    START_COMMENT = "<!--"
    END_COMMENT = "-->"
    LISTSIGN = "- "
    MAX_IND = 20

    @classmethod
    def _clean_name(cls, line, idx_listsign):
        # breakpoint()
        name = line[idx_listsign+len(cls.LISTSIGN):]
        my_regex = cls.START_COMMENT + r".*" +  cls.END_COMMENT
        name = re.sub(my_regex, '', name)
        name = name.rstrip()
        return name

        

    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        with open(self.filename, 'r') as f:
            lines = [line.rstrip() for line in f]
        
        ws = Website("Dafne")
        parents = [None for i in range(Parser.MAX_IND)]
        cur_ind_level = 0

        for i,line in enumerate(lines):
            if not line.startswith(Parser.START_COMMENT):
                if '\t' in line:
                    raise Exception(f"Tab found at line {i}, bailing out")
                idx_listsign = line.find(Parser.LISTSIGN)
                
                if idx_listsign == -1:
                    raise Exception(f"No indentation found at line {i}, bailing out")
                
                if idx_listsign%2 != 0:
                    raise Exception(f"Line {i} has wrong indentation")

                ind_level = int(idx_listsign/2)
                # print(f"Indirection is {ind_level}")

                if ind_level > cur_ind_level + 1:
                    raise Exception(f"Line {i} has gap in indentation")

                cur_ind_level = ind_level
                
                page_name = Parser._clean_name(line, idx_listsign)
                page = WebPage.add_page(page_name,ind_level,ws)
                # breakpoint()
                               
                parents[ind_level] = page

                if ind_level > 0:
                    parent = parents[ind_level-1]
                    if parent == None:
                        raise Exception(f"Page {page.name} at level {ind_level} has no parent")
                    parent.add_child(page)

        return ws

def loop(page, sources, targets, values, color_links, color_nodes, known_nodes):
    # breakpoint()
    for child in page.children:
        # print(f"Add connection from {page.name} to {child.name}")
        sources.append(page.pageID)
        targets.append(child.pageID)
        values.append(1)
        color_links.append('#EBBAB5')
        color_nodes.append('#808B96')
        if child.pageID not in known_nodes:
            loop(child, sources, targets, values, color_links, color_nodes, known_nodes)
            known_nodes.append(child.pageID)
        
    return



def make_Sankey(ws):

    sources = []
    targets = []
    labels = []
    values = []
    color_links = []
    color_nodes = []
    known_nodes = []

    for page_name in ws.page_list:
        page = ws.page_list[page_name]
        # print(f"{page.name} : {page.pageID}")
        labels.append(page.name)

    loop(ws.root, sources, targets, values, color_links, color_nodes, known_nodes)

    # print(sources)
    # print(targets)
    # print(labels)
    
    link = dict(source = sources, target = targets, value = values, color=color_links)
    node = dict(label = labels, pad=15, thickness=5, color=color_nodes)
    
    data = go.Sankey(link = link, node=node)
    # plot
    fig = go.Figure(data)
    fig.show()

    

def main():
    p = Parser("./sitemap.md")
    # p = Parser("./test.md")
    ws = p.parse()

    # breakpoint()
    make_Sankey(ws)
    



main()