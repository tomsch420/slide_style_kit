located_on(cup_3, table).
located_on(plate_1, table).
category(cup_3, cup).
category(plate_1, plate).
belongs_in(cup, dishwasher).
belongs_in(plate, cupboard).

to_put_away(Object, Place) :-
    located_on(Object, table),
    category(Object, Kind),
    belongs_in(Kind, Place).
