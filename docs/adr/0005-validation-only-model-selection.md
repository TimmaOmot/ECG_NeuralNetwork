# Validation-only V1 model selection

The participant-grouped validation partition will select preprocessing candidates, class weighting, the binary threshold, and a narrow shallow-CNN search by macro F1. The test partition will remain untouched until these choices are frozen; normalization parameters are fitted only on training data and then applied unchanged outside it. Each selected configuration will use three fixed training seeds and report record-aware uncertainty plus per-record results; each seed's best validation checkpoint is evaluated directly on test.
