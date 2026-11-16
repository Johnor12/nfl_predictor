# MAINTAINER

- __init__.py: `DEFAULT`, the implementation the system uses unless another is named.
- baseline/: the baseline predictor (see its MAINTAINER.md).
- gbm/: the trained run and catch yards models on top of the baseline (see its MAINTAINER.md).

To add an implementation, add a package here that exports `predict`.
