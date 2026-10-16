"""Generate the Kiln theme files for both variants.

Writes src/main/resources/themes/kiln-{dark,light}.theme.json and the matching
editor color schemes (.xml) from the palettes defined below.

The themes inherit from JetBrains' Islands themes, so this script reads the Islands
color tokens from an IntelliJ install. Edit a palette, then run:

    ./gradlew generateThemes

That passes the IDE Gradle builds against, so everyone generates from the same
version. To use another install, run the script directly with its path:

    python3 scripts/generate_themes.py "/Applications/IntelliJ IDEA.app"
"""
import json, math, sys, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'src/main/resources/themes'
ISLANDS = 'themes/islands/ManyIslands{}.theme.json'

def find_islands_jar(ide):
    """The jar inside an IntelliJ install that holds the Islands themes."""
    for lib in (ide / 'lib', ide / 'Contents/lib'):
        for jar in sorted(lib.glob('*.jar')):
            with zipfile.ZipFile(jar) as z:
                if ISLANDS.format('Dark') in z.namelist():
                    return jar
    sys.exit(f'No Islands themes found in {ide}. Pass the folder of IntelliJ IDEA 2026.2 or newer.')

if len(sys.argv) != 2:
    sys.exit('Usage: python3 scripts/generate_themes.py <IntelliJ install folder>  (or run ./gradlew generateThemes)')
JAR = find_islands_jar(Path(sys.argv[1]).expanduser())

def islands_colors(variant):
    """Color tokens of the bundled Islands Dark or Islands Light theme."""
    with zipfile.ZipFile(JAR) as z:
        colors = json.loads(z.read(ISLANDS.format(variant)))['colors']
    if 'main-window-bg' not in colors:
        sys.exit(f'{JAR} has the old Islands colors. Kiln needs IntelliJ IDEA 2026.2 or newer.')
    return colors

# ---------- color math (OKLab) ----------
def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def lin_to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def hex_to_rgb(h):
    h = h.lstrip('#')[:6]
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
def rgb_to_hex(rgb):
    return '#' + ''.join(f'{round(max(0, min(1, c)) * 255):02X}' for c in rgb)
def to_oklab(h):
    r, g, b = (srgb_to_lin(c) for c in hex_to_rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (x ** (1 / 3) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)
def from_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return [lin_to_srgb(c) if c > 0 else 0 for c in rgb], all(-1e-4 <= c <= 1 + 1e-4 for c in rgb)
def oklch(L, C, H):
    # reduce chroma until in gamut
    while True:
        rgb, ok = from_oklab(L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)))
        if ok or C < 0.001:
            return rgb_to_hex(rgb)
        C *= 0.95
