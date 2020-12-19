import os

from pylint.pyreverse.utils import is_interface
from pylint.pyreverse.writer import DiagramWriter

EMPTY = "\n"
STARTUML = "@startuml\n"
ENDUML = "@enduml\n"
TITLE = "title {title}\n"
STYLECLASS = """
skinparam class {
    BackgroundColor White
    ArrowColor Grey
    BorderColor Black
}
"""
STYLEPACKAGE = """
skinparam package {
    BackgroundColor White
    ArrowColor Grey
    BorderColor Black
}
skinparam packageStyle frame
"""
OPEN = "{\n"
CLOSE = "}\n"
CLASS = "class {name} \n"
CLASSOPEN = "class {name} {{\n"
INTERFACE = "interface {name} \n"
INTERFACEOPEN = "interface {name} {{\n"
PACKAGE = "package {name} {{\n}}\n"
DEPENDS = "{parent} +-- {child}\n"
EXTENSION = "{parent} <|-- {child}\n"
COMPOSITION = "{parent} *-- {child}\n"
AGGREGATION = "{parent} o-- {child}\n"
CLASSMETHOD = "    {name}({args})\n"
CLASSATTR = "    {name}\n"

invokeplantuml = 'java -jar "{jar}" "{input}" -o "{output}"'
classes = "{package}_classes.txt"
packages = "{package}_packages.txt"

relationship2plantuml = {
    "specialization" : EXTENSION,
    "association" : AGGREGATION,
    "implements" : COMPOSITION
}
attr2type = {
    "public" : "+",
    "protected" : "#",
    "private" : "-"
}


def getAttrBase(attr):
    """E.g. 'Filesystem : str' -> 'Filesystem' """
    return attr.split(":")[0].strip()


def getFieldTypePrefix(attr):
    """Magic fields are public."""
    if attr.startswith("__") and not attr.endswith("__"):
        return attr2type["private"]
    if attr.startswith("_") and not attr.endswith("__"):
        return attr2type["protected"]
    return attr2type["public"]


def getAttrDesc(attr):
    base = getAttrBase(attr)
    desc = getFieldTypePrefix(attr) + base
    return desc


def writePackageDiagram(diagram):
    stream = STARTUML
    stream += STYLEPACKAGE
    stream += TITLE.format(title=diagram.title)

    for module in diagram.modules():
        stream += PACKAGE.format(name=module.title)

    for relation_type, relationsships in diagram.relationships.items():
        for rel in relationsships:
            stream += DEPENDS.format(
                parent=rel.to_object.title, child=rel.from_object.title
            )
    stream += "\n" + ENDUML

    packagesFile = packages.format(package=diagram.title)
    with open(packagesFile, "w") as f:
        f.write(stream)
    return packagesFile


def writeClassDiagram(diagram):
    stream = STARTUML
    stream += STYLECLASS
    # stream += TITLE.format(title=diagram.title)

    for obj in diagram.objects:
        attributes = diagram.get_attrs(obj.node)
        methods = diagram.get_methods(obj.node)

        if attributes or methods:
            template = INTERFACEOPEN if is_interface(obj.node) else CLASSOPEN
            stream += template.format(name=obj.title)

            for attr in sorted(attributes):
                attrDesc = getAttrDesc(attr)
                stream += CLASSATTR.format(name=attrDesc)

            for method in sorted(methods, key=lambda m: m.name):
                methodDesc = getAttrDesc(method.name)
                stream += CLASSMETHOD.format(
                    name=methodDesc, args=method.args.format_args()
                )

            stream += CLOSE
        else:
            template = INTERFACE if is_interface(obj.node) else CLASS
            stream += template.format(name=obj.title)

    stream += EMPTY

    for relation_type, relationsships in diagram.relationships.items():
        for rel in relationsships:
            stream += relationship2plantuml[rel.type].format(
                parent=rel.to_object.title, child=rel.from_object.title
            )

    stream += "\n" + ENDUML

    classesFile = classes.format(package=diagram.title)
    with open(classesFile, "w") as f:
        f.write(stream)
    return classesFile


def getLocalPlantUmlPath():
    """Returns the full path to plantuml.jar,
    if found on PATH, or None."""
    plantuml = "plantuml.jar"
    searchPaths = os.environ["PATH"].split(os.pathsep)
    for searchPath in searchPaths:
        plantumlPath = os.path.join(searchPath, plantuml)
        if os.path.isfile(plantumlPath):
            return os.path.abspath(plantumlPath)
    return None


def displayLocalImage(uml, jar):
    png = os.path.splitext(uml)[0] + ".png"
    cmd = invokeplantuml.format(jar=jar, input=uml, output=os.getcwd())
    os.system(cmd)
    os.system(png)
    return png


