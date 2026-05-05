---
size: medium
---
# Add Pydantic classes for every part of the yaml data we are reading

Create pydantic data classes that will be used to instantiate and thus validate a single object corresponding to a full cv (and/or cover letter)

## Concerns
- How do we translate the existing i18n mechanism to a class that represents any possible value string?
    - str -> not translatable
    - dictionary -> translatable
        - "def" field used for every language that doesn't have an explicit translation
        - ISO-639-1 language code to define a language specific translation
        - If no "def" field and no language field -> invalid
- How can we bring our existing (implicit) schema closer to [JSON Resume](https://jsonresume.org) without losing any part of our expressivity
    - We must investigate multiple scenarios
    - We must convert existing data to the new version of the format

# Non-functional constraints
- Good semantic documentation of every field (given that value validity is taken care of by pydantic)
    - LLMs need to be able to understand what each value corresponds to


## Goal:
- Integration with LLMs
- Automatic data validation
- Automatic JSON Schema creation


