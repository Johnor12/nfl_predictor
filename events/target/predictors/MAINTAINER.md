# MAINTAINER

- __init__.py: `DEFAULT`, the implementation the system uses unless another is named.
- baseline/: the baseline predictor (see its MAINTAINER.md).
- gbm/: the trained air yards model on top of the baseline (see its MAINTAINER.md).
- gbm_receiver/: a trained receiver choice on top of `gbm` (see its MAINTAINER.md). Not the default.

To add an implementation, add a package here that exports `predict`.
