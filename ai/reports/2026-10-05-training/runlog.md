# Run log (training)

- 12:27:13 `PYTHONPATH=src python -m training.phase0` (0s): 0 problem(s), 12 shortcut flag(s)
- 12:27:48 `PYTHONPATH=src python -m training.phase0` (0s): 0 problem(s), 12 shortcut flag(s)
- 12:39:44 `PYTHONPATH=src python -m training.track_b` (seed 0, 147s): chosen grown, verdict reject
- (about 12:35-12:46) `PYTHONPATH=src python -m training.track_b --retry` (seed 0): chosen capped_10_casual, adopt with caveats. The run stopped at the CSV step on a writer bug, after writing track_b_retry.json and the bundle; the CSV was then written from that JSON with the fixed writer
- 12:47:21 control: current examples + 40 casual honest texts only: dev recall 71.7%, real SMS false alarms 9.6%
- 12:52:40 `PYTHONPATH=src python -m training.track_a` (seeds 0-3, 275s): verdict reject
- 12:53:37 `PYTHONPATH=src python -m training.track_c` (seed 0, 337s): C=10.0, weight 0.3, verdict reject
- 13:00:09 `PYTHONPATH=src python -m training.final_test similarity_v3` (test sha256 6fc6fd2858a5bb33..., 39s): ONE-TIME test result written
