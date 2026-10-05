import json
import os
from datetime import datetime

from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.effectwidget import EffectWidget, HorizontalBlurEffect, VerticalBlurEffect
from kivy.effects.scroll import ScrollEffect
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform

def C(h, a=1):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [a]

BG, CARD, INNER, PANEL = C('0F0F11'), C('1A1A1E'), C('26262B'), C('121214')
PRIMARY, ACCENT, BORDER, TRANSP = C('A0123A'), C('FF3B5C'), C('2E2E34'), [0, 0, 0, 0]
WHITE, MUTED = C('FFFFFF'), C('9A9AA3')
GREEN, AMBER, RED, PURPLE, BLUE = C('10B981'), C('F59E0B'), C('EF4444'), C('A855F7'), C('3B82F6')
LIGHT_RED = C('FF6B6B')
TAG = {'ÓLEO': AMBER, 'REVISÃO': PURPLE, 'PNEU': BLUE, 'FREIO': GREEN}

FONT_REGULAR = 'fonts/Archivo.ttf'
FONT_BOLD = 'fonts/ArchivoBlack.ttf'

MENU = [
    ('inicio', 'Início'), 
    ('veiculos', 'Veículos'), 
    ('manutencao', 'Manutenção'),
    ('historico', 'Histórico'), 
    ('config', 'Configurações')
]

if platform != 'android':
    Window.size = (390, 844)
Window.clearcolor = BG

DEFAULT = {
    'active': 0, 'notif': True,
    'vehicles': [{'tipo': 'MOTO', 'nome': 'FAN 160 2023', 'placa': 'SHP-1234', 'km': 12400, 'oleo': '10W30', 'pneu': '30 F / 32 T'}],
    'maint': [],
    'hist': [],
    'alerts': [],
}

def km(n):
    return f"{int(n):,}".replace(',', '.') + ' km'

class Store:
    path = None
    data = {}

    @classmethod
    def load(cls, folder):
        cls.path = os.path.join(folder, 'techno.json')
        try:
            with open(cls.path, encoding='utf-8') as f:
                cls.data = json.load(f)
            
            cls.data['maint'] = [m for m in cls.data.get('maint', []) if m.get('placa') and m.get('placa') != 'Desconhecido']
            cls.data['hist'] = [h for h in cls.data.get('hist', []) if len(h) > 4 and h[4] != 'Desconhecido']
        except Exception:
            cls.reset()

    @classmethod
    def reset(cls):
        cls.data = json.loads(json.dumps(DEFAULT))

    @classmethod
    def save(cls):
        try:
            with open(cls.path, 'w', encoding='utf-8') as f:
                json.dump(cls.data, f, ensure_ascii=False)
        except Exception:
            pass

    @classmethod
    def vehicle(cls):
        v = cls.data.get('vehicles', [])
        return v[min(cls.data.get('active', 0), len(v) - 1)] if v else None


# ---------------------------------------------------------------- widgets
class Box(BoxLayout):
    def __init__(self, bg=TRANSP, radius=14, border=None, **kw):
        super().__init__(**kw)
        self._r, self._b = dp(radius), border
        with self.canvas.before:
            self._color = Color(*bg)
            self._rect = RoundedRectangle(radius=[self._r])
            if border:
                Color(*border)
                self._line = Line(width=1)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._rect.pos, self._rect.size = self.pos, self.size
        if self._b:
            self._line.rounded_rectangle = (*self.pos, *self.size, self._r)

    def add_widget(self, w, *a, **k):
        if self.orientation == 'horizontal' and w.size_hint_y is None and not w.pos_hint:
            w.pos_hint = {'center_y': .5}
        super().add_widget(w, *a, **k)

class Col(Box):
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        kw.setdefault('size_hint_y', None)
        super().__init__(**kw)
        self.bind(minimum_height=self.setter('height'))

class Row(Box):
    def __init__(self, h=30, **kw):
        kw.setdefault('size_hint_y', None)
        super().__init__(height=dp(h), **kw)

class Tap(Col):
    def __init__(self, cb=None, **kw):
        super().__init__(**kw)
        self.cb = cb

    def on_touch_down(self, t):
        if super().on_touch_down(t):
            return True
        if self.collide_point(*t.pos):
            t.grab(self)
            return True

    def on_touch_up(self, t):
        if t.grab_current is self:
            t.ungrab(self)
            if self.collide_point(*t.pos) and self.cb:
                self.cb()
            return True
        return super().on_touch_up(t)

def L(text, size=13, color=WHITE, bold=False, align='left', **kw):
    f_name = FONT_BOLD if bold else FONT_REGULAR
    lb = Label(text=text, font_size=sp(size), color=color, bold=False, halign=align,
               valign='middle', size_hint_y=None, font_name=f_name, **kw)
    lb.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
    lb.bind(texture_size=lambda i, s: setattr(i, 'height', s[1] + dp(2)))
    return lb

class Btn(Button):
    def __init__(self, bg=PRIMARY, radius=18, circle=False, **kw):
        kw.setdefault('font_size', sp(13))
        super().__init__(background_normal='', background_down='', background_disabled_normal='',
                         background_color=TRANSP, bold=False, font_name=FONT_BOLD, **kw)
        self.base_bg = bg
        with self.canvas.before:
            self._color = Color(*bg)
            self._rect = Ellipse() if circle else RoundedRectangle(radius=[dp(radius)])
        self.bind(pos=self._u, size=self._u, state=self._on_state)

    def _u(self, *_):
        self._rect.pos, self._rect.size = self.pos, self.size

    def _on_state(self, *_):
        if self.state == 'down':
            c = [x * 0.8 for x in self.base_bg[:3]] + [self.base_bg[3]] if len(self.base_bg) == 4 else self.base_bg
            Animation(rgba=c, d=0.1).start(self._color)
        else:
            Animation(rgba=self.base_bg, d=0.15).start(self._color)

