# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ChatbotLab'
copyright = '2026, Salvatore Giorgi, Lyle H. Ungar'
author = 'Salvatore Giorgi'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",     # Google/NumPy style docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",  # adds .nojekyll (+ CNAME if html_baseurl is set)
    "myst_parser",             # Markdown support
    "sphinxcontrib.mermaid",
    # "sphinx.ext.intersphinx",# optional cross‑project links
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

autosummary_generate = True
html_theme = "furo"
html_static_path = ["_static"]

html_baseurl = "https://sjgiorgi.github.io/chatlab/"

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "globaltoc_collapse": False,
    "globaltoc_maxdepth": 2,
}
