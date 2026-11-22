"""What the phone editor shows while it is loading, in a real browser set up as a phone:
"Loading editor..." until the editor is ready, the button only after that, and the background
pictures being fetched ahead.

Several tests here hold back something the page asks for, the way a slow connection would,
and let it through later.
"""
from browser_fixtures import COMMON_PHONE, finger_swipe, sideways
from phone_editor_helpers import expect, preview_point, shown_screen, widgets_on_preview

PHONE = sideways(COMMON_PHONE)

# Run in the page before anything else: every request for full screen is refused.
A_BROWSER_THAT_REFUSES_FULL_SCREEN = (
    "Element.prototype.requestFullscreen = () => Promise.reject(new Error('full screen was refused'));"
)


class HeldBack:
    """Holds back every request whose address matches a pattern, until let_through() is called."""

    def __init__(self, pattern: str):
        self._pattern = pattern
        self._waiting = []

    def prepare(self, page) -> None:
        page.route(self._pattern, lambda route: self._waiting.append(route))

    def is_waiting(self) -> bool:
        return len(self._waiting) > 0

    def let_through(self) -> None:
        for route in self._waiting:
            route.continue_()
        self._waiting.clear()


def start_screen(page):
    return page.locator("#start-screen")


def editing_screen(page):
    return page.locator("#editing-screen")


def loading_line(page):
    return page.locator("#start-loading")


def open_button(page):
    return page.locator("#open-editor-button")


def expect_still_loading(page) -> None:
    expect(start_screen(page)).to_have_attribute("data-state", "loading")
    expect(loading_line(page)).to_be_visible()
    expect(loading_line(page)).to_contain_text("Loading editor")
    expect(open_button(page)).to_be_hidden()                       # no button that would do nothing
    expect(editing_screen(page)).to_be_hidden()


def expect_ready(page) -> None:
    expect(start_screen(page)).to_have_attribute("data-state", "ready")
    expect(open_button(page)).to_be_visible()
    expect(loading_line(page)).to_be_hidden()


# --- Until the editor is ready ---------------------------------------------------------------------------

def test_the_button_is_not_shown_before_the_editors_code_has_arrived(open_page):
    code = HeldBack("**/js/editor_phone/phone_editor_main.js")     # the editor's code is slow to arrive
    editor = open_page("/editor", PHONE, as_phone=True, prepare=code.prepare, wait_until="commit")
    editor.wait_for_selector("#start-screen")
    assert code.is_waiting()
    expect_still_loading(editor)

    code.let_through()
    expect_ready(editor)


def test_the_button_is_not_shown_before_the_layout_has_arrived(open_page):
    layout = HeldBack("**/api/layout")                             # the layout is slow to arrive
    editor = open_page("/editor", PHONE, as_phone=True, prepare=layout.prepare)
    editor.wait_for_function("document.querySelector('#panel') !== null")
    editor.wait_for_timeout(300)
    expect_still_loading(editor)

    layout.let_through()
    expect_ready(editor)


def test_the_button_is_not_shown_before_the_pictures_have_arrived(open_page):
    pictures = HeldBack("**/static/backgrounds/*.jpg")             # the pictures are slow to arrive
    editor = open_page("/editor", PHONE, as_phone=True, prepare=pictures.prepare, wait_until="commit")
    editor.wait_for_selector("#start-screen")
    editor.wait_for_timeout(600)
    expect_still_loading(editor)

    pictures.let_through()
    expect_ready(editor)


def test_when_the_editor_cannot_load_the_start_screen_says_so(open_page):
    def prepare(page):
        page.route("**/api/layout", lambda route: route.abort())  # the server cannot be reached

    editor = open_page("/editor", PHONE, as_phone=True, prepare=prepare)
    expect(start_screen(editor)).to_have_attribute("data-state", "failed")
    expect(editor.locator("#start-failed")).to_be_visible()
    expect(editor.locator("#start-failed")).to_contain_text("could not load")
    expect(open_button(editor)).to_be_hidden()
    expect(loading_line(editor)).to_be_hidden()
    expect(editor.locator(".start__home")).to_be_visible()         # the way back is still there


