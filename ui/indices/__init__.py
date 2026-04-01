import streamlit as st

from .section import render_indices_section as _render_indices_section
from . import section as _section

__all__ = ["render_indices_section", "st"]


def render_indices_section(*args, **kwargs):
    _section.st = st
    return _render_indices_section(*args, **kwargs)
