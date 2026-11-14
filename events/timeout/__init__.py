# START
# The timeout event: whether a team calls a timeout before the next play (see README.md).
# - Predictor: predict(ctx, rng) -> str | None, the team calling a timeout, or None. ctx is the next play's
#   PlayContext as it stands before the snap.
# The output is a team name or None, so there is no output type.
# END