# --- Once it is ready ---------------------------------------------------------------------------------------

def test_once_ready_a_tap_opens_the_editor_at_once(open_page):
    editor = open_page("/editor", PHONE, as_phone=True)
    expect_ready(editor)

    open_button(editor).tap()
    expect(editing_screen(editor)).to_be_visible()
    expect(start_screen(editor)).to_be_hidden()
    expect(widgets_on_preview(editor)).to_have_count(4)            # already drawn: nothing was left to wait for
    assert editor.evaluate("document.fullscreenElement !== null")


def test_two_quick_taps_open_the_editor_once(open_page):
    editor = open_page("/editor", PHONE, as_phone=True)
    expect_ready(editor)
    editor.evaluate("() => { const button = document.getElementById('open-editor-button'); button.click(); button.click(); }")

    expect(editing_screen(editor)).to_be_visible()
    expect(start_screen(editor)).to_be_hidden()


def test_leaving_full_screen_brings_back_the_button_not_the_loading_line(open_page):
    editor = open_page("/editor", PHONE, as_phone=True)
    expect_ready(editor)
    open_button(editor).tap()
    expect(editing_screen(editor)).to_be_visible()

    editor.evaluate("document.exitFullscreen()")
    expect_ready(editor)


def test_a_browser_that_refuses_full_screen_still_opens_the_editor(open_page):
    # A browser that says no to full screen (rare), or cannot do it at all (an iPhone's): the
    # editor opens anyway, under the browser's bars.
    def prepare(page):
        page.add_init_script(A_BROWSER_THAT_REFUSES_FULL_SCREEN)

    editor = open_page("/editor", PHONE, as_phone=True, prepare=prepare)
    expect_ready(editor)
    open_button(editor).tap()
    expect(editing_screen(editor)).to_be_visible()


# --- The background pictures ------------------------------------------------------------------------------------

def watch_the_backgrounds(asked_for: list):
    def prepare(page):
        page.on("request", lambda request: asked_for.append(request.url.rsplit("/", 1)[-1])
                if "/static/backgrounds/" in request.url else None)
    return prepare


def test_every_background_is_fetched_before_the_editor_is_opened(open_page):
    asked_for = []
    editor = open_page("/editor", PHONE, as_phone=True, prepare=watch_the_backgrounds(asked_for))
    editor.wait_for_selector("body[data-ready]")                   # ready; "Open the editor" not tapped yet

    assert sorted(set(asked_for)) == [
        "calm-sea.jpg", "forest.jpg", "lavender.jpg", "morning-mist.jpg", "night-sky.jpg", "soft-hills.jpg",
    ]


def test_moving_between_screens_and_choosing_a_background_needs_nothing_from_the_server(open_page, server):
    editor = open_page("/editor", PHONE, as_phone=True)
    editor.wait_for_selector("body[data-ready]")
    editor.locator("#open-editor-button").tap()
    expect(editing_screen(editor)).to_be_visible()

    server.stop()                                                  # from here on, nothing can be fetched

    finger_swipe(editor, preview_point(editor, 0.7, 0.4), preview_point(editor, 0.3, 0.4))   # to the second screen
    expect(shown_screen(editor)).to_have_attribute("data-screen", "1")
    editor.locator("#backgrounds-button").tap()                    # six swatches, six pictures
    expect(editor.locator(".swatch")).to_have_count(6)
    editor.locator('.swatch[data-background-id="forest"]').tap()

    # Every background can still be drawn: the browser has them all, and asks nobody.
    pictures_the_browser_has = editor.evaluate("""async () => {
        const addresses = [...document.querySelectorAll('.swatch')]
            .map((swatch) => swatch.style.backgroundImage.slice(5, -2));
        const arrived = await Promise.all(addresses.map((address) => new Promise((done) => {
            const picture = new Image();
            picture.onload = () => done(picture.naturalWidth);
            picture.onerror = () => done(0);
            picture.src = address;
        })));
        return arrived;
    }""")
    assert pictures_the_browser_has == [480] * 6
    assert "forest.jpg" in editor.locator(".preview .display").evaluate("element => element.style.backgroundImage")
