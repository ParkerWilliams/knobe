# Severity and Moralization: Background for the RQ1a Confound (2026-08-10)

**Status:** theory/context note motivating the severity-vs-moral-label
analysis in `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` §1 and
`analysis/rq1_v1_1_robustness/17_severity_vs_label.py`, and the planned
escalated-severity pilot (`docs/SEVERITY_PILOT_PLAN.md`). Not a literature
review in the formal sense — a working synthesis of the psychological
literature most relevant to one specific question: **is severity a nuisance
confound sitting on top of an independently-manipulable "moral" dimension,
or is severity partly constitutive of what makes something read as moral in
the first place?** The answer bears directly on whether "severity-matched
moral/nonmoral vignettes" is an achievable stimulus-engineering goal or is
fighting something closer to a conceptual necessity.

## 1. The empirical starting point

Within this project's v1.1 stimulus set, reviewer-rated severity correlates
with sign (bad vs. good) at **r=.885 within moral items** (MB vs. MG) and
**r=.473 within nonmoral items** (NMB vs. NMG) — see
`analysis/rq1_v1_1_robustness/16_valence_split_severity_covariate.py`.
Nonmoral-bad severity never exceeds 4/10 anywhere in the release (mean 1.6);
moral-bad averages 7.0/10. The curation team's own flagged-variable analysis
(`data/curation/FLAGGED_VARIABLES_README.md`) independently found that
20–26% of nonmoral items in domains with real-world stakes (Healthcare,
Finance, Environment, Data Privacy, Product Safety) get reviewer-judged as
moral anyway, concentrated in exactly the families whose "nonmoral" outcome
still connects to the domain's real stakes. Two independent measurements
(the severity/sign correlation, and the moral-relevance miscategorization
rate) point the same direction: **severity and moral categorization are
entangled in this stimulus set, not merely accidentally correlated.**

## 2. Why this project's own taxonomy makes that entanglement likely, not incidental

`src/knobe/constants.py`'s `GENERATION_SYSTEM_PROMPT` defines the categories
explicitly:

> MB (morally bad): worsens welfare/rights/fairness/obligation/public
> good, independent of the agent's attitude, no evaluative adjectives.
> Use genuine harm, a rights violation, a broken obligation, or
> public-good damage — **NOT a loyalty betrayal, disrespect of
> authority, or purity/disgust violation** (these don't reliably
> satisfy the tests here, even though they feel morally loaded).

This is a **harm/welfare-based definition of moral badness**, and it
explicitly *excludes* the other candidate moral foundations (loyalty,
authority, purity) that a broader taxonomy — Moral Foundations Theory
(Haidt, 2001, 2012; Graham et al., 2013) — would treat as independently
moral. MFT's whole point is that morality is *not* reducible to harm: a
purity violation (e.g., a taboo act with no victim) or a loyalty betrayal
can register as highly "moral" to human judges while causing zero
measurable welfare loss — which would, in principle, let you build
high-moral, low-severity items. **This project deliberately doesn't use
that route.** By construction, "moral" here means "affects
welfare/rights/fairness," and severity is a direct measure of "how much
welfare is affected." Asking whether these two are independently
manipulable is close to asking whether "affects welfare" and "how much
welfare is affected" are independent — which is a much narrower ask than
"is moral judgment separable from consequences in general" (where the MFT
literature says yes, via purity/loyalty/authority) but a much harder one
given the specific, harm-based operationalization chosen here.

This isn't a criticism of the taxonomy's design — the harm-based
definition was almost certainly chosen because it's the most tractable,
least culturally-variable, most LLM-legible notion of "moral," and it
matches the classical developmental-psychology criterion for the
moral/conventional distinction (below). It does mean the RQ1a question
should be understood as "does the *categorical label* matter beyond the
*continuous harm signal* the label is largely defined by," not "is morality
in general separable from consequences."

## 3. The moral/conventional distinction and moralization literature

**Turiel's moral/conventional distinction** (Turiel, 1983; Smetana, 1981)
is the classical developmental-psychology finding this project's taxonomy
most closely tracks: children and adults distinguish *moral* rules (about
harm, welfare, justice, rights — judged wrong independent of authority,
generalizable across contexts) from *conventional* rules (arbitrary,
authority-dependent, changeable — e.g. dress codes, table manners). The
diagnostic criterion Turiel uses to sort an act into the moral bucket **is
harm/welfare impact**, essentially the same criterion this project's MB/NMB
distinction uses. On this account, severity isn't an external confound on
moral categorization — it's close to the sorting criterion itself.

**Rozin's moralization research** (Rozin, 1999, *Psychological Science*;
Rozin, Markwith & Stoess, 1997, on the moralization of vegetarianism) adds
the dynamic piece: attitudes and behaviors can *become* moralized over time
as their perceived consequences become more salient or severe, moving from
"mere preference" to "moral matter" — smoking is Rozin's paradigm case,
moralized as secondhand-smoke harm evidence accumulated. The mechanism
Rozin proposes is essentially: **rising perceived harm pulls a
previously-nonmoral matter across the moral/conventional line.** Applied
here: if you write a nonmoral vignette and then escalate its severity, you
are running exactly the process Rozin describes, and the plausible
prediction — independent of anything about LLM training — is that the item
starts reading as moral rather than staying nonmoral-but-severe.

