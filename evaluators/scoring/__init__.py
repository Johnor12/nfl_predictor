# START
# scoring: the evaluators' shared toolkit (see README.md).
# - Scores for an ensemble of samples: fair_crps, fair_brier, score, kind_of; the reference: climatology.
# - Scores for a stated probability: brier, log_loss; probability (a smoothed one from samples).
# - Diagnostics: pit, histogram, reliability.
# - Scorecard: scores many cases by output name; rows(), pit(name), reliability(name), merge(other).
# - Reports: OUT, GUIDE, score_table, pit_table, reliability_table.
# END
from evaluators.scoring.report import GUIDE, OUT, pit_table, reliability_table, score_table
from evaluators.scoring.scorecard import Scorecard
from evaluators.scoring.scores import (brier, climatology, fair_brier, fair_crps, histogram, kind_of, log_loss, pit,
                                       probability, reliability, score)

__all__ = [
    "fair_crps", "fair_brier", "score", "kind_of", "climatology", "brier", "log_loss", "probability",
    "pit", "histogram", "reliability", "Scorecard", "OUT", "GUIDE", "score_table", "pit_table", "reliability_table",
]
