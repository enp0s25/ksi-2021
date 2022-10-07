# Contact organizer

## How to use it
- run `main.py`
- program automatically tries to load `contacts.json` (I am including one with example entries)
- if `contacts.json` is not found in current directory it will start to create new contact DB from scratch
- saving is done with `Ctrl-S`, will overwrite current open JSON (or create new one if there is not one open)
- when loading contacts from JSON, it will create new window with list of contacts that have birthday today (if any), also showing how old they are if year of birth is specified
- valid birthday formats are `YYYY-MM-DD` or `MM-DD`
- program allows actions `Edit`, `Delete` and `Export vCard` based on number of currently selected contacts
