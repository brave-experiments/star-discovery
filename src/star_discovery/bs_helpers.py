from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    from bs4.element import Tag

MINIMUM_TITLE_LEN = 5


def html_desc(html: BeautifulSoup, additional_desc: str | None = None) -> str:
    # See if we can get a title out of the beautiful soup file
    desc: str = ""
    if title_tag := html.find("title"):
        title_text = title_tag.get_text().strip()
        if len(title_text) >= MINIMUM_TITLE_LEN:
            desc = title_text

    if additional_desc:
        desc += " - " + additional_desc
    return desc


def unrecovered_attr_name(attr_name: str) -> str:
    return f"-@sd-{attr_name}"


def tag_name(elm: Tag) -> str:
    if elm.namespace:
        return f"{elm.namespace}:{elm.name}"
    return elm.name


def unexpected_elm_error(elm: Any, index: None | int = 0) -> ValueError:
    return ValueError(
        f"Unexpected node: [{str(elm)}] (index: {index})\n"
        + f"Parent node is: [{str(elm.parent)}]"
    )
