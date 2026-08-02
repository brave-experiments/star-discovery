from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bs4.element import AttributeValueList as BSAttributeValueList
    from bs4.element import NavigableString as BSString
    from bs4.element import Tag as BSTag


def tag_name(elm: BSTag) -> str:
    if elm.namespace:
        return f"{elm.namespace}:{elm.name}"
    return elm.name


def unexpected_elm_error(elm: Any, index: None | int = 0) -> ValueError:
    return ValueError(
        f"Unexpected node: [{str(elm)}] (index: {index})\n"
        + f"Parent node is: [{str(elm.parent)}]"
    )
