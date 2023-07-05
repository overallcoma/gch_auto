# gch_auto
## Gencon Hotel Portal Room Auto-Booking Solution

## Setup

- Modify gch2.cfg - specifically you'll want the "entry-token"
--To get this value you must have a Gencon Account with no room already booked
--Open the Gencon profile and go to "Housing"
--Click "Go To Housing Portal" and "Yes" when prompted
--The value required is in your address bar
- Install requirements
```sh
pip install -r -requirements.txt
```

## Other config values
| Value | Description |
| ------ | ------ |
| event-id | From the Address bar when searching - same for everyone on the same year |
| owner-id | From the Address bar when searching - same for everyone on the same year |
| entry-token | See above |
| check-frequency | Seconds of delay between searches |

## Search Filters
Dates are formatted carefully - please note whitepace or zero filling was done carefully.
search-*somedistance* - Bools for turning search off or on
hotel name filter - Filters on the name of the hotel
hotel room filter - Filters based on description of the bedroom - usually you'll want "King" or "Queen" or "Double" or "Suite"

## Autobook
Use at your own risk. I last tested this in 2020.

### THINGS TO NOTE
If the autobook doesn't work, my methodology for correcting the issues was to step through the booking process manually, in Kali, through Burpsuite.
Then take the parameters of the POSTs in Python and adjust accordingly.

A few years ago they implemented "cross-site request forgery" that doesn't actually work, but you need to include it in some places.
Usually just on the initial searches.


### WARNING
- In some testing it appeared that this autobooker also does not terminate the validity of a login string.
-- This means without the kill command in the loop when the autobooker runs, it will keep booking rooms.
- I was able to book as many hotel rooms as I wanted on a single entry token.
- The housing portal doesn't validate credit card, email, or any personal data so long as the format is correct.
- This is a cool site - (https://www.vccgenerator.org/)
-- Or I'm sure one of those types of services has an API - that'd be fun to integrate in


## Background
You've have 4 years to fix this.(https://stevenloftus.com/projects/hotel-hacking-cvent-passkey/)

## License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License

(This means if it cannot be used in any commercial capacity. Looking at you, CVent.)
