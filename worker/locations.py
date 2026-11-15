"""Localisations sourcées ; une absence de rectangle reste explicite."""
import math
import re

import fitz
import pikepdf


def rect_values(value, normalize=False):
    try:
        values = [float(x) for x in value]
        if len(values) == 4 and all(math.isfinite(x) for x in values):
            x0, y0, x1, y1 = values
            if normalize:
                x0, y0, x1, y1 = min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
            if x1 > x0 and y1 > y0:
                return [x0, y0, x1, y1]
    except (TypeError, ValueError):
        pass
    return None


def object_refs(context):
    return [(int(a), int(b)) for a, b in re.findall(r"\((\d+)\s+(\d+)\s+obj\b", context)]


def compose(outer, inner):
    a, b, c, d, e, f = outer
    g, h, i, j, k, l = inner
    return (a*g+c*h, b*g+d*h, a*i+c*j, b*i+d*j, a*k+c*l+e, b*k+d*l+f)


def image_rect(matrix):
    a, b, c, d, e, f = matrix
    points = [(e, f), (a+e, b+f), (c+e, d+f), (a+c+e, b+d+f)]
    return rect_values([min(x for x, y in points), min(y for x, y in points),
                        max(x for x, y in points), max(y for x, y in points)])


class Locator:
    def __init__(self, pdf_path):
        self.pdf = pikepdf.open(pdf_path)
        self.render = fitz.open(pdf_path)
        self.pages = {page.obj.objgen: index+1 for index, page in enumerate(self.pdf.pages)}
        self.image_cache = {}
        self.text_cache = {}

    def close(self):
        self.pdf.close()
        self.render.close()

    def page_images(self, number):
        """Images directes dans un MCID de page, sans attribuer les MCID de Form."""
        if number in self.image_cache:
            return self.image_cache[number]
        page = self.pdf.pages[number-1]
        result, stack, marks = {}, [], []
        matrix = (1, 0, 0, 1, 0, 0)
        clipped = False
        clip_rect = None
        path_rect, path_parts = None, 0
        pending_clip = False
        text_mode, text_clip = 0, False
        repeated = set()

        def record(rect=None, reason=None):
            for mcid in marks:
                if mcid is not None:
                    entry = result.setdefault(mcid, {'rects': [], 'reasons': set()})
                    if rect:
                        entry['rects'].append(rect)
                    if reason:
                        entry['reasons'].add(reason)
        try:
            resources = page.resources
            for index, instruction in enumerate(pikepdf.parse_content_stream(page)):
                if index > 100_000:
                    raise ValueError('Inventaire des opérateurs incomplet.')
                if not hasattr(instruction, 'operator'):
                    record(reason='Image intégrée non localisée.')
                    continue
                op, args = str(instruction.operator), instruction.operands
                if op == 'q':
                    stack.append((matrix, clipped, clip_rect, text_mode))
                elif op == 'Q':
                    if not stack:
                        raise ValueError('Pile graphique incohérente.')
                    matrix, clipped, clip_rect, text_mode = stack.pop()
                elif op == 'cm' and len(args) == 6:
                    matrix = compose(matrix, tuple(float(x) for x in args))
                elif op in ('BDC', 'BMC'):
                    mcid = None
                    if op == 'BDC' and len(args) == 2:
                        properties = args[1]
                        if isinstance(properties, pikepdf.Name):
                            properties = resources.get('/Properties', {}).get(properties, {})
                        if isinstance(properties, pikepdf.Dictionary):
                            mcid = properties.get('/MCID')
                    mcid = int(mcid) if isinstance(mcid, int) else None
                    if mcid is not None and mcid in result:
                        repeated.add(mcid)
                    marks.append(mcid)
                    record()
                elif op == 'EMC':
                    if not marks:
                        raise ValueError('Pile de balisage incohérente.')
                    marks.pop()
                elif op == 'Do' and args:
                    obj = resources.get('/XObject', {}).get(args[0])
                    if obj is not None and str(obj.get('/Subtype')) == '/Image':
                        rect = image_rect(matrix)
                        if clipped:
                            # Tolérance des flottants PDF, puis intersection pour ne
                            # jamais dépasser le rectangle de découpe établi.
                            epsilon = 0.0001
                            if (rect and clip_rect and clip_rect[0] <= rect[0]+epsilon and
                                clip_rect[1] <= rect[1]+epsilon and clip_rect[2] >= rect[2]-epsilon and
                                    clip_rect[3] >= rect[3]-epsilon):
                                rect = rect_values([max(rect[0], clip_rect[0]), max(rect[1], clip_rect[1]),
                                                    min(rect[2], clip_rect[2]), min(rect[3], clip_rect[3])])
                            else:
                                rect = None
                        if rect:
                            record(rect=rect)
                        else:
                            record(reason='Image avec découpe ou géométrie indéterminée : rectangle masqué.')
                    else:
                        record(reason='Formulaire graphique ou objet externe non localisé.')
                elif op in ('W', 'W*'):
                    pending_clip = True
                    if path_rect and (not clipped or clip_rect):
                        clip_rect = path_rect if not clipped else rect_values([
                            max(clip_rect[0], path_rect[0]), max(clip_rect[1], path_rect[1]),
                            min(clip_rect[2], path_rect[2]), min(clip_rect[3], path_rect[3])])
                    else:
                        clip_rect = None
                    clipped = True
                elif op == 're':
                    if pending_clip:
                        clip_rect = None
                    path_parts += 1
                    aligned = (matrix[1] == 0 and matrix[2] == 0) or (matrix[0] == 0 and matrix[3] == 0)
                    if path_parts == 1 and aligned and len(args) == 4:
                        x, y, width, height = (float(v) for v in args)
                        path_rect = image_rect(compose(matrix, (width, 0, 0, height, x, y)))
                    else:
                        path_rect = None
                elif op in ('m', 'l', 'c', 'v', 'y', 'h'):
                    if pending_clip:
                        clip_rect = None
                    path_parts += 1
                    path_rect = None
                elif op == 'INLINE IMAGE':
                    record(reason='Image intégrée au flux non localisée.')
                elif op == 'Tr' and args:
                    text_mode = int(args[0])
                elif op == 'BT':
                    text_clip = False
                elif op == 'ET' and text_clip:
                    clipped, clip_rect = True, None
                elif op in ('Tj', 'TJ', "'", '"', 'S', 's', 'f', 'F', 'f*', 'B', 'B*', 'b', 'b*', 'sh'):
                    record(reason='Texte ou tracé non localisé dans ce contenu balisé.')
                    if op in ('Tj', 'TJ', "'", '"') and text_mode >= 4:
                        text_clip = True
                if op in ('n', 'S', 's', 'f', 'F', 'f*', 'B', 'B*', 'b', 'b*'):
                    path_rect, path_parts = None, 0
                    pending_clip = False
            if marks or stack or pending_clip:
                raise ValueError('Piles de contenu non refermées.')
            for mcid in repeated:
                result[mcid] = {'rects': [], 'reasons': {'MCID répété : attribution ambiguë, zones masquées.'}}
        except (pikepdf.PdfError, ValueError, TypeError, OverflowError):
            result = {None: {'rects': [], 'reasons': {'Inventaire du contenu interrompu ou piles incohérentes ; zones masquées.'}}}
        self.image_cache[number] = result
        return result

    def structure_locations(self, obj):
        found = {}
        visited = set()
        warnings = set()
        count = 0

        def collect(node, inherited=None, depth=0):
            nonlocal count
            count += 1
            if depth > 80 or count > 10_000:
                warnings.add('Limite de parcours atteinte ; une partie de la balise reste inconnue.')
                return
            if isinstance(node, int):
                if inherited:
                    images = self.page_images(inherited)
                    entry = images.get(node, images.get(None))
                    found.setdefault(inherited, [])
                    if entry is None:
                        warnings.add('Contenu MCID absent ou non localisé.')
                    else:
                        found[inherited].extend(entry['rects'])
                        warnings.update(entry['reasons'])
                        if not entry['rects'] and not entry['reasons']:
                            warnings.add('Contenu MCID sans zone graphique établie.')
                else:
                    warnings.add('Page du contenu MCID inconnue.')
                return
            if isinstance(node, pikepdf.Array):
                for child in node:
                    collect(child, inherited, depth+1)
                return
            if not isinstance(node, pikepdf.Dictionary):
                return
            identity = node.objgen
            if identity != (0, 0):
                if identity in visited:
                    warnings.add('Référence de structure répétée ; parcours incomplet.')
                    return
                visited.add(identity)
            page = self.pages.get(getattr(node.get('/Pg'), 'objgen', None)) if '/Pg' in node else inherited
            if '/Pg' in node and page is None:
                warnings.add('Référence de page invalide ; localisation incomplète.')
            if page:
                found.setdefault(page, [])
            if node.get('/Stm') is not None or node.get('/StmOwn') is not None:
                warnings.add('Contenu dans un autre flux non localisé.')
                return
            if str(node.get('/Type')) == '/OBJR':
                warnings.add('Objet référencé par la balise non localisé.')
                return
            if str(node.get('/Type')) == '/MCR':
                collect(node.get('/MCID'), page, depth+1)
            else:
                collect(node.get('/K'), page, depth+1)

        collect(obj)
        return [dict(page=p, rects=rects, precision=('partial' if warnings else 'image') if rects else 'page',
                     reason=('Zone partielle. ' if rects else 'Page connue ; zone précise indisponible. ') +
                     ' '.join(sorted(warnings)) if warnings else
                     ('Image directe dans le contenu balisé ciblé.' if rects else
                      'Page reliée à la balise ; aucune zone graphique précise établie.'))
                for p, rects in sorted(found.items())]

    def resolve(self, context):
        page_match = re.search(r'/pages\[(\d+)\]', context)
        number = int(page_match.group(1))+1 if page_match else None
        if number is not None and not 1 <= number <= len(self.pdf.pages):
            return []
        refs = object_refs(context)
        if number and ('annots[' in context or 'Annot' in context):
            for ref in reversed(refs):
                try:
                    obj = self.pdf.get_object(ref)
                    if any(a.objgen == ref for a in self.pdf.pages[number-1].obj.get('/Annots', [])):
                        rect = rect_values(obj.get('/Rect'), normalize=True)
                        if rect:
                            return [dict(page=number, rects=[rect], precision='annotation',
                                         reason='Rectangle /Rect de l’annotation ciblée par le rapport.')]
                except (pikepdf.PdfError, AttributeError, TypeError):
                    continue
        if number and '/font[' in context:
            names = re.findall(r'/font\[\d+\]\(([^)]+)\)', context)
            if names:
                normalize = lambda s: re.sub(r'^[A-Z]{6}\+', '', s).casefold()
                page = self.render[number-1]
                resources = self.pdf.pages[number-1].resources.get('/Font', {})
                homonyms = set()
                for font in resources.values():
                    if normalize(str(font.get('/BaseFont', '')).lstrip('/')) == normalize(names[-1]):
                        homonyms.add(font.objgen)
                if len(homonyms) > 1:
                    return [dict(page=number, rects=[], precision='page',
                                 reason='Plusieurs objets police portent ce nom ; attribution ambiguë, zones masquées.')]
                if self.pdf.pages[number-1].obj.get('/UserUnit', 1) != 1:
                    return [dict(page=number, rects=[], precision='page',
                                 reason='Unité de page particulière ; coordonnées de police non établies.')]
                boxes = []
                if number not in self.text_cache:
                    self.text_cache[number] = page.get_text('dict')['blocks']
                # MuPDF renvoie le texte dans la page non tournée, relatif à la CropBox.
                # La hauteur et l’origine sont celles de cette boîte avant rotation.
                left, top = page.cropbox.x0, page.mediabox.y1 - page.cropbox.y0
                for block in self.text_cache[number]:
                    for line in block.get('lines', []):
                        for span in line['spans']:
                            if normalize(span['font']) == normalize(names[-1]):
                                x0, y0, x1, y1 = span['bbox']
                                rect = rect_values([left+x0, top-y1, left+x1, top-y0])
                                if rect:
                                    boxes.append(rect)
                if boxes:
                    return [dict(page=number, rects=boxes, precision='font',
                                 reason='Fragments de texte rendus avec le nom de police du rapport ; pas une occurrence unique.')]
        if not number:
            for ref in reversed(refs):
                try:
                    obj = self.pdf.get_object(ref)
                    if isinstance(obj, pikepdf.Dictionary) and obj.get('/S') is not None:
                        return self.structure_locations(obj)
                except (pikepdf.PdfError, AttributeError, TypeError):
                    continue
        return [dict(page=number, rects=[], precision='page',
                     reason='Page donnée par le rapport ; zone précise indisponible.')] if number else []
