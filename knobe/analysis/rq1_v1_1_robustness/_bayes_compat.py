"""Import this before `pymc`/`bambi` (which pulls in `arviz`, which
unconditionally imports `arviz_plots` for a cosmetic once-a-day
FutureWarning). `arviz_plots` 0.7/0.8 assumes `matplotlib.style.core` exists
as a submodule; it doesn't in this project's matplotlib (3.11+) -- the thing
arviz_plots actually wants, `USER_LIBRARY_PATHS`, already lives directly on
`matplotlib.style`. Aliasing `core` to the module itself resolves that
attribute lookup harmlessly, without pinning any dependency version (a
matplotlib downgrade was tried instead and broke 26 existing tests via an
unrelated pyparsing-deprecation-as-error interaction -- worse than this).
"""
import matplotlib.style

if not hasattr(matplotlib.style, "core"):
    matplotlib.style.core = matplotlib.style