class Burger(Btn):
    def __init__(self, **kw):
        super().__init__(bg=CARD, radius=10, size_hint=(None, None), size=(dp(44), dp(44)), **kw)
        with self.canvas.after:
            Color(*WHITE)
            self._ls = [Line(width=1.3) for _ in range(3)]
        self.bind(pos=self._d, size=self._d)

    def _d(self, *_):
        cx, cy = self.center
        for i, ln in enumerate(self._ls):
            y = cy + (1 - i) * dp(5)
            ln.points = [cx - dp(9), y, cx + dp(9), y]

class Bell(Btn):
    def __init__(self, **kw):
        super().__init__(bg=CARD, radius=10, size_hint=(None, None), size=(dp(44), dp(44)), **kw)
        with self.canvas.after:
            Color(*WHITE)
            self._a = Line(width=1.3)
            self._b = Line(width=1.3)
        self.bind(pos=self._d, size=self._d)

    def _d(self, *_):
        cx, cy = self.center
        r = dp(7)
        self._a.ellipse = (cx - r, cy - dp(2), 2 * r, 2 * r, 270, 450)
        self._b.points = [cx - r, cy - dp(2), cx - r - dp(2), cy - dp(7), cx + r + dp(2), cy - dp(7), cx + r, cy - dp(2)]

class Bar(Widget):
    def __init__(self, frac, color, **kw):
        super().__init__(size_hint_y=None, height=dp(7), **kw)
        self.frac = max(0, min(1, frac))
        with self.canvas:
            Color(*INNER)
            self._t = RoundedRectangle(radius=[dp(4)])
            Color(*color)
            self._f = RoundedRectangle(radius=[dp(4)])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *_):
        self._t.pos, self._t.size = self.pos, self.size
        self._f.pos = self.pos
        self._f.size = (max(self.width * self.frac, dp(8)), self.height)

class Ring(Widget):
    def __init__(self, **kw):
        super().__init__(size_hint=(None, None), size=(dp(52), dp(52)), **kw)
        with self.canvas:
            Color(*INNER)
            self._f = Ellipse()
            Color(*ACCENT)
            self._l = Line(width=1.5)
        self.bind(pos=self._u, size=self._u)

    def _u(self, *_):
        self._f.pos, self._f.size = self.pos, self.size
        self._l.ellipse = (*self.pos, *self.size)

class Item(Tap):
    def __init__(self, label, active, cb=None, **kw):
        super().__init__(cb=cb, bg=PRIMARY if active else TRANSP, radius=12,
                         orientation='horizontal', size_hint_y=None, height=dp(70),
                         padding=[dp(24), 0, dp(16), 0], spacing=dp(14), **kw)
        
        self.add_widget(L(label, 18, color=WHITE if active else MUTED, bold=active))
        
        if active:
            self.add_widget(Box(bg=ACCENT, radius=2, size_hint=(None, None), size=(dp(4), dp(22)), pos_hint={'center_y': .5}))
        else:
            self.add_widget(Widget(size_hint_x=None, width=dp(4)))

class TI(Box):
    def __init__(self, **kw):
        text = kw.pop('text', '')
        hint_text = kw.pop('hint_text', '')
        input_filter = kw.pop('input_filter', None)
        
        super().__init__(bg=INNER, radius=12, padding=[dp(14), 0], size_hint_y=None, height=dp(44))
        
        self.ti = TextInput(
            text=str(text) if text else '',
            hint_text=hint_text,
            input_filter=input_filter,
            background_normal='',
            background_active='',
            background_color=[0, 0, 0, 0],
            foreground_color=WHITE,
            hint_text_color=MUTED,
            cursor_color=ACCENT,
            font_size=sp(13),
            font_name=FONT_REGULAR,
            multiline=False,
            size_hint_y=None,
            height=dp(30),
            padding=[0, dp(6), 0, 0],
            pos_hint={'center_y': .5}
        )
        self.ti.bind(focus=self._anim)
        self.add_widget(self.ti)

    @property
    def text(self):
        return self.ti.text

    @text.setter
    def text(self, value):
        self.ti.text = str(value)
        
    def _anim(self, *_):
        if self.ti.focus:
            Animation(rgba=[x * 1.5 for x in INNER[:3]] + [1], d=0.15).start(self._color)
            if self.ti.text:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.ti.select_all(), 0.1)
        else:
            Animation(rgba=INNER, d=0.15).start(self._color)

def chip(t, bg=PRIMARY):
    return Btn(text=t, bg=bg, radius=6, size_hint=(None, None), size=(dp(max(40, 16 + 6.4 * len(t))), dp(22)),
               font_size=sp(10))

def tag(t, color):
    b = Box(bg=TRANSP, border=color, radius=6, size_hint=(None, None),
            size=(dp(max(44, 14 + 6.4 * len(t))), dp(22)))
    b.add_widget(L(t, 10, color, True, 'center'))
    return b

