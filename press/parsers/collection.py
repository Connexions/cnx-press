from xml import sax
from press.models import CollectionMetadata, CollectionElement, ComparableElement
from .common import make_cnx_xpath, make_elm_tree, parse_common_properties


def parse_collection_metadata(model):
    """Parse the metadata from the given object.

    :param model: the object to parse
    :type model: :class:`litezip.Collection`
    :returns: a metadata object
    :rtype: :class:`press.models.CollectionMetadata`

    """
    elm_tree = make_elm_tree(model)
    xpath = make_cnx_xpath(elm_tree)

    props = parse_common_properties(elm_tree)

    print_style = xpath('//col:param[@name="print-style"]/@value')
    if not print_style or not print_style[0]:
        props['print_style'] = None
    else:
        props['print_style'] = print_style[0]

    return CollectionMetadata(**props)


class CollectionXmlHandler(sax.ContentHandler):
    def __init__(self, root):
        self.current_node = root
        self.next_node = None

    def startElementNS(self, name, qname, attrs):
        uri, localname = name
        self.next_node = ComparableElement(localname, self._attrs_hash(attrs))
        self.current_node.add_child(self.next_node)
        self.current_node = self.next_node

    def characters(self, content):
        self.current_node.insert_text(content)

    def endElementNS(self, name, qname):
        self.current_node = self.current_node.parent

    def _attrs_hash(self, attrs):
        return {name: v for (uri, name), v in attrs.items()}

def parse_collxml(input_collxml):
    """
    Given a collxml document, parses the document to a python object
    where collections and sub-collections (both branching points) contain
    subcollections and modules (leaf nodes).
    """
    tree_root = ComparableElement('collxml', {})

    parser = sax.make_parser()
    parser.setFeature(sax.handler.feature_namespaces, 1)
    parser.setContentHandler(CollectionXmlHandler(tree_root))

    parser.parse(input_collxml)

    return tree_root
