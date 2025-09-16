from docx import Docx
import xml.etree.ElementTree as ET
import logging
import re
import config
from image import ImageKeyTopic, IconKeyTopic

logger = logging.getLogger(__name__)


def process_images_docx():
    if config.docx is None:
        exit("Could not read the docx file.")
    else:
        image_list = ImageKeyTopic()
        root = config.docx.document

        last_image_id = None
        found_image = False
        empty_para = False

        for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            if found_image:
                label = _image_label(p)
                if label is not None:
                    found_image = False
                    empty_para = False
                    path = config.docx.id_to_path[last_image_id].split("/")[-1]
                    href = f"../images/{path}"
                    image_list.add_image(label, href)
                elif empty_para:
                    logger.debug("Failed to find the image label in the second paragraph.")
                    found_image = False
                    empty_para = False
                else:
                    empty_para = True
            else:
                # Ищем параграфы с рисунками
                pic = p.find(".//pic:pic", config.docx.ns)
                if pic:
                    image_id = _image_id(p, config.docx.ns)
                    if image_id is not None:
                        image_path = config.docx.id_to_path[image_id]
                        found_image = True
                        last_image_id = image_id
                    else:
                        pass  # Не найден ID изображения

        image_list.save()


def _image_id(element, ns):
    blip = element.find(".//a:blip", ns)
    try:
        return blip.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed']
    except Exception as e:
        return None


def _image_label(p):
    def label_text(para):
        labels = para.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        if len(labels) == 0:
            logger.debug("No text in the paragraph immediately after the image")
            return None
        else:
            label = "".join([l.text for l in labels if l.text])
            fig_pattern = re.compile(r"""^Рисунок[\s]*[А-Я]?[\d]*[\s]*[\–\-\-\—][\s]*""")
            correct = fig_pattern.match(label)
            if correct is None:
                logger.debug("Not a picture label pattern.")
                return None
            else:
                return fig_pattern.sub('', label).strip()

    label = label_text(p)
    # Можно добавить проверку стиля, если доступен (здесь он отсутствует)
    return label


def process_icons():
    if config.docx is None:
        exit("Could not read the docx file.")
    else:
        icon_list = IconKeyTopic()
        root = config.docx.document
        for icon in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline'):
            image_id = _image_id(icon, config.docx.ns)
            if (image_id is not None) and 'rId' in image_id:
                path = config.docx.id_to_path[image_id].split("/")[-1]
                href = f"../images/{path}"
                icon_list.add_image(image_id, href)
            else:
                # Неверный ID или не изображение
                pass

        icon_list.save()