**Gray, Young & Waytz's Theory of Dyadic Morality** (Gray, Young & Waytz,
2012, *Psychological Inquiry*; Schein & Gray, 2018, *Personality and Social
Psychology Review*) goes further and treats **perceived harm as graded and
central to moral cognition itself**, not a separate factor that modulates an
independent "moral" judgment: on this account, an agent-patient-damage
template is the perceptual core of moral judgment, and its intensity (how
much damage, how vulnerable the patient) *is* the moral judgment's
intensity. If TDM is right, "does severity predict the effect as well as
the moral label" isn't even the right framing — severity *is* most of what
the moral label is tracking, mechanically, not just empirically in this
particular stimulus set.

**A contrasting data point worth naming, not glossing over:** Haidt's
moral-dumbfounding studies (Haidt, Bjorklund & Murphy, 2000; the harmless
taboo-violation vignettes) show people *can* register strong moral
disapproval for acts with no discernible harm (e.g., consensual, private,
victimless taboo violations) — direct evidence that harm/severity is not
strictly *necessary* for something to register as moral, at least for
purity-type content. This is exactly the class of content this project's
generation prompt excludes from "moral" by fiat ("NOT a loyalty betrayal,
disrespect of authority, or purity/disgust violation"). So the broader
literature doesn't say severity and moral status are *always* inseparable —
it says they're inseparable *for the harm/welfare-based subset of morality
this project uses*, which is a real and durable constraint, not an
artifact to be engineered away with better vignette-writing.

## 4. What this predicts for the escalated-severity pilot

Putting 1–3 together, the falsifiable prediction for the planned pilot
(`docs/SEVERITY_PILOT_PLAN.md`) is specific, not just "expect trouble":

- **Procedural/aesthetic subdomains** should hit a moral-relevance ceiling
  at low-to-moderate severity — these subdomains are closest to Turiel's
  "conventional" pole (arbitrary, authority/context-dependent norms), so
  raising their stakes should push them across the moral/conventional line
  fairly quickly, consistent with Rozin's moralization mechanism.
- **Prudential subdomain** (bad outcomes for the *agent's own* interests,
  no other party's welfare/rights engaged) is the best candidate for
  resisting moralization at higher severity, because Turiel's and TDM's
  harm criterion is specifically about harm *to another*, not
  self-regarding costs — a severe but purely self-inflicted prudential
  disaster has nowhere near the same "victim" structure TDM's dyadic
  template requires. This is the concrete, falsifiable version of "prudential
  is the best shot," not just a guess.
- If moral-relevance tracks severity closely even within prudential, that's
  evidence for the strong TDM reading (severity *is* the moral signal, full
  stop, regardless of self- vs. other-directed harm) — a genuinely
  interesting finding in its own right, not just a null result for the
  pilot.

## References (working list, not verified against original pagination — treat as pointers, not citations of record)

- Turiel, E. (1983). *The Development of Social Knowledge: Morality and
  Convention.* Cambridge University Press.
- Smetana, J. G. (1981). Preschool children's conceptions of moral and
  social rules. *Child Development*, 52(4), 1333–1336.
- Rozin, P. (1999). The process of moralization. *Psychological Science*,
  10(3), 218–221.
- Rozin, P., Markwith, M., & Stoess, C. (1997). Moralization and becoming a
  vegetarian: The transformation of preferences into values and the
  recruitment of disgust. *Psychological Science*, 8(2), 67–73.
- Gray, K., Young, L., & Waytz, A. (2012). Mind perception is the essence
  of morality. *Psychological Inquiry*, 23(2), 101–124.
- Schein, C., & Gray, K. (2018). The theory of dyadic morality: Reinventing
  moral judgment by redefining harm. *Personality and Social Psychology
  Review*, 22(1), 32–70.
- Haidt, J. (2001). The emotional dog and its rational tail: A social
  intuitionist approach to moral judgment. *Psychological Review*, 108(4),
  814–834.
- Haidt, J., Bjorklund, F., & Murphy, S. (2000). Moral dumbfounding: When
  intuition finds no reason. Unpublished manuscript.
- Graham, J., Haidt, J., Koleva, S., Motyl, M., Iyer, R., Wojcik, S. P., &
  Ditto, P. H. (2013). Moral foundations theory: The pragmatic validity of
  moral pluralism. *Advances in Experimental Social Psychology*, 47, 55–130.

This project's own related citation, `Raimondi et al. (arXiv:2510.12229)`
and the Ngo et al. typicality/evocativeness mechanism work already anchor
the intentionality-side literature (`knobe/README.md`); the above is
specifically the moral-categorization side, which hadn't been connected to
the codebase's own severity confound finding until this note.
