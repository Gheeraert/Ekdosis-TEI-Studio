"""Simple dialogs used by the Tkinter UI."""

from .about_dialog import show_about_dialog
from .annotation_dialog import open_annotation_dialog
from .config_dialog import open_config_dialog
from .dramatic_merge_dialog import open_dramatic_merge_dialog
from .help_dialog import show_help_dialog
from .publication_dialog import open_publication_dialog
from .search_dialog import SearchReplaceDialog
from .text_transcription_merge_dialog import open_text_transcription_merge_dialog

__all__ = [
    "show_about_dialog",
    "show_help_dialog",
    "open_config_dialog",
    "open_annotation_dialog",
    "open_dramatic_merge_dialog",
    "open_text_transcription_merge_dialog",
    "open_publication_dialog",
    "SearchReplaceDialog",
]