def popup(title, content, h):
    m = ModalView(size_hint=(.9, None), background='', background_color=[0, 0, 0, 0])
    
    box = Box(bg=CARD, radius=20, orientation='vertical', padding=dp(18), spacing=dp(12))
    
    title_lbl = L(title, size=16, bold=True, color=WHITE)
    box.add_widget(title_lbl)
    
    sep = Box(bg=ACCENT, size_hint_y=None, height=dp(2))
    box.add_widget(sep)
    
    box.add_widget(content)
    
    def update_height(*_):
        overhead = dp(18)*2 + dp(12)*2 + title_lbl.height + sep.height
        
        if isinstance(content, ScrollView):
            child = content.children[0] if content.children else None
            ch_h = child.minimum_height if child and hasattr(child, 'minimum_height') else 0
            m.height = min(dp(h), overhead + ch_h)
        else:
            ch_h = content.minimum_height if hasattr(content, 'minimum_height') else content.height
            m.height = overhead + ch_h
            
    title_lbl.bind(height=update_height)
    if isinstance(content, ScrollView) and content.children and hasattr(content.children[0], 'minimum_height'):
        content.children[0].bind(minimum_height=update_height)
    elif hasattr(content, 'minimum_height'):
        content.bind(minimum_height=update_height)
        
    update_height()
    
    m.add_widget(box)
    
    m.opacity = 0
    def on_open(*_):
        app = App.get_running_app()
        if app and hasattr(app, 'root') and app.root:
            app.root.blur_bg(True)
        Animation(opacity=1, d=0.25, t='out_quad').start(m)
        
    def on_dismiss(*_):
        app = App.get_running_app()
        if app and hasattr(app, 'root') and app.root:
            app.root.blur_bg(False)
            
    m.bind(on_open=on_open, on_dismiss=on_dismiss)
    m.open()
    return m

def stack(*labels):
    c = Col(size_hint_y=1)
    for x in labels:
        c.add_widget(x)
    return c


