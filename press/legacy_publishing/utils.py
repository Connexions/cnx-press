from litezip.main import COLLECTION_NSMAP
from lxml import etree


__all__ = (
    'replace_id_and_version',
)


def replace_id_and_version(model, id, version):
    """Does an inplace replacement of the given model's id and version

    :param model: module
    :type model: :class:`litezip.Collection` or :class:`litezip.Module`
    :param id: id
    :type id: str
    :param version: version
    :type version: str

    """
    # Rewrite the content with the id and version
    with model.file.open('rb') as fb:
        xml = etree.parse(fb)
    elm = xml.xpath('//md:content-id', namespaces=COLLECTION_NSMAP)[0]
    elm.text = id
    elm = xml.xpath('//md:version', namespaces=COLLECTION_NSMAP)[0]
    elm.text = version
    with model.file.open('wb') as fb:
        fb.write(etree.tostring(xml))