"""Which editor a browser gets at /editor: the desktop editor or the phone editor.

The two editors are separate pages. Both live at the same address, and the server chooses.

It chooses from the label every browser sends with a request (the "User-Agent"), which says
what kind of browser it is. Browsers on phones put the word "Mobi" in that label; browsers on
desktops and on tablets do not. So a tablet, with its large screen, gets the desktop editor.

The label is occasionally wrong, and the phone editor is worth showing on a laptop. So the
address also takes the choice by hand:  /editor?view=phone  and  /editor?view=desktop.
"""
from __future__ import annotations

from typing import Optional

DESKTOP_EDITOR_PAGE = "editor.html"
PHONE_EDITOR_PAGE = "editor_phone.html"

# What may follow "view=" in the address, and the page each one asks for.
PAGE_FOR_CHOSEN_VIEW = {"desktop": DESKTOP_EDITOR_PAGE, "phone": PHONE_EDITOR_PAGE}

# The word that phone browsers put in their label.
MARK_OF_A_PHONE = "Mobi"


def is_a_phone(browser_label: Optional[str]) -> bool:
    """Does this label belong to a browser on a phone?"""
    return MARK_OF_A_PHONE in (browser_label or "")


def editor_page_for(browser_label: Optional[str], chosen_view: Optional[str] = None) -> str:
    """The file name of the editor page to send.

    browser_label: the browser's label (its User-Agent), or None if it sent none.
    chosen_view:   what the address said after "view=", or None. Anything other than "phone"
                   or "desktop" is ignored.
    """
    if chosen_view in PAGE_FOR_CHOSEN_VIEW:
        return PAGE_FOR_CHOSEN_VIEW[chosen_view]
    return PHONE_EDITOR_PAGE if is_a_phone(browser_label) else DESKTOP_EDITOR_PAGE
