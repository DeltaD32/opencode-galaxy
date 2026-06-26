# Template Layouts Reference

Slide size: 33.87 x 19.05 cm (12192000 x 6858000 EMU)

## Layout 0: Title | Full Area

Title slide with full-bleed background image.

| idx | Name                   | Type             | Position (cm) | Size (cm)     |
| --- | ---------------------- | ---------------- | ------------- | ------------- |
| 21  | Bildplatzhalter 8      | PICTURE          | 0, 0          | 33.87 x 18.26 |
| 0   | Titel 1                | CENTER_TITLE     | 0, 10.5       | 33.87 x 3.82  |
| 1   | Untertitel 2           | SUBTITLE         | 0, 14.6       | 33.87 x 1.26  |
| 22  | Textplatzhalter 14     | BODY (trapezoid) | 26.49, 16.35  | 7.37 x 1.16   |
| 24  | SmartArt-Platzhalter 6 | ORG_CHART        | 1.59, 1.59    | 3.06 x 1.59   |
| 23  | SmartArt-Platzhalter 4 | ORG_CHART        | 27.63, 1.59   | 4.65 x 1.59   |

**Placeholder 22 (Dept.)** has a custom trapezoid geometry (angled left edge). Call `fix_dept_placeholder(slide)` after setting its text to preserve this shape.

## Layout 1: Divider | Half Area Right

Section divider. Text left, image right.

| idx | Name              | Type         | Position (cm) | Size (cm)     |
| --- | ----------------- | ------------ | ------------- | ------------- |
| 11  | Textplatzhalter 6 | BODY         | 1.33, 3.95    | 17.69 x 3.18  |
| 12  | Bildplatzhalter 6 | PICTURE      | 20.4, 0       | 13.47 x 18.25 |
| 0   | Titel 1           | CENTER_TITLE | 1.33, 7.13    | 17.71 x 5.13  |

## Layout 2: Grid | 1 (also 3, 4, 5, 6)

Title only. Full area below is free for custom shapes.

| idx | Name    | Type  | Position (cm) | Size (cm)    |
| --- | ------- | ----- | ------------- | ------------ |
| 0   | Titel 1 | TITLE | 1.36, 0.96    | 31.18 x 1.11 |

**Free area:** left 1.36 cm (488947 EMU), top 2.07 cm (747294 EMU), width 31.18 cm (11224684 EMU), height ~15.4 cm (~5544000 EMU)

## Layout 7: Content | 1

Title + one full-width content area.

| idx | Name                 | Type   | Position (cm) | Size (cm)    |
| --- | -------------------- | ------ | ------------- | ------------ |
| 0   | Titel 1              | TITLE  | 1.36, 0.96    | 31.18 x 1.11 |
| 17  | Inhaltsplatzhalter 1 | OBJECT | 1.36, 3.93    | 31.18 x 13.6 |

## Layout 8: Content | 2

Title + two content columns.

| idx | Name                 | Type   | Position (cm) | Size (cm)    |
| --- | -------------------- | ------ | ------------- | ------------ |
| 0   | Titel 1              | TITLE  | 1.36, 0.96    | 31.18 x 1.11 |
| 17  | Inhaltsplatzhalter 1 | OBJECT | 1.36, 3.93    | 14.99 x 13.6 |
| 19  | Inhaltsplatzhalter 2 | OBJECT | 17.55, 3.93   | 14.99 x 13.6 |

## Layout 9: Content | 3

Title + three content columns.

| idx | Name                 | Type   | Position (cm) | Size (cm)    |
| --- | -------------------- | ------ | ------------- | ------------ |
| 0   | Titel 1              | TITLE  | 1.36, 0.96    | 31.18 x 1.11 |
| 17  | Inhaltsplatzhalter 1 | OBJECT | 1.36, 3.93    | 9.99 x 13.6  |
| 19  | Inhaltsplatzhalter 2 | OBJECT | 11.95, 3.93   | 9.99 x 13.6  |
| 21  | Inhaltsplatzhalter 3 | OBJECT | 22.54, 3.93   | 9.99 x 13.6  |

## Layout 10: Content | 4

Title + four content columns.

