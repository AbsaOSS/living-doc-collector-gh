# Fully authored fixture (R12 check 3): every scenario field of the ui-tests contract.
@US_ID:US-901
Feature: Fully Authored Scenarios

  @AC:US-901-01/aspect:desktop
  @AC:US-901-02
  @Regression
  Scenario: Every extension is read on desktop
    Given the fully authored story
    Then every field is filled

  @AC:US-901-01/aspect:mobile
  Scenario Outline: Every extension is read on <device>
    Given the fully authored story on <device>
    Then every field is filled

    Examples:
      | device |
      | phone  |

  @tutorial
  Scenario: A tutorial walkthrough is not mined
    Given a tutorial
