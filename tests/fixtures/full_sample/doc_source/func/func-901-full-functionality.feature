# Fully authored fixture (R12 check 3): every Functionality header key.
# =============================================================================
# LIVING DOC — FUNC-901 · Full Page - Fully Authored Functionality
# =============================================================================
# source:    https://github.com/AbsaOSS/living-doc-collector-gh/issues/9011
# status:    active
# parent:    FEAT-901
# func_type: button_action
# rationale:
#   - Every Functionality field needs one authored value.
# preconditions:
#   - The full page is open.
# not_in_scope:
#   - Server-side validation.
# notes:
#   - This functionality exists only to fill every contract field.
#
# acceptance_criteria:
#
#   AC:FUNC-901-01 (v1.0.0 - active)
#     - Pressing the button runs the action.
#     - Aspect: keyboard
#     - Rationale: The action needs one criterion.
#     - Button label: Save, Submit
#     preconditions:
#       - The button is enabled.
#     not_in_scope:
#       - Double-click handling.
#
#   AC:FUNC-901-02 (planned)
#     - A planned backlog criterion with no version.
# =============================================================================

@FUNC_ID:FUNC-901
Feature: Full Page - Fully Authored Functionality
  Pressing the button runs the action.
