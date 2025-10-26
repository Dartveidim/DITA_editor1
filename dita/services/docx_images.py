from dita.services.docx import Docx
import xml.etree.ElementTree as ET
import logging
import re
import dita.config.config as config
from dita.models.image import ImageKeyTopic, IconKeyTopic

logger = logging.getLogger(__name__)


def process_images_docx():
    """
    Обрабатывает изображения из Word-документа (.docx) и добавляет их в список ключей (keydef).
    
    Алгоритм:
        1. Проходит по абзацам документа.
        2. Находит абзацы с изображениями (<pic:pic>).
        3. Извлекает идентификатор изображения (rId).
        4. В следующем абзаце пытается найти подпись (например, "Рисунок – ...").
        5. Добавляет изображение с подписью в ImageKeyTopic.
    """
    if config.docx is None:
        exit("Could not read the docx file.")
    else:
        image_key_topic = ImageKeyTopic()
        doc_root = config.docx.document  # корневой XML элемент документа

        last_rel_id = None      # последний найденный relId изображения
        found_image = False     # флаг: нашли ли изображение
        waiting_for_caption = False  # флаг: ждём подпись в следующем абзаце

        # Перебираем все параграфы документа
        for para in doc_root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            if found_image:
                # Если предыдущий абзац был с картинкой, то ищем подпись
                caption = _extract_image_caption(para)
                if caption is not None:
                    # Подпись найдена
                    found_image = False
                    waiting_for_caption = False
                    image_file = config.docx.id_to_path[last_rel_id].split("/")[-1]
                    href = f"../images/{image_file}"
                    image_key_topic.add_image(caption, href)
                elif waiting_for_caption:
                    # Уже был один пустой параграф → считаем, что подписи нет
                    logger.debug("Failed to find the image caption in the next paragraph.")
                    found_image = False
                    waiting_for_caption = False
                else:
                    # Первый пустой параграф после картинки
                    waiting_for_caption = True
            else:
                # Ищем абзацы с рисунками (<pic:pic>)
                pic = para.find(".//pic:pic", config.docx.ns)
                if pic:
                    rel_id = _extract_rel_id(para, config.docx.ns)
                    if rel_id is not None:
                        _ = config.docx.id_to_path[rel_id]  # проверяем, что путь есть
                        found_image = True
                        last_rel_id = rel_id
                    else:
                        pass  # Не найден rId изображения

        image_key_topic.save()


def _extract_rel_id(element, ns):
    """
    Извлекает relId (relationship Id) изображения из элемента <a:blip>.
    
    Аргументы:
        element (ET.Element): XML-элемент (обычно <p> или <inline>).
        ns (dict): словарь пространств имён.
    
    Возвращает:
        str | None: идентификатор relId (например, 'rId23') или None, если не найден.
    """
    blip = element.find(".//a:blip", ns)
    try:
        return blip.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed']
    except Exception:
        return None


def _extract_image_caption(paragraph):
    """
    Пытается извлечь подпись к изображению из абзаца Word.
    
    Логика:
    1. Извлекает все текстовые элементы <w:t> в абзаце.
    2. Объединяет их в одну строку.
    3. Проверяет соответствие шаблону "Рисунок – ..." (например, "Рисунок 1 – Название").
    4. Если шаблон найден — убирает служебную часть и возвращает чистый текст подписи.
    5. Если подпись не соответствует шаблону — возвращает None.
    
    :param paragraph: XML-элемент абзаца (<w:p>), который может содержать подпись к рисунку.
    :return: str или None — текст подписи без префикса "Рисунок …", либо None если не найдено.
    """
    def _caption_text(para):
        # Собираем все текстовые части в абзаце
        text_elements = para.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        if len(text_elements) == 0:
            logger.debug("No text in the paragraph immediately after the image")
            return None
        else:
            full_text = "".join([t.text for t in text_elements if t.text])
            # Шаблон: "Рисунок N – ..." (поддерживает разные типы тире)
            fig_pattern = re.compile(r"""^Рисунок[\s]*[А-Я]?[\d]*[\s]*[\–\-\—][\s]*""")
            correct = fig_pattern.match(full_text)
            if correct is None:
                logger.debug("Paragraph is not a valid picture caption pattern.")
                return None
            else:
                # Убираем префикс "Рисунок N – " и возвращаем только название
                return fig_pattern.sub('', full_text).strip()

    caption = _caption_text(paragraph)
    # Можно добавить проверку стиля, если доступен (здесь он отсутствует)
    return caption


def process_icons():
    """
    Обрабатывает иконки (<inline> элементы) в документе Word и добавляет их в IconKeyTopic.
    
    Алгоритм:
        1. Перебирает все <w:inline> элементы.
        2. Извлекает relId изображения.
        3. Добавляет иконку в список keydef.
    """
    if config.docx is None:
        exit("Could not read the docx file.")
    else:
        icon_key_topic = IconKeyTopic()
        doc_root = config.docx.document

        # Ищем inline-объекты (в т.ч. иконки)
        for inline in doc_root.iter('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline'):
            rel_id = _extract_rel_id(inline, config.docx.ns)
            if (rel_id is not None) and 'rId' in rel_id:
                image_file = config.docx.id_to_path[rel_id].split("/")[-1]
                href = f"../images/{image_file}"
                icon_key_topic.add_image(rel_id, href)
            else:
                # Неверный relId или не изображение
                pass

        icon_key_topic.save()