# ---------------------------------------------------------------- pages
class Page(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.main_box = FloatLayout()
        
        self.sv = ScrollView(effect_cls=ScrollEffect, bar_width=0, smooth_scroll_end=10, size_hint=(1, 1))
        
        self.body = Col(padding=[dp(20), dp(76), dp(20), dp(110)], spacing=dp(14))
        self.sv.add_widget(self.body)
        
        self.top_bar = Row(h=56, padding=[dp(20), dp(10), dp(20), 0], bg=TRANSP, radius=0, size_hint=(1, None), pos_hint={'top': 1})
        
        self.main_box.add_widget(self.sv)
        self.main_box.add_widget(self.top_bar)
        
        self.add_widget(self.main_box)

    def on_pre_enter(self, *_):
        self.body.clear_widgets()
        self.top_bar.clear_widgets()
        self.top_bar.add_widget(Burger(on_release=lambda *_: App.get_running_app().root.toggle()))
        self.top_bar.add_widget(Widget())
        self.extra(self.top_bar)
        self.build(self.body)
        self.sv.scroll_y = 1

    def extra(self, row):
        pass

    def build(self, b):
        pass


class Home(Page):
    def build(self, b):
        go = lambda *_: App.get_running_app().root.go('manutencao')
        b.add_widget(L('TECHNO CAR', 32, bold=True, align='center'))
        b.add_widget(L('PERFORMANCE & CARE', 11, ACCENT, align='center'))
        ban = Tap(cb=go, orientation='horizontal', bg=PRIMARY, radius=16, padding=dp(18), spacing=dp(8))
        ban.add_widget(Col(spacing=dp(2)))
        t = ban.children[0]
        t.add_widget(L('Ver manutenções', 20, bold=True))
        t.add_widget(L('Acompanhe revisões e alertas pendentes', 12, C('E8C0CB')))
        ban.add_widget(Btn(text='>', bg=[1, 1, 1, .25], circle=True, size_hint=(None, None),
                           size=(dp(38), dp(38)), font_size=sp(18), on_release=go))
        b.add_widget(ban)

        v = Store.vehicle()
        card = Col(bg=CARD, border=BORDER, radius=16, padding=dp(16), spacing=dp(12))
        head = Row(h=44)
        head.add_widget(stack(L('VEÍCULOS ATIVOS', 10, ACCENT, True), L(v['nome'] if v else 'Nenhum veículo', 18, bold=True)))
        if v:
            head.add_widget(chip('ATIVO'))
        card.add_widget(head)
        
        oil = next((m for m in Store.data['maint'] if m.get('cat') == 'ÓLEO' and m.get('placa') == v['placa']), None) if v else None
        pct, rest = (int(oil['troca'] / oil['prox'] * 100), oil['prox'] - oil['troca']) if oil and oil['prox'] else (0, 0)
        mini = Row(h=74, spacing=dp(10))
        
        o_txt = v.get('oleo') or 'N/A' if v else 'N/A'
        p_txt = v.get('pneu') or 'N/A' if v else 'N/A'

        for a, bb, c, col in (('ÓLEO DO MOTOR', o_txt, f'Troca em {km(rest)}' if oil else 'Sem registro', ACCENT),
                              ('PRESSÃO PNEUS', p_txt, 'Monitorado', GREEN)):
            x = Col(bg=INNER, radius=10, padding=dp(10), spacing=dp(2), size_hint_y=1)
            x.add_widget(L(a, 9, MUTED))
            x.add_widget(L(bb, 15, bold=True))
            x.add_widget(L(c, 9, col))
            mini.add_widget(x)
        card.add_widget(mini)
        b.add_widget(card)

        if Store.data.get('alerts'):
            hd = Row(h=24)
            hd.add_widget(L('PRÓXIMOS ALERTAS', 13, bold=True))
            hd.add_widget(L('Ver Todos', 11, ACCENT, align='right'))
            b.add_widget(hd)
            for t1, t2, d in Store.data['alerts']:
                r = Row(h=66, bg=CARD, border=BORDER, radius=12, padding=dp(12), spacing=dp(12))
                ic = Box(bg=PRIMARY, radius=8, size_hint=(None, None), size=(dp(40), dp(40)))
                ic.add_widget(L('!', 18, bold=True, align='center'))
                r.add_widget(ic)
                r.add_widget(stack(L(t1, 14, bold=True), L(t2, 11, MUTED)))
                r.add_widget(Col(size_hint_x=None, width=dp(40)))
                q = r.children[0]
                q.add_widget(L(str(d), 15, ACCENT, True, 'right'))
                q.add_widget(L('DIAS', 8, MUTED, align='right'))
                b.add_widget(r)

        b.add_widget(Widget(size_hint_y=None, height=dp(5)))
        hd_hist = Row(h=24)
        hd_hist.add_widget(L('ÚLTIMAS MANUTENÇÕES', 13, bold=True))
        b.add_widget(hd_hist)

        if v:
            active_maint_names = [m['nome'] for m in Store.data['maint'] if m.get('placa') == v['placa']]
            v_hist = [h for h in Store.data['hist'] if len(h) > 4 and h[4] == v['placa'] and h[1] in active_maint_names]
            
            seen = set()
            v_hist_unique = []
            for item in v_hist:
                nome_historico = item[1]
                if nome_historico not in seen:
                    seen.add(nome_historico)
                    v_hist_unique.append(item)
            
            last_3 = v_hist_unique[:3]
            
            if last_3:
                hist_card = Col(bg=CARD, border=BORDER, radius=12, padding=dp(16), spacing=dp(10))
                for idx, item in enumerate(last_3):
                    tg, title, date, k, placa = item
                    
                    item_row = Col(orientation='horizontal', spacing=dp(12))
                    linha_vermelha = Box(bg=PRIMARY, radius=2, size_hint_x=None, width=dp(4))
                    
                    text_col = Col(spacing=dp(4))
                    text_col.add_widget(L(title, 14, bold=True))
                    text_col.add_widget(L(f'{date} • {km(k)}', 11, MUTED))
                    
                    text_col.bind(minimum_height=item_row.setter('height'))
                    
                    item_row.add_widget(linha_vermelha)
                    item_row.add_widget(text_col)
                    
                    hist_card.add_widget(item_row)
                    
                    if idx < len(last_3) - 1:
                        hist_card.add_widget(Box(bg=BORDER, radius=0, size_hint_y=None, height=dp(1)))
                b.add_widget(hist_card)
            else:
                b.add_widget(L('Nenhum registro para este veículo.', 12, MUTED))
        else:
            b.add_widget(L('Selecione um veículo ativo para ver o histórico.', 12, MUTED))


class Vehicles(Page):
    def build(self, b):
        b.add_widget(L('VEÍCULOS', 30, bold=True, align='center'))
        b.add_widget(L('GERENCIAR GARAGEM', 11, ACCENT, align='center'))
        
        b.add_widget(Btn(text='+ Adicionar Novo Veículo', bg=PRIMARY, radius=12, size_hint_y=None, height=dp(48),
                         on_release=lambda *_: self.open_form()))

        vs = Store.data['vehicles']
        b.add_widget(L(f'MEUS VEÍCULOS ({len(vs)})', 12, bold=True))
        for i, v in enumerate(vs):
            act = i == Store.data.get('active', 0)
            c = Tap(cb=lambda i=i: self.activate(i), bg=CARD, radius=16, border=ACCENT if act else BORDER,
                    padding=dp(14), spacing=dp(10))
            head = Row(h=46)
            head.add_widget(stack(L(v.get('tipo', 'VEÍCULO'), 10, ACCENT, True), L(v['nome'], 17, bold=True)))
            if act:
                head.add_widget(chip('ATIVO'))
            c.add_widget(head)
            
            info_col = Col(spacing=dp(10))
            
            r1 = Row(h=54, spacing=dp(10))
            for k, val in (('PLACA', v['placa']), ('KM TOTAL', km(v['km']))):
                x = Col(bg=INNER, radius=10, padding=dp(10), spacing=dp(2), size_hint_y=1)
                x.add_widget(L(k, 9, MUTED))
                x.add_widget(L(val, 14, bold=True))
                r1.add_widget(x)
            info_col.add_widget(r1)

            r2 = Row(h=54, spacing=dp(10))
            for k, val in (('ÓLEO', v.get('oleo', '')), ('PRESSÃO', v.get('pneu', ''))):
                x = Col(bg=INNER, radius=10, padding=dp(10), spacing=dp(2), size_hint_y=1)
                x.add_widget(L(k, 9, MUTED))
                display_val = val if val else 'N/A'
                x.add_widget(L(str(display_val), 14, bold=True))
                r2.add_widget(x)
            info_col.add_widget(r2)
            
            c.add_widget(info_col)
            
            btns = Row(h=32, spacing=dp(10))
            btns.add_widget(Btn(text='KM', bg=ACCENT, radius=8, size_hint_x=0.8, font_size=sp(11),
                                on_release=lambda *_, i=i: self.edit_km(i)))
            btns.add_widget(Btn(text='MANUTENÇÃO', bg=PRIMARY, radius=8, size_hint_x=1.2, font_size=sp(11),
                                on_release=lambda *_, i=i: self.add_maint(i)))
            btns.add_widget(Btn(text='EDITAR', bg=ACCENT, radius=8, size_hint_x=0.9, font_size=sp(11),
                                on_release=lambda *_, i=i: self.open_form(i)))
            c.add_widget(btns)
            b.add_widget(c)

    def open_form(self, index=None):
        is_edit = index is not None
        v_data = Store.data['vehicles'][index] if is_edit else {}

        box = Col(padding=dp(12), spacing=dp(10))
        inp = {}
        for k, lab, hint in (('nome', 'NOME', 'Ex: Honda Civic 2021'),
                             ('placa', 'PLACA', 'Ex: ABC-1234'),
                             ('km', 'QUILOMETRAGEM', 'Ex: 45000'),
                             ('oleo', 'ÓLEO DO MOTOR (Opcional)', 'Ex: 10W30'),
                             ('pneu', 'PRESSÃO DOS PNEUS (Opcional)', 'Ex: 30 F - 32 T')):
            box.add_widget(L(lab, 10, ACCENT, True))
            t = TI(hint_text=hint, text=str(v_data.get(k, '')), **({'input_filter': 'int'} if k == 'km' else {}))
            inp[k] = t
            box.add_widget(t)

        def save_form(*_):
            n, p, k, o, pn = (inp[x].text.strip().upper() for x in ('nome', 'placa', 'km', 'oleo', 'pneu'))
            if not n or not p:
                return
            
            new_data = {
                'tipo': v_data.get('tipo', 'VEÍCULO'), 'nome': n, 'placa': p,
                'km': int(k) if k.isdigit() else 0, 'oleo': o, 'pneu': pn
            }
            
            if is_edit:
                old_placa = v_data.get('placa')
                Store.data['vehicles'][index].update(new_data)
                
                if old_placa and old_placa != p:
                    for m in Store.data['maint']:
                        if m.get('placa') == old_placa: m['placa'] = p
                    for h in Store.data['hist']:
                        if len(h) > 4 and h[4] == old_placa: h[4] = p
            else:
                Store.data['vehicles'].append(new_data)
                Store.data['active'] = len(Store.data['vehicles']) - 1
                
            Store.save()
            popup_w.dismiss()
            self.on_pre_enter()

        box.add_widget(Btn(text='SALVAR', size_hint_y=None, height=dp(46), on_release=save_form))
        
        sv = ScrollView(effect_cls=ScrollEffect, size_hint=(1, 1))
        sv.add_widget(box)
        popup_w = popup('Editar Veículo' if is_edit else 'Adicionar Veículo', sv, 620)

    def activate(self, i):
        Store.data['active'] = i
        Store.save()
        self.on_pre_enter()

    def edit_km(self, i):
        t = TI(text=str(Store.data['vehicles'][i]['km']), input_filter='int')
        def ok(*_):
            Store.data['vehicles'][i]['km'] = int(t.text or 0)
            Store.save()
            p.dismiss()
            self.on_pre_enter()
        box = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12))
        box.add_widget(t)
        box.add_widget(Btn(text='SALVAR', size_hint_y=None, height=dp(44), on_release=ok))
        p = popup('Atualizar quilometragem', box, 280)

    def add_maint(self, i):
        v = Store.data['vehicles'][i]
        
        box = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12))
        
        box.add_widget(L('TIPO DE MANUTENÇÃO', 10, ACCENT, True))
        t_desc = TI(hint_text='Ex: Troca de Óleo, Pastilha, Pneu...')
        box.add_widget(t_desc)
        
        box.add_widget(L('KM DA MANUTENÇÃO', 10, ACCENT, True))
        t_km = TI(text=str(v['km']), input_filter='int')
        box.add_widget(t_km)
        
        box.add_widget(L('PRÓXIMO KM PARA MANUTENÇÃO', 10, ACCENT, True))
        t_prox = TI(text=str(v['km'] + 5000), input_filter='int')
        box.add_widget(t_prox)
        
        box.add_widget(Widget())

        def ok(*_):
            desc = t_desc.text.strip().upper()
            km_val = int(t_km.text or 0)
            prox_val = int(t_prox.text or 0)
            
            if desc:
                hoje = datetime.now().strftime("%d/%m/%Y")
                Store.data['hist'].insert(0, ['REVISÃO', desc, hoje, km_val, v['placa']])
                Store.data['maint'].insert(0, {
                    'cat': 'REVISÃO', 'nome': desc, 'troca': km_val, 
                    'prox': prox_val, 'placa': v['placa']
                })
                if km_val > v['km']:
                    v['km'] = km_val
                Store.save()
                p.dismiss()
                self.on_pre_enter()

        box.add_widget(Btn(text='SALVAR', size_hint_y=None, height=dp(44), on_release=ok))
        p = popup('Registrar Manutenção', box, 480)


