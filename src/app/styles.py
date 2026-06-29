"""Reusable Streamlit CSS snippets."""


def build_sidebar_style_overrides() -> str:
    """Return sidebar CSS that keeps interactive controls readable on dark chrome."""
    return """
        [data-testid="stSidebar"] div[data-testid="stButton"] {
            margin-bottom: .55rem;
        }
        [data-testid="stSidebar"] div[data-testid="stButton"] button {
            width: 100%;
            min-height: 2.55rem;
            padding: .55rem .72rem;
            border: 1px solid rgba(255, 255, 255, .20);
            border-radius: 10px;
            background: rgba(255, 255, 255, .10);
            color: #f4fffb;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, .12);
            text-align: left;
            white-space: normal;
            transition: all .16s ease;
        }
        [data-testid="stSidebar"] div[data-testid="stButton"] button * {
            color: #f4fffb !important;
            white-space: normal;
        }
        [data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            border-color: rgba(118, 218, 168, .58);
            background: rgba(118, 218, 168, .20);
            transform: translateY(-1px);
        }
        [data-testid="stSidebar"] div[data-testid="stButton"] button:focus {
            outline: 2px solid rgba(118, 218, 168, .55);
            outline-offset: 2px;
        }
    """

def build_global_layout_overrides() -> str:
    """Return CSS that keeps page titles clear of the Streamlit toolbar."""
    return """
        .block-container {
            padding-top: 2.75rem;
            max-width: 1420px;
        }
        @media (max-width: 760px) {
            .block-container {
                padding-top: 2.35rem;
            }
        }
    """
