"""Synthetic versioned statute corpus generator.

Produces N statute sections with M versions each. Each transition between
versions has a controlled probability of:
  - unchanged (~50%)
  - cosmetic (whitespace / punctuation only, ~15%)
  - renumbering (section id changes, text identical, ~5%)
  - substantive (real text + meaning change, ~25%)
  - deleted (section disappears, ~3%)
  - added (new section appears, ~2%)

The transitions are deterministic per seed so tests can pin behavior.
For real-data mode, swap `generate_versions` for a USC / CFR loader.
"""

from __future__ import annotations

import random
from dataclasses import replace

from ..types import Section

# templated section text
_TEMPLATES = {
    "criminal_liability": (
        "Any person who, under color of any statute, ordinance, regulation, "
        "custom, or usage, of any State or Territory or the District of Columbia, "
        "subjects, or causes to be subjected, any citizen of the United States to "
        "the deprivation of any rights, privileges, or immunities secured by the "
        "Constitution and laws, shall be liable to the party injured in an action "
        "at law, suit in equity, or other proper proceeding for redress."
    ),
    "tax_credit": (
        "There shall be allowed as a credit against the tax imposed by this chapter "
        "for the taxable year an amount equal to {pct} percent of the qualified "
        "expenses paid or incurred by the taxpayer during such taxable year, "
        "not to exceed {cap} dollars."
    ),
    "agency_authority": (
        "The Administrator may, by rule promulgated in accordance with section 553 of "
        "title 5, United States Code, prescribe such regulations as may be necessary "
        "or appropriate to carry out the purposes of this section. Such regulations "
        "shall take effect not earlier than {days} days after publication in the "
        "Federal Register."
    ),
    "definition": (
        "For purposes of this section, the term '{term}' means {definition}. "
        "Such term does not include {exclusion}."
    ),
    "penalty": (
        "Any person who violates this section shall be subject to a civil penalty of "
        "not more than ${amount} for each violation. Each day on which a violation "
        "continues constitutes a separate violation."
    ),
}


def _fill(template_key: str, seed: int) -> str:
    rng = random.Random(seed)
    if template_key == "tax_credit":
        return _TEMPLATES[template_key].format(
            pct=rng.choice([10, 15, 20, 25, 30]),
            cap=rng.choice([1000, 2500, 5000, 10000]),
        )
    if template_key == "agency_authority":
        return _TEMPLATES[template_key].format(days=rng.choice([30, 60, 90, 180]))
    if template_key == "definition":
        terms = [
            ("qualified taxpayer", "an individual filing a Form 1040", "trusts and estates"),
            ("eligible business", "a corporation organized under State law", "foreign entities"),
            (
                "covered employer",
                "an employer with more than 50 employees",
                "religious organizations",
            ),
        ]
        t, d, x = rng.choice(terms)
        return _TEMPLATES[template_key].format(term=t, definition=d, exclusion=x)
    if template_key == "penalty":
        return _TEMPLATES[template_key].format(amount=rng.choice([500, 1000, 5000, 10000, 25000]))
    return _TEMPLATES[template_key]


def _cosmetic_edit(text: str, seed: int) -> str:
    rng = random.Random(seed)
    # add whitespace, swap punctuation, slight reformatting
    out = text
    if rng.random() < 0.5:
        out = out.replace("United States", "the United States")
    if rng.random() < 0.5:
        out = out.replace("section", "Section")
    if rng.random() < 0.3:
        out = out.replace(", ", ",  ")  # double space
    return out


def _substantive_edit(text: str, template_key: str, seed: int) -> str:
    # regenerate with a different seed = different numbers/terms
    return _fill(template_key, seed=seed * 7919)


def generate_versions(
    n_sections: int = 30,
    n_versions: int = 3,
    seed: int = 7,
) -> list[list[Section]]:
    """Return [list[Section] per version]. All versions share the same
    statute_id set; section_ids may renumber across versions.
    """
    rng = random.Random(seed)
    template_keys = list(_TEMPLATES.keys())
    # build version 0
    v0: list[Section] = []
    for i in range(n_sections):
        tk = rng.choice(template_keys)
        v0.append(
            Section(
                statute_id="USC.42",
                section_id=f"{1000 + i}",
                version="2022-01-01",
                text=_fill(tk, seed=i),
                title=tk.replace("_", " ").title(),
            )
        )
    versions = [v0]

    for v_idx in range(1, n_versions):
        prev = versions[-1]
        new_version = f"202{v_idx + 2}-01-01"
        new_sections: list[Section] = []
        for sec in prev:
            roll = rng.random()
            # find the template by title
            tk = sec.title.lower().replace(" ", "_") if sec.title else "definition"
            if roll < 0.50:
                new_sections.append(replace(sec, version=new_version))
            elif roll < 0.65:
                new_sections.append(
                    replace(
                        sec,
                        version=new_version,
                        text=_cosmetic_edit(sec.text, seed=hash((sec.section_id, v_idx))),
                    )
                )
            elif roll < 0.70:
                # renumbering: same text, new section_id
                new_id = f"{int(sec.section_id) + 5000}"
                new_sections.append(replace(sec, version=new_version, section_id=new_id))
            elif roll < 0.95:
                # substantive change
                new_sections.append(
                    replace(
                        sec,
                        version=new_version,
                        text=_substantive_edit(sec.text, tk, seed=hash((sec.section_id, v_idx))),
                    )
                )
            elif roll < 0.97:
                # deleted - skip
                continue
            else:
                # added - keep existing AND add a new one
                new_sections.append(replace(sec, version=new_version))
                tk2 = rng.choice(template_keys)
                new_sections.append(
                    Section(
                        statute_id="USC.42",
                        section_id=f"{9000 + len(new_sections)}",
                        version=new_version,
                        text=_fill(tk2, seed=hash((sec.section_id, v_idx, "new"))),
                        title=tk2.replace("_", " ").title(),
                    )
                )
        # also possibly add a brand-new section
        if rng.random() < 0.10:
            tk = rng.choice(template_keys)
            new_sections.append(
                Section(
                    statute_id="USC.42",
                    section_id=f"{9500 + v_idx}",
                    version=new_version,
                    text=_fill(tk, seed=v_idx * 13),
                    title=tk.replace("_", " ").title(),
                )
            )
        versions.append(new_sections)
    return versions