class Maint(Page):
    def build(self, b):
        v = Store.vehicle()
        if v:
            btn_top = Btn(text=f"{v['nome']} • {v['placa']}   ▼", bg=PRIMARY, radius=8,
                          size_hint_y=None, height=dp(38), font_size=sp(12),
                          on_release=self.open_selector)
            b.add_widget(btn_top)
            
        b.add_widget(L('Manutenções', 28, bold=True))
        b.add_widget(L('Acompanhe o desgaste e saúde de cada item', 12, MUTED))
        
        maint_list = [m for m in Store.data['maint'] if m.get('placa') == v['placa']] if v else []
        
        if not maint_list:
            b.add_widget(L('\nNenhuma manutenção registrada para este veículo.', 13, MUTED, align='center'))
            
        for m in maint_list:
            idx = Store.data['maint'].index(m)
            
            rest = m['prox'] - m['troca']
            frac = m['troca'] / m['prox'] if m['prox'] else 0
            col = RED if frac >= .8 else AMBER if frac >= .6 else GREEN
            
            c = Col(bg=CARD, border=BORDER, radius=14, padding=dp(14), spacing=dp(8))
            r = Row(h=46)
            r.add_widget(stack(L(m.get('cat', 'REVISÃO'), 10, ACCENT, True), L(m['nome'], 15, bold=True)))
            q = stack(L(km(rest), 16, col, True, 'right'), L('RESTANTES', 9, MUTED, align='right'))
            q.size_hint_x, q.width = None, dp(104)
            r.add_widget(q)
            c.add_widget(r)
            
            c.add_widget(Bar(frac, col))
            
            f = Row(h=16)
            f.add_widget(L(f"Troca: {km(m['troca'])}", 10, MUTED))
            f.add_widget(L(f"Próxima: {km(m['prox'])}", 10, MUTED, align='right'))
            c.add_widget(f)
            
            bot_row = Row(h=26, spacing=dp(8))
            bot_row.add_widget(Widget()) 
            
            bot_row.add_widget(Btn(text='EDITAR', bg=LIGHT_RED, radius=6, font_size=sp(10), size_hint_x=None, width=dp(70), on_release=lambda *_, i=idx: self.edit_maint(i)))
            bot_row.add_widget(Btn(text='EXCLUIR', bg=RED, radius=6, font_size=sp(10), size_hint_x=None, width=dp(70), on_release=lambda *_, i=idx: self.confirm_delete(i)))
            
            c.add_widget(bot_row)
            b.add_widget(c)

    def open_selector(self, *_):
        box = Col(padding=dp(12), spacing=dp(8))
        for i, veh in enumerate(Store.data['vehicles']):
            btn = Btn(text=f"{veh['nome']} • {veh['placa']}", size_hint_y=None, height=dp(44),
                      bg=ACCENT if i == Store.data.get('active', 0) else INNER,
                      on_release=lambda *_, idx=i: self.select_vehicle(idx))
            box.add_widget(btn)
        
        sv = ScrollView(effect_cls=ScrollEffect, size_hint=(1, 1))
        sv.add_widget(box)
        self.pop = popup('Selecionar Veículo', sv, min(500, 140 + 60 * len(Store.data['vehicles'])))

    def select_vehicle(self, idx):
        Store.data['active'] = idx
        Store.save()
        self.pop.dismiss()
        self.on_pre_enter()
        
    def edit_maint(self, idx):
        m_data = Store.data['maint'][idx]
        box = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12))
        
        box.add_widget(L('TIPO DE MANUTENÇÃO', 10, ACCENT, True))
        t_desc = TI(text=m_data['nome'])
        box.add_widget(t_desc)
        
        box.add_widget(L('KM DA MANUTENÇÃO', 10, ACCENT, True))
        t_km = TI(text=str(m_data['troca']), input_filter='int')
        box.add_widget(t_km)
        
        box.add_widget(L('PRÓXIMO KM PARA MANUTENÇÃO', 10, ACCENT, True))
        t_prox = TI(text=str(m_data['prox']), input_filter='int')
        box.add_widget(t_prox)
        
        box.add_widget(Widget())

        def ok(*_):
            desc = t_desc.text.strip().upper()
            if desc:
                m_data['nome'] = desc
                m_data['troca'] = int(t_km.text or 0)
                m_data['prox'] = int(t_prox.text or 0)
                Store.save()
                p.dismiss()
                self.on_pre_enter()

        box.add_widget(Btn(text='SALVAR', size_hint_y=None, height=dp(44), on_release=ok))
        p = popup('Editar Manutenção', box, 480)

    def confirm_delete(self, idx):
        m_data = Store.data['maint'][idx]
        nome_maint = m_data['nome']
        km_maint = m_data['troca']
        placa_maint = m_data['placa']
        
        box = Col(padding=dp(16), spacing=dp(12))
        
        def do_delete(also_hist, *_):
            Store.data['maint'].pop(idx)
            if also_hist:
                Store.data['hist'] = [
                    h for h in Store.data['hist'] 
                    if not (len(h) > 4 and h[1] == nome_maint and h[3] == km_maint and h[4] == placa_maint)
                ]
            Store.save()
            p.dismiss()
            self.on_pre_enter()
            
        box.add_widget(Btn(text='SIM, APAGAR DE TUDO', bg=RED, size_hint_y=None, height=dp(44), on_release=lambda *_: do_delete(True)))
        box.add_widget(Btn(text='NÃO, SÓ DA MANUTENÇÃO', bg=LIGHT_RED, size_hint_y=None, height=dp(44), on_release=lambda *_: do_delete(False)))
        box.add_widget(Btn(text='CANCELAR', bg=INNER, size_hint_y=None, height=dp(44), on_release=lambda *_: p.dismiss()))
        
        p = popup('Confirmar Exclusão', box, 300)