def lum(h):
    r, g, b = (srgb_to_lin(c) for c in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

# ---------- ramps: Islands gray -> warm neutral, Islands blue -> clay ----------
islands = islands_colors('Dark')
CLAY_HUE = 40.5      # hue of #D97757
NEUTRAL_HUE = 95.0   # hue of the cream and charcoal neutrals
ramps = {}
for k, v in islands.items():
    m = re.match(r'^(gray|blue)-(\d+)$', k)
    if not m:
        continue
    L, a, b = to_oklab(v)
    if m.group(1) == 'gray':
        ramps[k] = oklch(L, 0.004 + 0.008 * L, NEUTRAL_HUE)
    else:
        C = math.hypot(a, b)
        ramps[k] = oklch(L, C * 0.72, CLAY_HUE)

# ---------- palettes ----------
DARK = dict(
    # surfaces
    frame='#1A1918', toolAlt='#22211F', bg='#262624', bg2='#2C2B28', raised='#2E2D2A', border='#34332F', border2='#3E3C37',
    fg='#E8E6DC', muted='#A8A59A', secondary='#8A877D', disabled='#5F5D56',
    accent='#D97757', accentStrong='#C96442', link='#E0896A',
    selection='#4A3B33', selectionMuted='#3A322C', selectionInactive='#34332F',
    caretRow='#2D2C29', lineNum='#5F5D56', lineNumCur='#B5B2A6',
    indent='#34332F', indentSel='#4A4843', whitespace='#45433E',
    # syntax
    keyword='#D97757', string='#A9B57E', number='#86BFAE', type='#8DB4D4', method='#E3BE7E',
    annotation='#BD9ACF', field='#D4A27F', comment='#85827A', docTag='#A8A396', unused='#6E6B63',
    error='#E5735F', warning='#D9A54A', info='#8A7550',
    # highlights
    usage='#463B2F', usageStripe='#D4A27F', usageWrite='#52352F', usageWriteStripe='#D97757',
    search='#5A4430', searchStripe='#E3BE7E', textSearch='#6E5532',
    brace='#3E3C37', folded='#3A3935', inlayBg='#34332F', inlayFg='#9C998E', inlayCurBg='#6B4434', inlayCurFg='#F0D5C8',
    hintBg='#2E2D2A', errorHint='#4A2E28', breakpoint='#47302C', execution='#5C3A2C', injected='#2B2E28',
    smartCast='#2F3A2B', docCode='#2E2D2A',
    added='#6B8A4E', modified='#6F8FB0', deleted='#8A877D',
    vcsAge=('#6B4434', '#56392D', '#433027', '#352A24', '#2D2825'),
    # ANSI
    ansi=dict(BLACK='#3A3935', RED='#E5735F', GREEN='#A9B57E', YELLOW='#E3BE7E', BLUE='#8DB4D4',
              MAGENTA='#BD9ACF', CYAN='#86BFAE', GRAY='#C9C6BA', DARKGRAY='#6E6B63',
              RED_BRIGHT='#F08C78', GREEN_BRIGHT='#C2CC94', YELLOW_BRIGHT='#F0D29A', BLUE_BRIGHT='#A9C8E3',
              MAGENTA_BRIGHT='#D2B5E0', CYAN_BRIGHT='#A3D4C4', WHITE='#F5F3EC'),
)
LIGHT = dict(
    frame='#EAE7DE', toolAlt='#F5F3EC', bg='#FAF9F5', bg2='#F3F1EA', raised='#FFFFFF', border='#DEDAD0', border2='#CFCBC0',
    fg='#2A2925', muted='#5E5B53', secondary='#77736A', disabled='#A9A59A',
    accent='#C15F3C', accentStrong='#C15F3C', link='#B5532F',
    selection='#F3DCCF', selectionMuted='#F7E8DF', selectionInactive='#ECE9E0',
    caretRow='#F2F0E8', lineNum='#B3AFA3', lineNumCur='#6F6B60',
    indent='#E6E3DA', indentSel='#CFCBC0', whitespace='#D3CFC4',
    keyword='#B5532F', string='#5C7A2E', number='#2C7A6B', type='#2D6597', method='#8F6410',
    annotation='#8150A0', field='#9A5A2C', comment='#8D897C', docTag='#6F6B60', unused='#A9A59A',
    error='#C8432E', warning='#B07A12', info='#C9B48A',
    usage='#F0E4CF', usageStripe='#9A5A2C', usageWrite='#F6D6CC', usageWriteStripe='#C15F3C',
    search='#F6DFB4', searchStripe='#B07A12', textSearch='#F3D08F',
    brace='#E6E2D6', folded='#ECE9E0', inlayBg='#ECE9E0', inlayFg='#77736A', inlayCurBg='#F3DCCF', inlayCurFg='#7A3A22',
    hintBg='#FFFFFF', errorHint='#F9E2DC', breakpoint='#F7DDD6', execution='#F3D2C2', injected='#EEF2E6',
    smartCast='#E4EDD8', docCode='#F3F1EA',
    added='#9DB87A', modified='#8FB0D0', deleted='#B3AFA3',
    vcsAge=('#EFC9BB', '#F3D8CF', '#F6E4DB', '#F8EEE8', '#F9F5F0'),
    ansi=dict(BLACK='#2A2925', RED='#C8432E', GREEN='#5C7A2E', YELLOW='#8F6410', BLUE='#2D6597',
              MAGENTA='#8150A0', CYAN='#2C7A6B', GRAY='#77736A', DARKGRAY='#8D897C',
              RED_BRIGHT='#D9573F', GREEN_BRIGHT='#6E8F3A', YELLOW_BRIGHT='#A87A1A', BLUE_BRIGHT='#3A79B0',
              MAGENTA_BRIGHT='#9563B5', CYAN_BRIGHT='#33907E', WHITE='#B3AFA3'),
)

# ---------- theme.json ----------
def theme_json(p, dark):
    name = 'Kiln ' + ('Dark' if dark else 'Light')
    colors = dict(ramps)
    colors.update({
        # Kiln roles, usable by name below
        'kiln-frame': p['frame'], 'kiln-bg': p['bg'], 'kiln-bg-raised': p['raised'],
        'kiln-border': p['border'], 'kiln-fg': p['fg'], 'kiln-clay': p['accent'],
        'kiln-clay-strong': p['accentStrong'],
        # Islands semantic tokens
        'text-default': 'kiln-fg', 'editor-text': 'kiln-fg',
        'text-muted': p['muted'], 'text-secondary': p['secondary'], 'text-disabled': p['disabled'],
        'text-link': p['link'], 'text-error': p['error'], 'text-warning': p['warning'], 'text-success': p['string'],
        'main-window-bg': 'kiln-frame', 'main-window-border': 'kiln-frame',
        # the alternate Islands style, where tool windows get their own shade
        'main-window-bg-alt': 'kiln-frame', 'tool-window-bg-alt': p['toolAlt'], 'editor-border-alt': 'kiln-border',
        'editor-bg': 'kiln-bg', 'tool-window-bg': 'kiln-bg', 'dialog-bg': 'kiln-bg',
        'editor-bg-inline': p['bg2'], 'tool-window-bg-inline': p['bg2'], 'dialog-bg-inline': p['bg2'],
        'editor-border': 'kiln-border', 'tool-window-border': 'kiln-border', 'dialog-border': 'kiln-border',
        'popup-bg': 'kiln-bg-raised', 'popup-bg-inline': 'kiln-bg-raised',
        'popup-border': p['border2'] if dark else p['border'], 'popup-border-inline': p['border2'] if dark else p['border'],
        'accent-brand-bg': 'kiln-clay-strong', 'accent-brand-border': 'kiln-clay-strong',
        'selection-bg-active': p['selection'], 'selection-bg-active-muted': p['selectionMuted'],
        'selection-bg-inactive': p['selectionInactive'],
        'search-match-bg': p['search'],
        'tab-selected-border-active': 'kiln-clay',
        'popup-completion-match-text': 'kiln-clay',
    })
    # The parent theme resolves its own color chains before ours are applied, so every
    # Islands token is resolved here through our palette and written out as a hex value.
    parent = islands_colors('Dark' if dark else 'Light')
    merged = dict(parent)
    merged.update(colors)
    def resolve(v, depth=0):
        if v.startswith('#') or depth > 20:
            return v
        return resolve(merged[v], depth + 1)
    order = sorted(merged, key=lambda k: not k.startswith('kiln-'))
    colors = {k: resolve(merged[k]) for k in order}
    ui = {
        'Island.borderColor': 'tool-window-bg',
        'MainToolbar.borderColor': '#00000000',
        'StatusBar.borderColor': '#00000000',
        'ToolWindow.Stripe.borderColor': '#00000000',
        'ToolWindow.Header.background': 'tool-window-bg',
        'ToolWindow.Header.inactiveBackground': 'tool-window-bg',
        'EditorTabs.background': 'editor-bg',
        'EditorTabs.underlineColor': 'kiln-clay',
        'TabbedPane.underlineColor': 'kiln-clay',
        'ProgressBar.progressColor': 'kiln-clay',
        'ProgressBar.indeterminateStartColor': 'kiln-clay',
        'ProgressBar.indeterminateEndColor': 'kiln-clay-strong',
        'Editor.ToolTip.selectionBackground': p['selectionInactive'],
        'List.Tag.background': p['border'],
        'List.Tag.foreground': p['secondary'],
        'MainWindow.Tab.background': 'kiln-frame',
        'Debugger.Variables.changedValueForeground': p['link'],
        'Debugger.Variables.modifyingValueForeground': p['link'],
        'VersionControl.Log.Commit.currentBranchBackground': p['selectionMuted'],
        'VersionControl.FileHistory.Commit.selectedBranchBackground': p['selectionMuted'],
        'HelpBrowser.titleHighlightForeground': 'kiln-clay',
        'DataSummary.Chart.barColor': 'kiln-clay',
    }
    icons = {'ColorPalette': {
        'Checkbox.Background.Selected': p['accentStrong'],
        'Checkbox.Border.Selected': p['accentStrong'],
        'Checkbox.Focus.Wide': p['accent'],
        # default icon stroke of the New UI icon set, warmed to match the neutrals
        ('#CED0D6' if dark else '#6C707E'): colors['icon-default-stroke'],
    }}
    return {
        'name': name,
        'dark': dark,
        'author': 'Dan Vega',
        'parentTheme': 'Islands Dark' if dark else 'Islands Light',
        'editorScheme': '/themes/kiln-' + ('dark' if dark else 'light') + '.xml',
        'colors': colors,
        'ui': ui,
        'icons': icons,
    }

# ---------- editor scheme ----------
BOLD, ITALIC = 1, 2
LINE, WAVE, STRIKE, BOLD_DOTTED = 1, 2, 3, 5

def scheme_xml(p, dark):
    name = 'Kiln ' + ('Dark' if dark else 'Light')
    h = lambda c: c.lstrip('#').lower()
    colors = {
        'CARET_COLOR': p['accent'], 'CARET_ROW_COLOR': p['caretRow'],
        'LINE_NUMBERS_COLOR': p['lineNum'], 'LINE_NUMBER_ON_CARET_ROW_COLOR': p['lineNumCur'],
        'SELECTION_BACKGROUND': p['selection'],
        # empty keeps syntax colors in selected text (the Default parent paints it white)
        'SELECTION_FOREGROUND': '',
        'GUTTER_BACKGROUND': p['bg'], 'FOLDED_TEXT_BORDER_COLOR': p['border'],
        'DIFF_SEPARATORS_BACKGROUND': p['selectionInactive'], 'PROMOTION_PANE': p['selectionMuted'],
        'DOC_COMMENT_GUIDE': p['border2'], 'DOC_COMMENT_LINK': p['type'],
        'INLINE_REFACTORING_SETTINGS_DEFAULT': p['inlayBg'], 'INLINE_REFACTORING_SETTINGS_FOCUSED': p['inlayBg'],
        'INLINE_REFACTORING_SETTINGS_HOVERED': p['border2'],
        'INDENT_GUIDE': p['indent'], 'SELECTED_INDENT_GUIDE': p['indentSel'], 'VISUAL_INDENT_GUIDE': p['indent'],
        'MATCHED_BRACES_INDENT_GUIDE_COLOR': p['indentSel'],
        'RIGHT_MARGIN_COLOR': p['border'], 'METHOD_SEPARATORS_COLOR': p['border'], 'TEARLINE_COLOR': p['border'],
        'WHITESPACES': p['whitespace'],
        'CONSOLE_BACKGROUND_KEY': p['bg'], 'EDITOR_GUTTER_BACKGROUND': p['bg'],
        # alternate rows in the Data Editor grid (the Default parent paints them blue)
        'GRID_STRIPE_COLOR': p['bg2'],
        'DOCUMENTATION_COLOR': p['raised'], 'LOOKUP_COLOR': p['raised'], 'NOTIFICATION_BACKGROUND': p['raised'],
        'INFORMATION_HINT': p['hintBg'], 'QUESTION_HINT': p['hintBg'], 'ERROR_HINT': p['errorHint'],
        'HINT_BORDER': p['border2'], 'RECENT_LOCATIONS_SELECTION': p['selectionMuted'],
        'ADDED_LINES_COLOR': p['added'], 'MODIFIED_LINES_COLOR': p['modified'], 'DELETED_LINES_COLOR': p['deleted'],
        'WHITESPACES_MODIFIED_LINES_COLOR': p['modified'],
        'IGNORED_ADDED_LINES_BORDER_COLOR': p['added'], 'IGNORED_MODIFIED_LINES_BORDER_COLOR': p['modified'],
        'IGNORED_DELETED_LINES_BORDER_COLOR': p['deleted'],
        'ANNOTATIONS_COLOR': p['secondary'], 'ANNOTATIONS_LAST_COMMIT_COLOR': p['fg'],
        'FILESTATUS_ADDED': p['string'], 'FILESTATUS_COPIED': p['string'], 'FILESTATUS_MODIFIED': p['type'],
        'FILESTATUS_NOT_CHANGED_IMMEDIATE': p['type'], 'FILESTATUS_NOT_CHANGED_RECURSIVE': p['type'],
        'FILESTATUS_RENAMED': p['type'], 'FILESTATUS_DELETED': p['secondary'],
        'FILESTATUS_IDEA_FILESTATUS_DELETED_FROM_FILE_SYSTEM': p['secondary'],
        'FILESTATUS_IDEA_FILESTATUS_IGNORED': p['warning'], 'FILESTATUS_UNKNOWN': p['error'],
        'FILESTATUS_MERGED': p['annotation'],
        'FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_CONFLICTS': p['error'],
        'FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_BOTH_CONFLICTS': p['error'],
        'FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_PROPERTY_CONFLICTS': p['error'],
        'FILESTATUS_addedOutside': p['string'], 'FILESTATUS_modifiedOutside': p['type'],
        'FILESTATUS_changelistConflict': p['error'],
        **{f'VCS_ANNOTATIONS_COLOR_{i}': c for i, c in enumerate(p['vcsAge'], 1)},
    }

    def a(fg=None, bg=None, font=None, effect=None, etype=None, stripe=None):
        return dict(FOREGROUND=fg, BACKGROUND=bg, FONT_TYPE=font, EFFECT_COLOR=effect, EFFECT_TYPE=etype,
                    ERROR_STRIPE_COLOR=stripe)
    base = lambda key: ('base', key)
    fg = p['fg']
    attrs = {
        'TEXT': a(fg, p['bg']),
        # language defaults
        'DEFAULT_KEYWORD': a(p['keyword']),
        'DEFAULT_STRING': a(p['string']),
        'DEFAULT_VALID_STRING_ESCAPE': a(p['keyword']),
        'DEFAULT_INVALID_STRING_ESCAPE': a(p['keyword'], effect=p['error'], etype=WAVE),
        'DEFAULT_NUMBER': a(p['number']),
        'DEFAULT_LINE_COMMENT': a(p['comment'], font=ITALIC),
        'DEFAULT_BLOCK_COMMENT': a(p['comment'], font=ITALIC),
        'DEFAULT_DOC_COMMENT': a(p['comment'], font=ITALIC),
        'DEFAULT_DOC_COMMENT_TAG': a(p['docTag'], font=BOLD | ITALIC),
        'DEFAULT_DOC_COMMENT_TAG_VALUE': a(p['docTag'], font=ITALIC),
        'DEFAULT_DOC_MARKUP': a(p['docTag']),
        'DEFAULT_IDENTIFIER': a(fg),
        'DEFAULT_LOCAL_VARIABLE': a(fg),
        'DEFAULT_PARAMETER': a(fg),
        'DEFAULT_REASSIGNED_LOCAL_VARIABLE': a(fg, effect=p['unused'], etype=LINE),
        'DEFAULT_REASSIGNED_PARAMETER': a(fg, effect=p['unused'], etype=LINE),
        'DEFAULT_FUNCTION_DECLARATION': a(p['method']),
        'DEFAULT_FUNCTION_CALL': base('DEFAULT_IDENTIFIER'),
        'DEFAULT_INSTANCE_METHOD': a(fg),
        'DEFAULT_STATIC_METHOD': a(fg, font=ITALIC),
        'DEFAULT_CLASS_NAME': a(p['type']),
        'DEFAULT_CLASS_REFERENCE': a(p['type']),
        'DEFAULT_INTERFACE_NAME': a(p['type']),
        'TYPE_PARAMETER_NAME_ATTRIBUTES': a(p['number']),
        'DEFAULT_METADATA': a(p['annotation']),
        'ANNOTATION_NAME_ATTRIBUTES': base('DEFAULT_METADATA'),
        'DEFAULT_INSTANCE_FIELD': a(p['field']),
        'DEFAULT_STATIC_FIELD': a(p['field'], font=ITALIC),
        'DEFAULT_CONSTANT': a(p['field'], font=ITALIC),
        'IMPLICIT_ANONYMOUS_CLASS_PARAMETER_ATTRIBUTES': a(p['field']),
        'DEFAULT_LABEL': a(p['number']),
        'DEFAULT_PREDEFINED_SYMBOL': a(p['annotation']),
        'DEFAULT_OPERATION_SIGN': a(fg), 'DEFAULT_BRACES': a(fg), 'DEFAULT_BRACKETS': a(fg),
        'DEFAULT_PARENTHS': a(fg), 'DEFAULT_COMMA': a(fg), 'DEFAULT_SEMICOLON': a(fg), 'DEFAULT_DOT': a(fg),
        'DEFAULT_TAG': a(p['keyword']), 'DEFAULT_ATTRIBUTE': a(p['field']), 'DEFAULT_ENTITY': a(p['number']),
        'DEFAULT_TEMPLATE_LANGUAGE_COLOR': a(bg=p['raised']),
        'CUSTOM_KEYWORD1_ATTRIBUTES': a(p['keyword']), 'CUSTOM_KEYWORD2_ATTRIBUTES': a(p['annotation']),
        'CUSTOM_KEYWORD3_ATTRIBUTES': a(p['number']), 'CUSTOM_KEYWORD4_ATTRIBUTES': a(p['method']),
        'CUSTOM_STRING_ATTRIBUTES': base('DEFAULT_STRING'),
        'CUSTOM_VALID_STRING_ESCAPE_ATTRIBUTES': base('DEFAULT_VALID_STRING_ESCAPE'),
        'TEMPLATE_VARIABLE_ATTRIBUTES': a(p['annotation']),
        # markup and data languages
        'XML_TAG': a(p['docTag']), 'XML_TAG_NAME': a(p['keyword']), 'XML_CUSTOM_TAG_NAME': a(p['keyword']),
        'XML_ATTRIBUTE_NAME': a(p['field']), 'XML_ATTRIBUTE_VALUE': base('DEFAULT_STRING'),
        'XML_ENTITY_REFERENCE': a(p['number']), 'XML_PROLOGUE': a(p['comment']),
        'HTML_TAG': a(p['docTag']), 'HTML_TAG_NAME': a(p['keyword']), 'HTML_CUSTOM_TAG_NAME': a(p['keyword']),
        'HTML_ATTRIBUTE_NAME': a(p['field']), 'HTML_ATTRIBUTE_VALUE': base('DEFAULT_STRING'),
        'HTML_ENTITY_REFERENCE': a(p['number']),
        'JSON.PROPERTY_KEY': a(p['field']),
        'YAML_SCALAR_KEY': a(p['field']),
        'PROPERTIES.KEY': a(p['field']), 'PROPERTIES.VALUE': a(p['string']),
        'PROPERTIES.INVALID_STRING_ESCAPE': a(p['error'], effect=p['error'], etype=WAVE),
        'CSS.COLOR': a(p['number']), 'CSS.IMPORTANT': a(p['keyword'], font=BOLD), 'CSS.URL': a(p['type']),
        'JS.GLOBAL_VARIABLE': a(p['field'], font=ITALIC), 'JS.GLOBAL_FUNCTION': base('DEFAULT_FUNCTION_DECLARATION'),
        'JS.INSTANCE_MEMBER_FUNCTION': base('DEFAULT_INSTANCE_METHOD'), 'JS.REGEXP': a(p['number']),
        'JS.JSX_CLIENT_COMPONENT': a(p['type']),
        # Java keys the Darcula parent defines on its own, so the DEFAULT_* fallbacks never reach them
        'INSTANCE_FIELD_ATTRIBUTES': a(p['field']), 'INSTANCE_FINAL_FIELD_ATTRIBUTES': a(p['field']),
        'STATIC_FIELD_ATTRIBUTES': a(p['field'], font=ITALIC), 'STATIC_FINAL_FIELD_ATTRIBUTES': a(p['field'], font=ITALIC),
        'METHOD_DECLARATION_ATTRIBUTES': a(p['method']), 'CONSTRUCTOR_DECLARATION_ATTRIBUTES': a(p['method']),
        'STATIC_METHOD_ATTRIBUTES': a(fg, font=ITALIC),
        'CONSTRUCTOR_CALL_ATTRIBUTES': a(p['type']),
        'KOTLIN_NAMED_ARGUMENT': a(p['number']), 'KOTLIN_LABEL': a(p['number']),
        'KOTLIN_CONTEXT_ARGUMENT': a(p['annotation']), 'KOTLIN_COROUTINE_DEBUGGER_VALUE': a(p['error']),
        'KOTLIN_PROPERTY_WITH_BACKING_FIELD': a(bg=p['selectionMuted']),
        'KOTLIN_TYPE_PARAMETER': base('TYPE_PARAMETER_NAME_ATTRIBUTES'),
        'KOTLIN_MUTABLE_VARIABLE': a(effect=p['unused'], etype=LINE),
        'KOTLIN_SMART_CAST_RECEIVER': a(bg=p['smartCast']), 'KOTLIN_SMART_CAST_VALUE': a(bg=p['smartCast']),
        'KOTLIN_SMART_CONSTANT': a(bg=p['smartCast']),
        'MARKDOWN_HEADER_LEVEL_1': a(p['keyword'], font=BOLD), 'MARKDOWN_HEADER_LEVEL_2': a(p['keyword'], font=BOLD),
        'MARKDOWN_HEADER_LEVEL_3': a(p['keyword'], font=BOLD), 'MARKDOWN_HEADER_LEVEL_4': a(p['keyword'], font=BOLD),
        'MARKDOWN_HEADER_LEVEL_5': a(p['keyword'], font=BOLD), 'MARKDOWN_HEADER_LEVEL_6': a(p['keyword'], font=BOLD),
        'MARKDOWN_CODE_SPAN': a(p['field']), 'MARKDOWN_CODE_BLOCK': a(p['fg']),
        'MARKDOWN_LINK_TEXT': a(p['type'], effect=p['type'], etype=LINE),
        'MARKDOWN_AUTO_LINK': a(p['type'], effect=p['type'], etype=LINE),
        'REGEXP.BRACES': base('DEFAULT_BRACES'), 'REGEXP.BRACKETS': base('DEFAULT_BRACKETS'),
        'REGEXP.PARENTHS': base('DEFAULT_PARENTHS'), 'REGEXP.META': base('DEFAULT_KEYWORD'),
        'REGEXP.ESC_CHARACTER': base('DEFAULT_VALID_STRING_ESCAPE'),
        'REGEXP.QUOTE_CHARACTER': base('DEFAULT_VALID_STRING_ESCAPE'),
        'REGEXP.CHAR_CLASS': a(p['method'], font=BOLD), 'REGEXP.REDUNDANT_ESCAPE': a(p['comment']),
        # problems
        'ERRORS_ATTRIBUTES': a(effect=p['error'], etype=WAVE, stripe=p['error']),
        'WARNING_ATTRIBUTES': a(effect=p['warning'], etype=WAVE, stripe=p['warning']),
        'INFO_ATTRIBUTES': a(effect=p['info'], etype=WAVE),
        'TYPO': a(effect=p['string'], etype=WAVE),
        'TEXT_STYLE_ERROR': a(effect=p['error'], etype=BOLD_DOTTED),
        'TEXT_STYLE_WARNING': a(effect=p['warning'], etype=BOLD_DOTTED),
        'RUNTIME_ERROR': a(effect=p['warning'], etype=BOLD_DOTTED, stripe=p['error']),
        'BAD_CHARACTER': a(p['error'], effect=p['error'], etype=WAVE),
        'WRONG_REFERENCES_ATTRIBUTES': a(p['error']),
        'UNMATCHED_BRACE_ATTRIBUTES': a(p['error']),
        'NOT_USED_ELEMENT_ATTRIBUTES': a(p['unused']),
        'DEPRECATED_ATTRIBUTES': a(effect=fg, etype=STRIKE),
        'MARKED_FOR_REMOVAL_ATTRIBUTES': a(effect=p['error'], etype=STRIKE),
        'TODO_DEFAULT_ATTRIBUTES': a(p['accent'], font=ITALIC, stripe=p['accent']),
        # highlighting
        'IDENTIFIER_UNDER_CARET_ATTRIBUTES': a(bg=p['usage'], stripe=p['usageStripe']),
        'WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES': a(bg=p['usageWrite'], stripe=p['usageWriteStripe']),
        'SEARCH_RESULT_ATTRIBUTES': a(bg=p['search'], stripe=p['searchStripe']),
        'WRITE_SEARCH_RESULT_ATTRIBUTES': a(bg=p['usageWrite'], stripe=p['usageWriteStripe']),
        'TEXT_SEARCH_RESULT_ATTRIBUTES': a(bg=p['textSearch'], stripe=p['searchStripe']),
        'MATCHED_BRACE_ATTRIBUTES': a(bg=p['brace'], font=BOLD),
        'MATCHED_TAG_NAME': a(bg=p['brace']),
        'DEFAULT_HIGHLIGHTED_REFERENCE': a(effect=p['unused'], etype=LINE),
        'HYPERLINK_ATTRIBUTES': a(p['type'], effect=p['type'], etype=LINE),
        'FOLLOWED_HYPERLINK_ATTRIBUTES': a(p['annotation'], effect=p['annotation'], etype=LINE),
        'INACTIVE_HYPERLINK_ATTRIBUTES': a(effect=p['unused'], etype=LINE),
        'CTRL_CLICKABLE': a(p['type'], effect=p['type'], etype=LINE),
        'FOLDED_TEXT_ATTRIBUTES': a(p['docTag'], bg=p['folded']),
        'INJECTED_LANGUAGE_FRAGMENT': a(bg=p['injected']),
        'LIVE_TEMPLATE_ATTRIBUTES': a(effect=p['accent']),
        'BOOKMARKS_ATTRIBUTES': a(stripe=p['method']),
        'BREAKPOINT_ATTRIBUTES': a(bg=p['breakpoint'], stripe=p['error']),
        'EXECUTIONPOINT_ATTRIBUTES': a(bg=p['execution']),
        'INLAY_DEFAULT': a(p['inlayFg'], bg=p['inlayBg']),
        'INLAY_TEXT_WITHOUT_BACKGROUND': a(p['secondary']),
        'INLINE_PARAMETER_HINT': a(p['inlayFg'], bg=p['inlayBg']),
        'INLINE_PARAMETER_HINT_HIGHLIGHTED': a(fg, bg=p['border2']),
        'INLINE_PARAMETER_HINT_CURRENT': a(p['inlayCurFg'], bg=p['inlayCurBg']),
        'BREADCRUMBS_DEFAULT': a(p['muted']), 'BREADCRUMBS_INACTIVE': a(p['unused']),
        'BREADCRUMBS_CURRENT': a(fg, bg=p['border']), 'BREADCRUMBS_HOVERED': a(fg, bg=p['border']),
        'DOC_CODE_BLOCK': a(fg, bg=p['docCode'], effect=p['border']),
        'DOC_CODE_INLINE': a(fg, bg=p['border']),
        'DEBUGGER_INLINED_VALUES': a(p['secondary'], font=ITALIC),
        'DEBUGGER_INLINED_VALUES_EXECUTION_LINE': a(p['type'], font=ITALIC),
        'DEBUGGER_INLINED_VALUES_MODIFIED': a(p['method'], font=ITALIC),
        # console and terminal
        'CONSOLE_NORMAL_OUTPUT': a(fg), 'CONSOLE_ERROR_OUTPUT': a(p['error']),
        'CONSOLE_SYSTEM_OUTPUT': a(p['docTag']), 'CONSOLE_USER_INPUT': a(p['string'], font=ITALIC),
        'CONSOLE_RANGE_TO_EXECUTE': a(effect=p['string']),
        'LOG_ERROR_OUTPUT': a(p['error']), 'LOG_WARNING_OUTPUT': a(p['warning']),
        'LOG_INFO_OUTPUT': a(p['string']), 'LOG_VERBOSE_OUTPUT': a(p['type']),
    }
    for k, v in p['ansi'].items():
        attrs[f'CONSOLE_{k}_OUTPUT'] = a(v)

    lines = [f'<scheme name="{name}" version="142" parent_scheme="{"Darcula" if dark else "Default"}">',
             '  <metaInfo>', '    <property name="ide">idea</property>',
             f'    <property name="originalScheme">{name}</property>', '  </metaInfo>', '  <colors>']
    for k, v in colors.items():
        lines.append(f'    <option name="{k}" value="{h(v)}"/>')
    lines += ['  </colors>', '  <attributes>']
    for k, v in attrs.items():
        if isinstance(v, tuple):
            lines.append(f'    <option name="{k}" baseAttributes="{v[1]}"/>')
            continue
        lines += [f'    <option name="{k}">', '      <value>']
        for opt, val in v.items():
            if val is None:
                continue
            lines.append(f'        <option name="{opt}" value="{val if isinstance(val, int) else h(val)}"/>')
        lines += ['      </value>', '    </option>']
    lines += ['  </attributes>', '</scheme>', '']
    return '\n'.join(lines)

for p, dark in ((DARK, True), (LIGHT, False)):
    slug = 'kiln-' + ('dark' if dark else 'light')
    (OUT / f'{slug}.theme.json').write_text(json.dumps(theme_json(p, dark), indent=2) + '\n')
    (OUT / f'{slug}.xml').write_text(scheme_xml(p, dark))
    print(f'== {slug}: contrast vs editor bg')
    for role in ('fg', 'keyword', 'string', 'number', 'type', 'method', 'annotation', 'field', 'comment', 'docTag', 'unused', 'lineNum', 'muted', 'secondary', 'link'):
        print(f'   {role:11} {p[role]}  {contrast(p[role], p["bg"]):.2f}')
    print(f'   frame vs bg {contrast(p["frame"], p["bg"]):.2f}   white on accentStrong {contrast("#FFFFFF", p["accentStrong"]):.2f}')
