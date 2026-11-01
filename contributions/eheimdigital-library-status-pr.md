Expose professionel5e error status and estimated flow and power through
`error_code`, `estimated_flow_rate` and `estimated_power`.

Decode errors independently of mode and calibration bits. Return an unknown
error for unrecognized codes. Flow is always expressed in l/h. Power follows
the estimate in the manufacturer's 1.03.2 web interface and returns `None`
when the curve is undefined. Register the new properties in `packet_mapping`.

Tests cover packet updates, missing data, stopped pumps, display units and
error bits. Update the existing hub test to use the keyword-only, async API.

Validation: 39 tests pass. Strict Mypy passes for both modified source modules.
1,629 power estimates match the independently executed manufacturer formula.
The new properties were also read from a professionel 5e 350 without changing
device settings.
