- our tool is good. but now I want it become multiple feature card creation support instead of only translate


# card (question) type
- normal (like current card we have implemented)
- phrasel verb
- word form
- word parttern

# general
- when open the card creator in deck, it will show radio buttons to choose type, each type auto display rational input field 

# feature for each type
## normal
- we have already implement translate, this normal is just like that

## phrasel verb
- this is quite similar to normal, but use LLM to has more correct meaning
- We will call api to LLM, force LLM to response with a struct suitable for our card
- this support select definition options too

## word form
- this type of question use to learn familyword (like able -> ability, disabled, unable)
- the data will be:
```json
    {
        "rootWord" : {
            "word":"abc",
            "type": "verb",
            "definition": 

        },
        "other" : [
            {
                "word":"abc",
                "type": "verb",
                "special_definition":null
            },
            {
                "word":"abc",
                "type": "verb",
                "special_definition":"completely different from root"
            }
        ]
    }
```
- when learn, it will show the root word, the number of other type if existed: example
-   able (adj), 1N, 2adj
-   show: show all info with good format
- *the special_definition only need if the meaning is completely different from the root meaning
## word parttern
- this type is learn some specific way to use a word (like: help + sb + with, ...)
- the input will be like : make a decision
- LLM should make a gap question like:
A ___ a decision ...