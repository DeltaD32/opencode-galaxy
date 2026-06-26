# Numerics

> **Source**: BMW Group Density Design System
> For the most up-to-date guidelines, visit:
> https://density.bmwgroup.net/v11/content/voice-and-tone

---

Compliance with certain rules of formatting numbers keeps the interface clear and increases readability. Depending on the language settings, number formats are displayed differently. For all non-German applications use the British English format.

## Date and Time

### Date

Different usecases in your UI might require different representation of dates. In the following examples **Medium** can be taken as default.

**1. Full Date**

| Format      | English               | German                |
| ----------- | --------------------- | --------------------- |
| Short       | 4/7/17                | 4.7.17                |
| Medium      | 4/7/2017              | 4.7.2017              |
| Long        | 04/07/2017            | 04.07.2017            |
| Short-text  | 4 Jul 2017            | 4. Jul 2017           |
| Medium-text | Sat, 4 Jul 2017       | Sa, 4. Jul 2017       |
| Long-text   | Saturday, 4 July 2017 | Samstag, 4. Juli 2017 |

**2. Days of the Week and Months**

Abbreviated without a dot.

| Type            | English                                         | German                                          |
| --------------- | ----------------------------------------------- | ----------------------------------------------- |
| Day of the week | Mon Tue Wed Thu Fri Sat Sun                     | Mo Di Mi Do Fr Sa So                            |
| Month           | Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec | Jan Feb Mrz Apr Mai Jun Jul Aug Sep Okt Nov Dez |

**3. Month and Year**

| Format      | English   | German    |
| ----------- | --------- | --------- |
| Short       | 4/17      | 4.17      |
| Medium      | 4/2017    | 4.2017    |
| Long        | 04/2017   | 04.2017   |
| Short-text  | Jul 2017  | Jul 2017  |
| Medium-text | Jul 2017  | Jul 2017  |
| Long-text   | July 2017 | Juli 2017 |

**4. Year**

| Format                                           | English / German |
| ------------------------------------------------ | ---------------- |
| Short                                            | 17               |
| Medium, Long, Short-text, Medium-text, Long-text | 2017             |

### Time

Show time durations depending on the provided data base. If seconds are crucial: go with the longer version `hh:mm:ss`. Otherwise stay with `hh:mm`. When focusing on the comparability of several times, leading zeros can be displayed for better readability.

Use numerals and "Uhr" for German, with a space in between. Only add minutes for not on-the-hour time, like 19:30. Display the time without am/pm when using 24-hour clock.

| Format                  | English     | German         |
| ----------------------- | ----------- | -------------- |
| Default                 | 07:00       | 7 Uhr          |
| Time with minutes       | 19:30       | 19:30 Uhr      |
| Time period             | 07:00-19:30 | 7:00-19:30 Uhr |
| Focus on comparing time | 07:12:34    | 07:12:34       |

**Hint:** If a time period is to be displayed, connect the time to a hyphen without spaces (e.g. `07:00-19:30`).

**1. Time Stamp**

Using absolute or relative timestamps will depend on the context. If the user is primarily interested in understanding the exact date and time that an event occurred, use an absolute timestamp. If users are interested in how long ago an event occurred, use a relative timestamp.

**2. Time Frame - Relative Time**

| Time Frame     | English        | German         |
| -------------- | -------------- | -------------- |
| 0-60 seconds   | just now       | gerade         |
| 1-60 minutes   | 10 minutes ago | vor 10 Minuten |
| 1-24 hours     | 7 hours ago    | vor 7 Stunden  |
| Yesterday      | yesterday      | gestern        |
| + 1 day        | tomorrow       | morgen         |
| 1-30 days      | 12 days ago    | vor 12 Tagen   |
| 1 month-1 year | 10 month ago   | vor 10 Monaten |
| >1 year        | 24 Dec 2010    | 24 Dez 2010    |

**3. Date and Time Together**

When representing date and time, include the timestamp after the date and separate with a comma.

**4. Time Zone**

Display the time in the logged-in user's time zone when it is useful. Only add the time zone when it is inherent to the user's time zone:

- "Maintenance begins today at 08:00 UTC."
- Or even better: "Maintenance begins today at 08:00 UTC (04:00 EST)."

## Decimal Places and Huge Numbers

Display numbers based on the language settings. In an English interface, the decimal place is specified with a period, in a German with a comma. Thousands of delimiters are displayed with a comma in English and a period in German.

| Type           | English       | German        |
| -------------- | ------------- | ------------- |
| Round amount   | 1,123         | 1.123         |
| Decimal places | 1,001.99      | 1.001,99      |
| Huge numbers   | 1,123,456,789 | 1.123.456.789 |

## Phone Numbers

Use hyphen without spaces for phone numbers in English. In German the area code is enclosed in parentheses and for better readability, numbers can be separated with a space. The international area code always starts with a `+`.

| Type          | English         | German           |
| ------------- | --------------- | ---------------- |
| National      | 89-123-4567     | (089) 123 45678  |
| International | +1-89-123-45678 | +49 89 123 45678 |

## Currency

Depending on the currency use the currency sign before the amount ($10) without a space or after (10 €) with a space. Separators of thousands are optional, but for large quantities separators increase readability.

| Type           | English        | German         |
| -------------- | -------------- | -------------- |
| Round amount   | €1,000         | €1.000         |
| Decimal places | $1,000.99      | $1.000,99      |
| Huge amounts   | 1,123,456.78 € | 1.123.456,78 € |

**Hint:** BMW standard currency is Euro.

## Units

There is always a space between number and unit. The only exceptions to this rule are for degree, minute and second for the plane angle, such as `30° 22′ 8″`. There is no difference between German and English.

**Do:**

- 23 kg
- 89 km/h

**Don't:**

- 23kg
- 89km/h

---

**Last Updated**: April 2026
**Source**: BMW Group Density Design System