def toPlantUml(diadefs, plantumlArgs):
    umls = []
    try:
        packageDiagram, classDiagram = diadefs
        umls.append(writePackageDiagram(packageDiagram))
    except ValueError:
        classDiagram = diadefs[0]
    umls.append(writeClassDiagram(classDiagram))
    return umls


def visualizeLocally(umls):
    jar = getLocalPlantUmlPath()
    if not jar:
        print("Could not find a plantuml.jar on PATH.")
        return []

    images = []
    for uml in umls:
        images.append(
            displayLocalImage(uml, jar)
        )
    return images

class PlantUmlWriter(DiagramWriter):
    def __init__(self, config):
        print(config)
        # styles = [
        #     dict(arrowstyle="solid", backarrowstyle="none", backarrowsize=0),
        #     dict(arrowstyle="solid", backarrowstyle="none", backarrowsize=10),
        #     dict(
        #         arrowstyle="solid",
        #         backarrowstyle="none",
        #         linestyle="dotted",
        #         backarrowsize=10,
        #     ),
        #     dict(arrowstyle="solid", backarrowstyle="none", textcolor="green"),
        # ]
        styles = [
            dict(edge_type="+--"),
            dict(edge_type="<|--"),
            dict(edge_type="*--"),
            dict(edge_type="o--")
        ]
        DiagramWriter.__init__(self, config, styles)

    def set_printer(self, file_name, basename):
        """initialize VCGWriter for a UML graph"""
        print("filename %s" % file_name)
        self.graph_file = open(file_name, "w+")
        self.printer = PlantUmlPrinter(self.graph_file)
        self.printer.open_graph()
        self.printer.emit_node = self.printer.node
        self.printer.emit_edge = self.printer.edge

    def close_graph(self):
        """print the dot graph into <file_name>"""
        self.printer.close_graph()
        self.graph_file.close()
    def get_title(self, obj):
        """get project title"""
        return obj.title

    def get_values(self, obj):
        # label = "\nclass %s {\n" % obj.title
        # if not self.config.only_classnames:
        #     attrs = obj.attrs
        #     methods = [func.name for func in obj.methods]
        #     # box width for UML like diagram
        #     for attr in attrs:
        #         print(attr)
        #         label = "%s\n\t%s" % (label, attr)
            
        #     for func in methods:
        #         label = "%s\n\t%s()" % (label, func)
        #     label = "%s\n}" % (label)
        # print(label)
        stream = ""
        attributes = obj.attrs
        methods = [func for func in obj.methods]

        if attributes or methods:
            template = INTERFACEOPEN if is_interface(obj.node) else CLASSOPEN
            stream += template.format(name=os.path.basename(obj.title))

            for attr in sorted(attributes):
                attrDesc = getAttrDesc(attr)
                stream += CLASSATTR.format(name=attrDesc)

            for method in methods:
                methodDesc = getAttrDesc(method.name)
                if method.args.args:
                    args = [arg.name for arg in method.args.args if arg.name != "self"]
                else:
                    args = []
                stream += CLASSMETHOD.format(
                    name=methodDesc, args=", ".join(args)
                )

            stream += CLOSE
        else:
            template = INTERFACE if is_interface(obj.node) else CLASS
            stream += template.format(name=os.path.basename(obj.title))
        print("#"*80)
        print(stream)
        return dict(label=stream,name=os.path.basename(obj.title) , shape="")

class PlantUmlPrinter:
    def __init__(self, output_stream):
        self._stream = output_stream
        self._indent = ""
        self.obj_map = {}
     
    def open_graph(self, **args):
        self._stream.write("%s\n" % STARTUML)
        self._inc_indent()

    def close_graph(self):
        """close a vcg graph
        """
        self._dec_indent()
        self._stream.write("%s\n" % ENDUML)
        

    def _inc_indent(self):
        """increment indentation
        """
        self._indent = "  %s" % self._indent
    
    def _dec_indent(self):
        """decrement indentation
        """
        self._indent = self._indent[:-2]

    def node(self, idx, **args):
        """draw a node
        """
        #self._stream.write('class %s {' % (title))
        self._stream.write('%s' % (args['label']))
        print(args)
        if 'name' in args.keys():
            self.obj_map[idx] = args['name']
        else:
            self.obj_map[idx] = args['label']
        print("node attributes{}".format(args))
        #self._write_attributes(NODE_ATTRS, **args)
        
    
    def edge(self, from_node, to_node, **args):
        """draw an edge from a node to another.
        """
        self._stream.write(
             '%s %s %s' % (self.obj_map[to_node], args["edge_type"],  self.obj_map[from_node])
         )
        
        print('%s' % ( args))
        print('%s %s %s' % (self.obj_map[to_node], args["edge_type"],  self.obj_map[from_node]))
        if "label" in args.keys():
          self._stream.write(
             ' : %s' % ( args["label"], )
         )  
        #print("edge attrs %s" % EDGE_ATTRS)
        #self._write_attributes(EDGE_ATTRS, **args)
        self._stream.write("\n")