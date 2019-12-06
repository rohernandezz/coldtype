from coldtype.pens.datpen import DATPen, DATPenSet
from coldtype.geometry import Rect, Point

from coldtype.text.shaper import segment
from coldtype.text.reader import Style, StyledString, FittableMixin


class GrafStyle():
    def __init__(self, leading=10, x="centerx", xp=0, **kwargs):
        self.leading = kwargs.get("l", leading)
        self.x = x
        self.xp = xp


class Graf():
    def __init__(self, lines, container, style=None, **kwargs):
        if isinstance(container, Rect):
            self.container = DATPen().rect(container)
        else:
            self.container = container
        if style and isinstance(style, GrafStyle):
            self.style = style
        else:
            self.style = GrafStyle(**kwargs)
        self.lines = lines
    
    def lineRects(self):
        # which came first, the height or the width???
        rects = []
        leadings = []
        box = self.container.getFrame()
        leftover = box
        for l in self.lines:
            box, leftover = leftover.divide(l.height(), "maxy")
            if self.style.leading < 0:
                # need to add pixels back to leftover
                leftover.h += abs(self.style.leading)
            else:
                leading, leftover = leftover.divide(self.style.leading, "maxy")
                leadings.append(leading)
            rects.append(box)
        return rects
    
    def width(self):
        return max([l.width() for l in self.lines])

    def fit(self):
        rects = self.lineRects()
        for idx, l in enumerate(self.lines):
            l.fit(rects[idx].w - self.style.xp)
        return self
    
    def pens(self):
        rects = self.lineRects()
        pens = DATPenSet()
        for idx, l in enumerate(self.lines):
            r = rects[idx]
            dps = l.pens().translate(r.x, r.y)
            dps.container = r
            dps.align(dps.container, x=self.style.x, y=None)
            pens.pens.append(dps)
        return pens
    
    def fpa(self, rect=None):
        return self.fit().pens().align(rect or self.container.getFrame())


class Lockup(FittableMixin):
    def __init__(self, slugs, preserveLetters=True, nestSlugs=True):
        self.slugs = slugs
        self.preserveLetters = preserveLetters
        self.nestSlugs = nestSlugs
    
    def width(self):
        return sum([s.width() for s in self.slugs])
    
    def height(self):
        return max([s.height() for s in self.slugs])
    
    def textContent(self):
        return "/".join([s.textContent() for s in self.slugs])

    def shrink(self):
        adjusted = False
        for s in self.slugs:
            adjusted = s.shrink() or adjusted
        return adjusted

    def pens(self):
        pens = []
        x_off = 0
        for s in self.slugs:
            x_off += s.margin[0]
            if self.preserveLetters:
                dps = s.pens()
                dps.translate(x_off, 0)
                if self.nestSlugs:
                    pens.append(dps)
                else:
                    pens.extend(dps.pens)
            else:
                dps = s.pen()
                dps.translate(x_off, 0)
                pens.append(dps)
            x_off += dps.getFrame().w
            x_off += s.margin[1]
            x_off += s.strings[-1].tracking
        return DATPenSet(pens)
    
    def pen(self):
        return self.pens().pen()
    
    def TextToLines(text, primary, fallback=None):
        lines = []
        for line in text.split("\n"):
            lines.append(Lockup([Slug(line, primary, fallback)]))
        return lines
    
    def SlugsToLines(slugs):
        return [Lockup([slug]) for slug in slugs]


def T2L(text, primary, fallback=None):
    return Lockup.TextToLines(text, primary, fallback)


class Slug(FittableMixin):
    def __init__(self, text, primary, fallback=None, margin=[0, 0]):
        self.text = text
        self.primary = primary
        self.fallback = fallback
        self.margin = margin
        self.strings = []
        self.tag()
    
    def tag(self):
        if self.fallback:
            segments = segment(self.text, "LATIN")
            self.strings = [StyledString(s[1], self.fallback if "LATIN" in s[0] else self.primary) for s in segments]
        else:
            self.strings = [StyledString(self.text, self.primary)]
    
    def width(self):
        return sum([s.width() for s in self.strings])
    
    def height(self):
        return max([s.style.capHeight*s.scale() for s in self.strings])
    
    def textContent(self):
        return "-".join([s.textContent() for s in self.strings])

    def shrink(self):
        adjusted = False
        for s in self.strings:
            adjusted = s.shrink() or adjusted
        return adjusted

    def pens(self, atomized=True):
        pens = DATPenSet()
        x_off = 0
        for s in self.strings:
            #x_off += s.margin[0]
            if atomized:
                dps = s.pens(frame=True)
                if dps.layered:
                    pens.layered = True
                dps.translate(x_off, 0)
                pens.pens.extend(dps.pens)
                x_off += dps.getFrame().w
            else:
                dp = s.pen(frame=True)
                dp.translate(x_off, 0)
                pens.pens.append(dp)
                x_off += dp.getFrame().w
            #x_off += dps.getFrame().w
            #x_off += s.margin[1]
        return pens
        #return DATPenSet([s.pens(frame=True) for s in self.strings])
    
    def pen(self):
        return self.pens(atomized=False).pen()