class Hist(Page):
    def extra(self, row):
        row.add_widget(Bell())

    def build(self, b):
        b.add_widget(L('HISTÓRICO', 30, bold=True))
        b.add_widget(L('Registro de todas as manutenções cadastradas', 12, MUTED))
        
        items = Store.data.get('hist', [])

        if not items:
             b.add_widget(L('\nNenhum histórico registrado.', 13, MUTED, align='center'))

        for n, item in enumerate(items):
            tg, title, date, k = item[:4]
            placa = item[4] if len(item) > 4 else 'Desconhecido'
            
            col = TAG.get(tg, MUTED)
            
            c = Col(bg=CARD, border=BORDER, radius=12, padding=dp(12), spacing=dp(6))
            
            h = Row(h=24)
            h.add_widget(tag(tg, col))
            h.add_widget(L(km(k), 12, bold=True, align='right'))
            c.add_widget(h)
            c.add_widget(L(title, 13, bold=True))
            c.add_widget(L(f'Veículo: {placa} • Realizado em: {date}', 10, MUTED))
            
            b.add_widget(c)


class Config(Page):
    def build(self, b):
        b.add_widget(L('CONFIGURAÇÕES', 26, bold=True, align='center'))
        b.add_widget(L('PREFERÊNCIAS DO APP', 11, ACCENT, align='center'))
        c = Col(bg=CARD, border=BORDER, radius=16, padding=dp(16), spacing=dp(6))
        c.add_widget(L('Fael Do Grau', 16, bold=True))
        c.add_widget(L('faelfingequeedograu.com', 12, MUTED))
        b.add_widget(c)
        on = Store.data.get('notif', True)
        b.add_widget(Btn(text=f"Notificações: {'ATIVADAS' if on else 'DESATIVADAS'}", bg=PRIMARY if on else INNER,
                         size_hint_y=None, height=dp(48), on_release=self.notif))
        b.add_widget(Btn(text='Apagar todos os dados', bg=INNER, size_hint_y=None, height=dp(48),
                         on_release=self.reset))

    def notif(self, *_):
        Store.data['notif'] = not Store.data.get('notif', True)
        Store.save()
        self.on_pre_enter()

    def reset(self, *_):
        Store.reset()
        Store.save()
        self.on_pre_enter()


