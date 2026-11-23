SELECT located_on.object, belongs_in.place
FROM located_on
JOIN category
  ON category.object = located_on.object
JOIN belongs_in
  ON belongs_in.kind = category.kind
WHERE located_on.support = 'table';
