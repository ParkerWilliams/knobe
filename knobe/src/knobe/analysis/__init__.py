"""S8: behavioral statistical analysis pipeline (master spec §6; WO-8).

Modules:
  * ``ingest``   -- stream-join results + release vignettes + curated ratings
                    into one analysis DataFrame; never-silent exclusions ledger.
  * ``models``   -- the RQ1 primary LMMs + the contrasts.yaml governance
                    mechanism (LMM-primary / ordinal-sensitivity, documented).
  * ``figstyle`` -- the single figure-styling module (Agg backend, palette).
  * ``figures``  -- descriptive distributions, item caterpillars, model panels.
  * ``report``   -- paper-artifact emission + the ingest->models->figures->report
                    orchestrator (``knobe analyze`` / ``make paper``).
"""