# ---------------------------------------------------------------- root
class Root(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.pw = min(dp(300), Window.width * .8)
        
        self.effect_widget = EffectWidget()
        
        self.sm = ScreenManager(transition=FadeTransition(duration=0.25))
        for n, cls in (('inicio', Home), ('veiculos', Vehicles), ('manutencao', Maint),
                       ('historico', Hist), ('config', Config)):
            self.sm.add_widget(cls(name=n))
            
        self.effect_widget.add_widget(self.sm)
        self.add_widget(self.effect_widget)
        
        self.add_widget(Btn(text='?', bg=ACCENT, circle=True, size_hint=(None, None), size=(dp(56), dp(56)),
                            pos_hint={'right': .94, 'y': .03}, font_size=sp(15),
                            on_release=lambda *_: self.assist()))
        self.dim = Btn(bg=[0, 0, 0, .6], radius=0, opacity=0, size_hint=(None, None), size=(0, 0),
                       on_release=lambda *_: self.toggle(False))
        self.add_widget(self.dim)

        self.panel = Box(bg=PANEL, radius=0, orientation='vertical', size_hint=(None, 1), width=self.pw, x=-self.pw)
        head = Col(bg=CARD, radius=0, padding=[dp(20), dp(44), dp(20), dp(16)], spacing=dp(10))
        r = Row(h=52)
        r.add_widget(Ring())
        r.add_widget(Widget())
        r.add_widget(Btn(text='x', bg=INNER, circle=True, size_hint=(None, None), size=(dp(34), dp(34)),
                         color=MUTED, on_release=lambda *_: self.toggle(False)))
        head.add_widget(r)
        head.add_widget(L('Fael Do Grau', 16, bold=True))
        head.add_widget(L('faelfingequeedograu.com', 11, MUTED))
        self.panel.add_widget(head)
        
        self.menu = Col(padding=[dp(16), dp(16), dp(16), dp(16)], spacing=dp(8))
        self.panel.add_widget(self.menu)
        self.panel.add_widget(Widget())
        self.add_widget(self.panel)
        self.sm.bind(current=self.refresh_menu)
        self.refresh_menu()

    def blur_bg(self, enable=True):
        if enable:
            self.effect_widget.effects = [HorizontalBlurEffect(size=12.0), VerticalBlurEffect(size=12.0)]
        else:
            self.effect_widget.effects = []

    def refresh_menu(self, *_):
        self.menu.clear_widgets()
        for n, lab in MENU:
            self.menu.add_widget(Item(lab, n == self.sm.current, cb=lambda n=n: self.go(n)))

    def toggle(self, open_=None):
        open_ = (self.panel.x < 0) if open_ is None else open_
        if open_:
            self.dim.size_hint, self.dim.size = (1, 1), Window.size
        else:
            a = Animation(opacity=0, d=.2)
            a.bind(on_complete=lambda *_: setattr(self.dim, 'size_hint', (None, None)) or
                   setattr(self.dim, 'size', (0, 0)))
            a.start(self.dim)
        Animation(x=0 if open_ else -self.pw, d=.22, t='out_quad').start(self.panel)
        if open_:
            Animation(opacity=1, d=.2).start(self.dim)

    def go(self, name):
        self.sm.current = name
        self.toggle(False)

    def assist(self):
        v = Store.vehicle()
        v_name = v['nome'] if v else 'Nenhum veículo'

        chat_modal = ModalView(size_hint=(1, 1), background='', background_color=[0, 0, 0, 0])
        root_box = Box(bg=BG, radius=0, orientation='vertical', size_hint=(1, 1))

        # --- header ---
        header = Row(h=70, bg=BG, radius=0, padding=[dp(16), dp(10), dp(16), dp(4)], spacing=dp(12))
        header.add_widget(Btn(text='<', bg=CARD, radius=10, size_hint=(None, None),
                              size=(dp(40), dp(40)), font_size=sp(18),
                              on_release=lambda *_: chat_modal.dismiss()))
        
        avatar = Box(bg=CARD, radius=20, border=ACCENT, size_hint=(None, None), size=(dp(40), dp(40)))
        # Usando a fonte padrão do Kivy para garantir que o emoji renderize
        avatar.add_widget(Label(text='🤖', font_size=sp(20), color=WHITE))
        header.add_widget(avatar)
        
        hdr_text = Col(spacing=dp(2), size_hint_y=None, height=dp(36), pos_hint={'center_y': .5})
        hdr_text.add_widget(L('TECHNO BOT', 16, WHITE, True))
        
        dot_row = Row(h=14, spacing=dp(4))
        dot_row.add_widget(L('●', 10, ACCENT, size_hint_x=None, width=dp(12)))
        dot_row.add_widget(L('Assistente automotivo', 11, MUTED))
        hdr_text.add_widget(dot_row)
        
        header.add_widget(hdr_text)
        header.add_widget(Widget())
        
        # Quadrado do canto superior direito removido.
        root_box.add_widget(header)
        
        root_box.add_widget(Box(bg=BORDER, size_hint_y=None, height=dp(1)))

        # --- vehicle card ---
        v_card_wrap = Col(padding=[dp(16), dp(16), dp(16), dp(8)], size_hint_y=None, height=dp(80))
        v_card = Row(h=48, bg=CARD, radius=12, padding=[dp(12), dp(0), dp(12), dp(0)], spacing=dp(12))
        v_icon = Box(bg=INNER, radius=10, size_hint=(None, None), size=(dp(36), dp(36)), pos_hint={'center_y': .5})
        
        # Trocando por um emote renderizável baseado no veículo do usuário
        veh_icon = '🏍' if v and v.get('tipo') == 'MOTO' else '🚘'
        v_icon.add_widget(Label(text=veh_icon, font_size=sp(16), color=ACCENT))
        v_card.add_widget(v_icon)
        
        vc_text = Col(spacing=dp(2), size_hint_y=None, height=dp(32), pos_hint={'center_y': .5})
        vc_text.add_widget(L('SEU VEÍCULO', 9, MUTED))
        vc_text.add_widget(L(v_name, 13, WHITE, True))
        v_card.add_widget(vc_text)
        v_card.add_widget(Widget())
        v_card.add_widget(L('Selecionado', 11, ACCENT, align='right'))
        
        v_card_wrap.add_widget(v_card)
        root_box.add_widget(v_card_wrap)

        # --- messages area ---
        messages_sv = ScrollView(effect_cls=ScrollEffect, bar_width=0, size_hint=(1, 1))
        
        # Convertido para BoxLayout padrão para permitir preenchimento flexível
        messages_col = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(16), dp(10), dp(16), dp(20)], spacing=dp(16))
        
        # Spacer que ocupa o espaço vazio do topo para empurrar o chat para baixo
        spacer = Widget(size_hint_y=1)
        messages_col.add_widget(spacer)

        def adjust_height(*_):
            messages_col.height = max(messages_col.minimum_height, messages_sv.height)
            
        messages_col.bind(minimum_height=adjust_height)
        messages_sv.bind(height=adjust_height)

        messages_col.add_widget(L('Hoje', 11, MUTED, align='center'))

        now_str = datetime.now().strftime("%H:%M")
        
        def add_msg(txt, is_user=False):
            bubble_wrap = Row(size_hint_y=None)
            
            b_bg = ACCENT if not is_user else PRIMARY
            bubble = Col(bg=b_bg, radius=16, size_hint=(None, None), padding=[dp(14), dp(10), dp(14), dp(6)], spacing=dp(4))
            
            lbl = L(txt, 14, WHITE)
            lbl.text_size = (dp(240), None)
            lbl.bind(texture_size=lambda i, s: setattr(i, 'height', s[1]))
            
            time_row = Row(h=12)
            time_row.add_widget(Widget())
            time_lbl = L(now_str + (' ✓' if is_user else ''), 9, [1, 1, 1, 0.6], align='right')
            time_row.add_widget(time_lbl)
            
            bubble.add_widget(lbl)
            bubble.add_widget(time_row)
            
            def upd_bubble_size(*_):
                bubble.height = lbl.height + dp(32)
                bubble.width = max(lbl.texture_size[0], time_lbl.texture_size[0]) + dp(28)
                bubble_wrap.height = bubble.height
                
            lbl.bind(texture_size=upd_bubble_size)
            
            if is_user:
                bubble_wrap.add_widget(Widget())
                bubble_wrap.add_widget(bubble)
            else:
                bubble_wrap.add_widget(bubble)
                bubble_wrap.add_widget(Widget())
                
            messages_col.add_widget(bubble_wrap)
            
        greeting = f"Olá, Fael! Sou o TECHNO BOT.\nComo posso cuidar da sua {'moto' if v and v.get('tipo') == 'MOTO' else 'veículo'}?"
        add_msg(greeting, False)

        self._chat_messages = messages_col
        self._chat_sv = messages_sv

        messages_sv.add_widget(messages_col)
        root_box.add_widget(messages_sv)

        # --- input bar ---
        input_wrap = Col(size_hint_y=None, height=dp(80), padding=[dp(16), dp(10), dp(16), dp(10)], spacing=dp(8))
        
        input_bar = Row(h=50, spacing=dp(10))

        inp_box = Box(bg=CARD, border=BORDER, radius=25, padding=[dp(16), dp(0), dp(12), dp(0)])
        msg_input = TextInput(
            hint_text='Digite sua mensagem...',
            background_normal='', background_active='', background_color=[0, 0, 0, 0],
            foreground_color=WHITE, hint_text_color=MUTED, cursor_color=ACCENT,
            font_size=sp(14), font_name=FONT_REGULAR, multiline=False, size_hint_y=None, height=dp(30), pos_hint={'center_y': .5}
        )
        inp_box.add_widget(msg_input)
        inp_box.add_widget(Btn(text='@', bg=TRANSP, color=MUTED, size_hint=(None, None), size=(dp(30), dp(30)), pos_hint={'center_y': .5}))
        
        input_bar.add_widget(inp_box)

        def send_msg(*_):
            text = msg_input.text.strip()
            if not text: return
            add_msg(text, True)
            msg_input.text = ''
            # Removida a lógica de resposta automática
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(self._chat_sv, 'scroll_y', 0), 0.1)

        # Enviar com emote customizado via Tap em vez do caractere de fonte problemática
        send_btn = Tap(bg=ACCENT, radius=14, size_hint=(None, None), size=(dp(50), dp(50)), cb=send_msg)
        send_btn.add_widget(Label(text='🚀', font_size=sp(20), color=WHITE))
        input_bar.add_widget(send_btn)

        input_wrap.add_widget(input_bar)
        input_wrap.add_widget(L('Assistente virtual · Não substitui uma avaliação técnica', 9, MUTED, align='center'))

        root_box.add_widget(input_wrap)
        
        chat_modal.add_widget(root_box)
        
        chat_modal.opacity = 0
        def on_chat_open(*_):
            self.blur_bg(True)
            Animation(opacity=1, d=0.25, t='out_quad').start(chat_modal)
        def on_chat_dismiss(*_):
            self.blur_bg(False)
        chat_modal.bind(on_open=on_chat_open, on_dismiss=on_chat_dismiss)
        chat_modal.open()


class TechnoCarApp(App):
    title = 'Techno Car'

    def build(self):
        Window.softinput_mode = 'below_target'
        Store.load(self.user_data_dir)
        return Root()


if __name__ == '__main__':
    TechnoCarApp().run()