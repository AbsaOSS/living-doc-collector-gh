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

  # AC:US-901-06 declares its variants with the keyword `user role:`, so its tag names that keyword
  # instead of `aspect` - the same link, the other spelling (`DEC-76`).
  @AC:US-901-06/user-role:admin
  Scenario: The story is readable for an admin
    Given the fully authored story
    Then an admin can read it

  # A bare tag on an AC that declares variants links the whole criterion, every declared value (`DEC-76`).
  @AC:US-901-06
  Scenario: The story is readable for every role
    Given the fully authored story
    Then every role can read it

  @tutorial
  Scenario: A tutorial walkthrough is not mined
    Given a tutorial