| idx | Name                 | Type   | Position (cm) | Size (cm)    |
| --- | -------------------- | ------ | ------------- | ------------ |
| 0   | Titel 1              | TITLE  | 1.36, 0.96    | 31.18 x 1.11 |
| 17  | Inhaltsplatzhalter 1 | OBJECT | 1.36, 3.93    | 7.34 x 13.6  |
| 19  | Inhaltsplatzhalter 2 | OBJECT | 9.3, 3.93     | 7.34 x 13.6  |
| 21  | Inhaltsplatzhalter 3 | OBJECT | 17.25, 3.93   | 7.34 x 13.6  |
| 23  | Inhaltsplatzhalter 4 | OBJECT | 25.19, 3.93   | 7.34 x 13.6  |

## Layout 11: Content | 2x2

Title + four quadrants.

| idx | Name                 | Type   | Position (cm) | Size (cm)    |
| --- | -------------------- | ------ | ------------- | ------------ |
| 0   | Titel 1              | TITLE  | 1.36, 0.96    | 31.18 x 1.11 |
| 10  | Inhaltsplatzhalter 1 | OBJECT | 1.36, 3.93    | 14.99 x 6.5  |
| 11  | Inhaltsplatzhalter 2 | OBJECT | 17.55, 3.93   | 14.99 x 6.5  |
| 12  | Inhaltsplatzhalter 3 | OBJECT | 1.36, 11.02   | 14.99 x 6.5  |
| 13  | Inhaltsplatzhalter 4 | OBJECT | 17.55, 11.02  | 14.99 x 6.5  |

## Layout 12: Content | Area

Title only. Full content area free for custom placement.

| idx | Name    | Type  | Position (cm) | Size (cm)    |
| --- | ------- | ----- | ------------- | ------------ |
| 0   | Titel 1 | TITLE | 1.36, 0.96    | 31.18 x 1.11 |

**Free area:** left 1.36 cm (488947 EMU), top 3.93 cm (1413933 EMU), width 31.18 cm (11224684 EMU), height 13.6 cm (4894792 EMU)

## Layout 13: Content | Picture Left

Title + image left, content right.

| idx | Name                 | Type    | Position (cm) | Size (cm)    |
| --- | -------------------- | ------- | ------------- | ------------ |
| 0   | Titel 1              | TITLE   | 1.36, 0.96    | 31.18 x 1.11 |
| 12  | Bildplatzhalter 1    | PICTURE | 0, 3.93       | 16.35 x 13.6 |
| 10  | Inhaltsplatzhalter 1 | OBJECT  | 17.54, 3.93   | 14.99 x 13.6 |

## Layout 14: Content | Picture Right

Title + content left, image right.

| idx | Name                 | Type    | Position (cm) | Size (cm)    |
| --- | -------------------- | ------- | ------------- | ------------ |
| 0   | Titel 1              | TITLE   | 1.36, 0.96    | 31.18 x 1.11 |
| 10  | Inhaltsplatzhalter 1 | OBJECT  | 1.36, 3.93    | 14.99 x 13.6 |
| 12  | Bildplatzhalter 3    | PICTURE | 17.52, 3.93   | 16.35 x 13.6 |

## Layout 18: Key Note

Full background image + large centered title.

| idx | Name              | Type    | Position (cm) | Size (cm)     |
| --- | ----------------- | ------- | ------------- | ------------- |
| 10  | Bildplatzhalter 1 | PICTURE | 0, 0          | 33.87 x 18.25 |
| 0   | Titel 1           | TITLE   | 0, 3.92       | 33.9 x 4.03   |

## Layout 19: Title | Full Picture

Alternative title slide with full background.

| idx | Name               | Type             | Position (cm) | Size (cm)     |
| --- | ------------------ | ---------------- | ------------- | ------------- |
| 21  | Bildplatzhalter 8  | PICTURE          | 0, 0          | 33.87 x 18.26 |
| 0   | Titel 1            | CENTER_TITLE     | 0, 10.56      | 33.87 x 3.92  |
| 1   | Untertitel 2       | SUBTITLE         | 0, 14.75      | 33.87 x 1.26  |
| 22  | Textplatzhalter 14 | BODY (trapezoid) | 26.49, 16.35  | 7.37 x 1.16   |

**Placeholder 22 (Dept.)** has a custom trapezoid geometry (angled left edge). Call `fix_dept_placeholder(slide)` after setting its text to preserve this shape.
